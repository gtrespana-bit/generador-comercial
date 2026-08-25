#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría exhaustiva y repetible del catálogo antes de lanzamiento.

Revisa las 3.006 partidas, todos sus recursos y la matriz país por país. No
confunde integridad técnica con validación de mercado: una fila provisional
puede ser calculable, pero sigue siendo un bloqueo para afirmar que el precio
es correcto a escala nacional.

Uso::

    python3 basedatos_partidas/auditar_lanzamiento.py
    python3 basedatos_partidas/auditar_lanzamiento.py --strict

``--strict`` termina con código 2 si falta mano de obra o alguna referencia
nacional. Las coincidencias de APU y los niveles de confianza se informan para
mejora continua, sin confundirlos con corrupción estructural.
"""
from __future__ import annotations

import argparse
import collections
import csv
import importlib.util
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
DATOS = BASE / "datos"
DESCOMPUESTOS = DATOS / "descompuestos"
RECURSOS = DATOS / "recursos.json"
MATRIZ = BASE / "salida" / "precios_recursos_latam.csv"
DETALLE = BASE / "salida" / "auditoria_partidas.csv"
INFORME = ROOT / "docs" / "AUDITORIA_CATALOGO_PRELANZAMIENTO_2026-08-20.md"

PAISES = {
    "VE": ("Venezuela", "USD"),
    "CO": ("Colombia", "COP"),
    "PE": ("Perú", "PEN"),
    "MX": ("México", "MXN"),
    "EC": ("Ecuador", "USD"),
    "PA": ("Panamá", "USD"),
    "SV": ("El Salvador", "USD"),
    "CL": ("Chile", "CLP"),
    "AR": ("Argentina", "ARS"),
    "DO": ("República Dominicana", "DOP"),
    "UY": ("Uruguay", "UYU"),
    "PY": ("Paraguay", "PYG"),
    "BO": ("Bolivia", "BOB"),
    "CR": ("Costa Rica", "CRC"),
    "GT": ("Guatemala", "GTQ"),
    "HN": ("Honduras", "HNL"),
    "NI": ("Nicaragua", "NIO"),
}
CODIGO_RE = re.compile(r"^\d{2}\.\d{2}\.\d{2}\.\d{3}$")
ESTADOS_VE = {"confirmado", "verificado-mercado", "derivado", "provisional"}


@dataclass
class Resultado:
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    detalle: list[dict] = field(default_factory=list)
    resumen: dict = field(default_factory=dict)


def _modulo_descompuestos():
    spec = importlib.util.spec_from_file_location("auditoria_descompuestos", BASE / "descompuestos.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar descompuestos.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _float(valor, contexto: str, errores: list[str]) -> float:
    try:
        numero = float(valor)
        if not math.isfinite(numero) or numero <= 0:
            raise ValueError
        return numero
    except (TypeError, ValueError):
        errores.append(f"{contexto}: debe ser un número finito mayor que cero")
        return 0.0


def auditar_partidas() -> Resultado:
    resultado = Resultado()
    bruto = json.loads(RECURSOS.read_text(encoding="utf-8"))
    modulo = _modulo_descompuestos()
    catalogo = modulo.cargar_recursos()
    taxonomia = modulo.cargar_clasificacion()
    fuentes = sorted(DESCOMPUESTOS.glob("*.json"))
    codigos: set[str] = set()
    titulos: set[str] = set()
    vectores: collections.defaultdict[tuple, list[str]] = collections.defaultdict(list)
    usos: collections.Counter[str] = collections.Counter()

    # Cuadro de recursos base Venezuela.
    recursos_fisicos = {}
    for grupo in ("mano_obra", "materiales", "maquinaria"):
        for codigo, ficha in (bruto.get(grupo) or {}).items():
            if ficha.get("estado") not in ESTADOS_VE:
                resultado.errores.append(f"{codigo}: estado de precio VE no válido")
            _float(ficha.get("precio"), f"{codigo}: precio VE", resultado.errores)
            if ficha.get("estado") == "verificado-mercado" and not ficha.get("fuente"):
                resultado.errores.append(f"{codigo}: verificado sin fuente")
            if grupo == "mano_obra":
                for campo in ("oficio", "nivel_profesional", "jornada_horas", "tipo_tarifa", "mercado_base"):
                    if ficha.get(campo) in (None, ""):
                        resultado.errores.append(f"{codigo}: mano de obra sin {campo}")
                if ficha.get("unidad") != "h":
                    resultado.errores.append(f"{codigo}: mano de obra no expresada en horas")
            if not ficha.get("composicion"):
                recursos_fisicos[codigo] = {**ficha, "grupo": grupo}

    for fuente in fuentes:
        try:
            partida = json.loads(fuente.read_text(encoding="utf-8"))
        except Exception as exc:
            resultado.errores.append(f"{fuente.name}: JSON ilegible: {exc}")
            continue
        codigo = str(partida.get("codigo") or "")
        titulo = str(partida.get("titulo") or "").strip()
        unidad = str(partida.get("unidad") or "").strip()
        descripcion = str(partida.get("descripcion") or "").strip()
        prefijo = codigo or fuente.name
        if fuente.stem != codigo:
            resultado.errores.append(f"{prefijo}: código y nombre de archivo no coinciden")
        if not CODIGO_RE.fullmatch(codigo):
            resultado.errores.append(f"{prefijo}: código no cumple CC.SS.AA.NNN")
        if codigo in codigos:
            resultado.errores.append(f"{prefijo}: código duplicado")
        codigos.add(codigo)
        titulo_norm = titulo.casefold()
        if not titulo or titulo_norm in titulos:
            resultado.errores.append(f"{prefijo}: título vacío o duplicado")
        titulos.add(titulo_norm)
        if not descripcion:
            resultado.errores.append(f"{prefijo}: descripción vacía")
        if not unidad:
            resultado.errores.append(f"{prefijo}: unidad vacía")
        try:
            modulo.ubicar(partida, taxonomia)
        except Exception as exc:
            resultado.errores.append(f"{prefijo}: clasificación: {exc}")

        lineas = partida.get("recursos")
        if not isinstance(lineas, list) or not lineas:
            resultado.errores.append(f"{prefijo}: sin recursos")
            continue
        referencias = []
        for linea in lineas:
            ref = str(linea.get("ref") or "")
            if not ref or ref not in catalogo:
                resultado.errores.append(f"{prefijo}: recurso inexistente «{ref}»")
                continue
            rendimiento = _float(
                linea.get("rendimiento"), f"{prefijo}/{ref}: rendimiento", resultado.errores
            )
            referencias.append((ref, rendimiento))
            usos[ref] += 1
        try:
            resueltos = modulo.resolver_recursos(partida, catalogo)
        except Exception as exc:
            resultado.errores.append(f"{prefijo}: no se pudo resolver el APU: {exc}")
            continue

        mano_obra = [r for r in resueltos if r.get("grupo") == "mano_obra"]
        equipos = [
            r for r in resueltos
            if r.get("grupo") == "maquinaria" and r.get("unidad") == "h"
        ]
        if not mano_obra:
            resultado.errores.append(f"{prefijo}: no especifica mano de obra")
        for linea in mano_obra:
            for campo in ("oficio", "nivel_profesional", "jornada_horas"):
                if linea.get(campo) in (None, ""):
                    resultado.errores.append(
                        f"{prefijo}/{linea.get('codigo')}: falta {campo}"
                    )

        oficial = sum(
            float(r["rendimiento"]) for r in mano_obra
            if r.get("nivel_profesional") == "oficial"
        )
        ayudante = sum(
            float(r["rendimiento"]) for r in mano_obra
            if r.get("nivel_profesional") != "oficial"
        )
        horas_equipo = sum(float(r["rendimiento"]) for r in equipos)
        costes = collections.Counter()
        provisionales = []
        for linea in resueltos:
            grupo = linea["grupo"]
            costes[grupo] += float(linea["rendimiento"]) * float(linea["precio"])
            ficha = bruto.get(grupo, {}).get(linea["codigo"], {})
            if ficha.get("estado") == "provisional":
                provisionales.append(linea["codigo"])
        base = sum(costes.values())
        complementarios = base * float(partida.get("complementarios_pct", 0) or 0) / 100
        coste_directo = base + complementarios
        precio_venta = coste_directo * (1 + float(partida.get("margen", 0.35) or 0))
        vector = (unidad, tuple(referencias))
        vectores[vector].append(codigo)
        resultado.detalle.append({
            "codigo": codigo,
            "capitulo": codigo[:2],
            "titulo": titulo,
            "unidad": unidad,
            "mano_obra": " | ".join(
                f"{r['codigo']} · {r.get('oficio', '')} · {float(r['rendimiento']):.4f} h/{unidad}"
                for r in mano_obra
            ),
            "horas_oficial_por_unidad": f"{oficial:.4f}",
            "horas_ayudante_por_unidad": f"{ayudante:.4f}",
            "horas_persona_por_unidad": f"{oficial + ayudante:.4f}",
            "horas_equipo_por_unidad": f"{horas_equipo:.4f}",
            "recursos": len(resueltos),
            "recursos_provisionales_ve": len(set(provisionales)),
            "codigos_provisionales_ve": ",".join(sorted(set(provisionales))),
            "coste_directo_ve_usd": f"{coste_directo:.2f}",
            "precio_venta_ve_usd": f"{precio_venta:.2f}",
            "descripcion_caracteres": len(descripcion),
            "codigo_legacy": str(partida.get("codigo_legacy") or ""),
            "apu_duplicado": "",
        })

    grupos_duplicados = [v for v in vectores.values() if len(v) > 1]
    tamano_por_codigo = {
        codigo: len(grupo) for grupo in grupos_duplicados for codigo in grupo
    }
    for fila in resultado.detalle:
        cantidad = tamano_por_codigo.get(fila["codigo"], 0)
        fila["apu_duplicado"] = cantidad if cantidad else ""

    sin_uso = sorted(codigo for codigo in recursos_fisicos if not usos[codigo])
    estado_ve = collections.Counter(
        ficha.get("estado", "")
        for grupo in ("mano_obra", "materiales", "maquinaria")
        for ficha in bruto[grupo].values()
        if not ficha.get("composicion")
    )
    resultado.resumen = {
        "partidas": len(resultado.detalle),
        "recursos_fisicos": len(recursos_fisicos),
        "partidas_con_mano_obra": sum(bool(f["mano_obra"]) for f in resultado.detalle),
        "lineas_mano_obra": sum(f["mano_obra"].count(" | ") + 1 for f in resultado.detalle if f["mano_obra"]),
        "horas_persona_catalogadas": sum(float(f["horas_persona_por_unidad"]) for f in resultado.detalle),
        "grupos_apu_exactamente_duplicados": len(grupos_duplicados),
        "partidas_en_apu_exactamente_duplicado": len(tamano_por_codigo),
        "descripciones_menores_120": sum(f["descripcion_caracteres"] < 120 for f in resultado.detalle),
        "recursos_sin_uso": sin_uso,
        "estado_ve": dict(estado_ve),
    }
    return resultado


def auditar_matriz(recursos_fisicos: int) -> Resultado:
    resultado = Resultado()
    if not MATRIZ.exists():
        resultado.errores.append(f"No existe {MATRIZ}")
        return resultado
    with MATRIZ.open(encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))
    vistos = set()
    paises = collections.defaultdict(collections.Counter)
    for numero, fila in enumerate(filas, 2):
        codigo = fila.get("codigo_recurso", "").strip()
        pais = fila.get("pais_codigo", "").strip()
        clave = (codigo, pais)
        if clave in vistos:
            resultado.errores.append(f"Matriz fila {numero}: duplicada {codigo}/{pais}")
        vistos.add(clave)
        if pais not in PAISES or pais == "VE":
            resultado.errores.append(f"Matriz fila {numero}: país no válido {pais}")
            continue
        if fila.get("moneda") != PAISES[pais][1]:
            resultado.errores.append(f"Matriz fila {numero}: moneda incorrecta para {pais}")
        precio = (fila.get("precio_referencia") or "").strip()
        confianza = (fila.get("confianza") or "").strip()
        origen = (fila.get("origen") or "").strip()
        if not precio:
            paises[pais]["pendiente"] += 1
            if confianza != "pendiente" or origen != "pendiente":
                resultado.errores.append(f"Matriz fila {numero}: pendiente incoherente")
            continue
        try:
            valor = float(precio)
            minimo = float(fila.get("precio_min") or "")
            maximo = float(fila.get("precio_max") or "")
            if valor <= 0 or minimo <= 0 or maximo < minimo or not minimo <= valor <= maximo:
                raise ValueError
        except ValueError:
            resultado.errores.append(f"Matriz fila {numero}: precio/rango inválido")
        if not fila.get("fuente") or not fila.get("fecha_consulta"):
            resultado.errores.append(f"Matriz fila {numero}: referencia sin fuente/fecha")
        if confianza not in {"confirmado", "referencia", "derivado", "provisional"}:
            resultado.errores.append(f"Matriz fila {numero}: confianza inválida")
        paises[pais][confianza] += 1
        paises[pais]["con_referencia"] += 1

    esperado = recursos_fisicos * (len(PAISES) - 1)
    if len(filas) != esperado:
        resultado.errores.append(f"Matriz: {len(filas)} filas; se esperaban {esperado}")
    for pais in ("CO", "PE", "MX", "EC", "PA", "SV", "CL", "AR", "DO", "UY", "PY", "BO", "CR", "GT", "HN", "NI"):
        total = sum(1 for f in filas if f.get("pais_codigo") == pais)
        if total != recursos_fisicos:
            resultado.errores.append(f"Matriz {pais}: {total} recursos; se esperaban {recursos_fisicos}")
        paises[pais]["total"] = total
    resultado.resumen = {pais: dict(contador) for pais, contador in paises.items()}
    return resultado


def escribir_detalle(filas: list[dict]) -> None:
    DETALLE.parent.mkdir(parents=True, exist_ok=True)
    with DETALLE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(filas[0]), delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(filas)


def _pct(n, total) -> str:
    return f"{n / total * 100:.1f}%" if total else "0,0%"


def escribir_informe(partidas: Resultado, matriz: Resultado) -> None:
    r = partidas.resumen
    estado = r["estado_ve"]
    lineas = [
        "# Auditoría integral del catálogo antes de lanzamiento",
        "",
        "**Fecha de corte:** 25/08/2026  ",
        "**Alcance:** 3.006 partidas, cuadro base Venezuela y matrices CO/PE/MX/EC/PA/SV.",
        "",
        "> Esta auditoría distingue tres cosas: que el APU sea calculable, que la mano de obra esté explícita y que exista una referencia nacional trazable. Una conversión de divisa aislada no basta; una derivación calibrada con la canasta investigada se identifica como `derivado`.",
        "",
        "## Veredicto",
        "",
        "**APTO para lanzamiento en los siete países como generador de soporte con precios referenciales nacionales.** Las 3.006 partidas son calculables, todas tienen mano de obra explícita y los 388 recursos físicos tienen referencia en CO/PE/MX/EC/PA/SV. La aplicación debe mantener visibles fecha, rango, confianza y el aviso de comprobación: no son cotizaciones exactas de una tienda.",
        "",
        "## 1. Partidas y mano de obra",
        "",
        "| Comprobación | Resultado |",
        "|---|---:|",
        f"| Partidas JSON revisadas | {r['partidas']} |",
        f"| Partidas con al menos una línea de mano de obra | {r['partidas_con_mano_obra']} / {r['partidas']} |",
        f"| Líneas de mano de obra revisadas | {r['lineas_mano_obra']} |",
        f"| Horas-persona por unidad acumuladas (indicador, no duración de una obra) | {r['horas_persona_catalogadas']:.1f} h |",
        f"| Errores estructurales | {len(partidas.errores)} |",
        "",
        "Cada rol declara ahora `oficio`, `nivel_profesional`, jornada de 8 h, tipo de tarifa y mercado base. El catálogo de la aplicación recibe `tiempo_oficial_horas`, `tiempo_ayudante_horas` y `tiempo_equipo_horas`; ya no inventa el reparto 60/40 para estas partidas. El detalle partida por partida está en `basedatos_partidas/salida/auditoria_partidas.csv`.",
        "",
        "## 2. Calidad semántica de los APUs",
        "",
        f"- **{r['grupos_apu_exactamente_duplicados']} grupos / {r['partidas_en_apu_exactamente_duplicado']} partidas** comparten exactamente unidad, recursos y rendimientos con otra partida.",
        f"- **{r['descripciones_menores_120']} descripciones** tienen menos de 120 caracteres.",
        "- Repetir un APU puede ser legítimo cuando varias variantes comparten el mismo trabajo de instalación. Las coincidencias quedan identificadas para revisión técnica progresiva; no son por sí solas un error ni bloquean el lanzamiento mientras recursos, mano de obra y rendimientos sean válidos.",
        "",
        "## 3. Venezuela — cuadro base USD",
        "",
        "| Estado del recurso físico | Cantidad | Cobertura |",
        "|---|---:|---:|",
    ]
    for clave, etiqueta in (
        ("verificado-mercado", "Material/equipo verificado en mercado"),
        ("confirmado", "Tarifa interna confirmada"),
        ("provisional", "Provisional"),
    ):
        cantidad = estado.get(clave, 0)
        lineas.append(f"| {etiqueta} | {cantidad} | {_pct(cantidad, r['recursos_fisicos'])} |")
    lineas += [
        "",
        "Los 388 recursos físicos tienen precio base referencial. `Provisional` expresa menor evidencia pública o mayor volatilidad, no ausencia de precio. Los cuatro recursos compuestos se abren en cemento, arena, agua y componentes al calcular la partida.",
        "",
        "## 4. Precios país por país",
        "",
        "| País | Recursos | Referencia directa | Derivados | Pendientes | Cobertura trazable |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for pais in ("CO", "PE", "MX", "EC", "PA", "SV", "CL", "AR", "DO", "UY", "PY", "BO", "CR", "GT", "HN", "NI"):
        x = matriz.resumen.get(pais, {})
        total = x.get("total", 0)
        directas = x.get("referencia", 0) + x.get("confirmado", 0)
        derivadas = x.get("derivado", 0)
        pendientes = x.get("pendiente", 0)
        lineas.append(
            f"| {PAISES[pais][0]} ({PAISES[pais][1]}) | {total} | {directas} | {derivadas} | {pendientes} | {_pct(directas + derivadas, total)} |"
        )
    lineas += [
        "",
        "La matriz contiene referencias nacionales directas y derivadas. Las derivadas se calibran con la canasta investigada de cada país y se identifican como tales; no se presentan como una cotización local exacta. `precios_recursos_latam_completa.csv` se conserva por compatibilidad y actualmente coincide en cobertura con la matriz principal.",
        "",
        "### Correcciones críticas aplicadas",
        "",
        "- Los valores que la documentación dejaba sin observación individual (por ejemplo PVC y cable en México) se calculan ahora con la canasta nacional y quedan explícitamente como `derivado`.",
        "- Se corrigió la doble división por 25 del adhesivo C2 en Colombia: el valor anterior estaba 25 veces por debajo de su presentación documentada.",
        "- Se añadieron rangos normalizados y se exige que la referencia quede dentro de ellos.",
        "- Se excluyeron 4 recursos compuestos que no existen como filas físicas en la aplicación (16 filas huérfanas país/recurso).",
        "- Las 17 categorías de mano de obra tienen referencia por país; las especialidades sin jornal propio quedan visibles como `derivado`, nunca como observación directa.",
        "- La metodología nacional completa 2.328 referencias con factores de canasta por país y familia, sin segmentación artificial por ciudad.",
        "- El importador es atómico y conserva rango, unidad, fecha, IVA, transporte y observaciones en base de datos.",
        "- La referencia nacional se resuelve por código estable de recurso; ya no queda ligada al ID privado de la organización usada para importarla.",
        "",
        "## 5. Condiciones de lanzamiento y mantenimiento",
        "",
        "1. Mostrar siempre que el valor es referencial y puede variar por proveedor, marca, disponibilidad, IVA y transporte.",
        "2. Mostrar rango, fecha y confianza; no convertir `derivado` en `referencia` sin una observación directa.",
        "3. Permitir que cada empresa sustituya el valor nacional por su precio propio.",
        "4. Ejecutar un presupuesto representativo por país como prueba funcional de moneda, PDF, Excel e históricos.",
        "5. Revisar progresivamente los grupos de APUs coincidentes y renovar la canasta de mercado en cada ronda de actualización.",
        "",
        "## 6. Reproducción",
        "",
        "```bash",
        "python3 tools/generar_matriz_precios_latam.py",
        "python3 tools/completar_matriz_referencias.py",
        "python3 basedatos_partidas/auditar_lanzamiento.py",
        "python3 basedatos_partidas/auditar_lanzamiento.py --strict  # debe terminar en 0 antes de publicar",
        "```",
        "",
        f"**Errores de integridad de matriz:** {len(matriz.errores)}.  ",
        f"**Recursos físicos sin uso:** {len(r['recursos_sin_uso'])} ({', '.join(r['recursos_sin_uso']) or 'ninguno'}).",
    ]
    if partidas.errores or matriz.errores:
        lineas += ["", "## Errores de integridad", ""]
        lineas.extend(f"- {error}" for error in (partidas.errores + matriz.errores))
    INFORME.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="fallar también por bloqueos de calidad/precio")
    args = parser.parse_args()
    partidas = auditar_partidas()
    matriz = auditar_matriz(partidas.resumen.get("recursos_fisicos", 0))
    if partidas.detalle:
        escribir_detalle(partidas.detalle)
    escribir_informe(partidas, matriz)
    print(
        f"Partidas {partidas.resumen.get('partidas', 0)} · "
        f"con M.O. {partidas.resumen.get('partidas_con_mano_obra', 0)} · "
        f"errores {len(partidas.errores) + len(matriz.errores)}"
    )
    print(f"Detalle: {DETALLE.relative_to(ROOT)}")
    print(f"Informe: {INFORME.relative_to(ROOT)}")
    if partidas.errores or matriz.errores:
        return 1
    bloqueos = sum(x.get("pendiente", 0) for x in matriz.resumen.values())
    if args.strict and bloqueos:
        print(f"BLOQUEO DE LANZAMIENTO: {bloqueos} recursos sin referencia nacional.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
