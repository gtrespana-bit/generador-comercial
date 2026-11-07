#!/usr/bin/env python3
"""Verificación cruzada de los precios de España con evidencia ya reunida.

Un precio solo puede darse por **confirmado** si lo sostiene una observación
**independiente** del documento que lo originó, dentro de una banda del ±15 %.
Este comando construye el grafo de evidencia de los 388 recursos a partir de:

- el registro maestro (estado, precio revisado y documento que lo originó);
- las 20 tablas ``espana_fuentes_*.csv`` de los lotes (observaciones con URL);
- el cribado del banco oficial (``espana_cribado_bcca_*.csv``), aceptando solo
  candidatos con precisión ≥ 0,70 y números de especificación compatibles;
- la matriz local (precio vigente).

Salida: `espana_verificacion_2026-11-07.csv`, con una fila por recurso y un
veredicto explícito. Con ``--aplicar`` escribe además la tabla de
confirmaciones que consume ``tools/confirmar_precios_espana.py``.

Reglas (publicadas para que el resultado sea auditable):

1. Una observación es independiente si procede de otra familia documental
   (BCCA/Andalucía, Palencia, Extremadura, BOE/modelo propio, comercial) o de
   otra URL de la misma familia.
2. Solo cuentan las observaciones con unidad compatible con la del recurso.
3. Se confirma si alguna observación independiente cae dentro del ±15 % del
   precio revisado. Fuera de esa banda el veredicto es *divergencia*: el precio
   no se toca y queda documentado el contraste.
4. Sin observación independiente el veredicto es *solo fuente propia*: el precio
   puede estar bien, pero no está verificado y no se confirma.

Uso:
    python tools/verificar_precios_espana.py
    python tools/verificar_precios_espana.py --aplicar
"""
from __future__ import annotations

import argparse
import csv
import glob
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

if __package__:
    from .cruzar_precios_bc3 import unidad as normalizar_unidad
else:
    from cruzar_precios_bc3 import unidad as normalizar_unidad

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"
REGISTRO = DOC / "espana_2026-11-06.csv"
MATRIZ = ROOT / "basedatos_partidas/salida/precios_recursos_espana.csv"
CRIBADO_GLOB = "espana_cribado_*.csv"
ADJUDICACION = DOC / "espana_adjudicacion_2026-11-07.csv"
SALIDA = DOC / "espana_verificacion_2026-11-07.csv"
CONFIRMACIONES = DOC / "espana_confirmaciones_2026-11-07.csv"
PENDIENTES = DOC / "espana_pendientes_verificacion_2026-11-07.csv"
REVISION_MANUAL_GLOB = "espana_revision_manual_*.csv"
BANDA = Decimal("0.15")
# Comercios: dos tiendas no equivalen a una referencia oficial. Se registran
# como contraste, pero no convierten un precio en confirmado.
FAMILIAS_CONFIRMAN = {"bcca", "palencia", "extremadura", "modelo_propio"}
PRECISION_MINIMA = Decimal("0.70")
CAMPOS_CONFIRMACION = ["codigo_recurso", "precio", "fuente", "codigo_fuente", "criterio",
                       "reserva", "incluye_iva", "incluye_transporte"]


def leer(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def numero(valor) -> Decimal | None:
    """Número con coma o punto decimal (los CSV de auditoría mezclan ambos)."""
    texto = str(valor or "").strip().replace(" ", "")
    if not texto:
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        dato = Decimal(texto)
    except Exception:
        return None
    return dato if dato.is_finite() and dato > 0 else None


def sin_acentos(texto: str) -> str:
    reemplazos = str.maketrans("áéíóúüàèìòùâêîôûçÁÉÍÓÚÜ", "aeiouuaeiouaeioucAEIOUU")
    return texto.translate(reemplazos)


def familia(fuente: str, url: str) -> str:
    """Familia documental de una observación (no del precio)."""
    texto = sin_acentos(f"{fuente} {url}").lower()
    if "juntadeandalucia" in texto or "cerp" in texto or "bcca" in texto:
        return "bcca"
    if "diputaciondepalencia" in texto or "palencia" in texto:
        return "palencia"
    if "juntaex" in texto or "gobex" in texto or "extremadura" in texto:
        return "extremadura"
    if "boe.es" in texto:
        return "modelo_propio"
    if url:
        return "comercial:" + (urlparse(url).hostname or "desconocido")
    return "desconocida"


def precio_de_fila(fila: dict) -> Decimal | None:
    """Precio unitario ya normalizado de una fila de fuentes."""
    for campo in ("precio_resultante", "precio_normalizado", "precio_eur"):
        valor = numero(fila.get(campo))
        if valor is not None:
            return valor
    importe, cantidad = numero(fila.get("importe_eur")), numero(fila.get("cantidad"))
    if importe is not None and cantidad:
        return importe / cantidad
    return None


def observaciones_de_fuentes() -> dict[str, list[dict]]:
    """{codigo_recurso: [{familia, precio, unidad, url, fichero}]}."""
    salida: dict[str, list[dict]] = defaultdict(list)
    for ruta in sorted(glob.glob(str(DOC / "espana_fuentes_*.csv"))):
        for fila in leer(Path(ruta)):
            codigo = (fila.get("codigo_recurso") or "").strip()
            precio = precio_de_fila(fila)
            if not codigo or precio is None:
                continue
            url = (fila.get("url") or fila.get("url_precio") or "").strip()
            salida[codigo].append({
                "codigo": (fila.get("codigo_fuente") or "").strip(),
                "familia": familia(fila.get("fuente") or fila.get("vendedor") or "", url),
                "precio": precio,
                "unidad": (fila.get("unidad") or "").strip(),
                "url": url,
                "fichero": Path(ruta).name,
                "detalle": (fila.get("producto") or fila.get("descripcion_fuente") or "")[:90],
            })
    return salida


def observaciones_de_cribado() -> dict[str, list[dict]]:
    """Candidatos de cada banco cribado (BCCA, Extremadura…) con especificación acreditada."""
    salida: dict[str, list[dict]] = defaultdict(list)
    filas = [f for ruta in sorted(glob.glob(str(DOC / CRIBADO_GLOB)))
             for f in leer(Path(ruta))]
    for fila in filas:
        if not fila["codigo_fuente"]:
            continue
        try:
            precision = Decimal(fila["precision"])
        except Exception:
            continue
        if precision < PRECISION_MINIMA or fila["numeros_compatibles"] != "si":
            continue
        precio = numero(fila["precio_fuente"])
        if precio is None:
            continue
        banco = (fila.get("banco") or "bcca").strip() or "bcca"
        salida[fila["codigo_recurso"]].append({
            "codigo": fila["codigo_fuente"],
            "familia": banco,
            "precio": precio,
            "unidad": fila["unidad"],
            "url": (f"{banco} ed. {fila['edicion_fuente']} código {fila['codigo_fuente']} "
                    f"(precio declarado {fila['fecha_precio']})"),
            "fichero": banco,
            "detalle": fila["descripcion_fuente"][:90],
            "precision": precision,
        })
    return salida


FAMILIAS_CITADAS = {
    "bcca": ("bcca", "cerp", "andaluc", "junadeandalucia"),
    "palencia": ("palencia",),
    "extremadura": ("extremadura", "juntaex", "gobex"),
    "modelo_propio": ("boe.es", "boe-", "convenio", "cuotas"),
}


def familias_citadas(recurso: dict) -> set[str]:
    """Familias documentales que ya sostienen el precio revisado.

    Si el precio se construyó con una fuente, esa fuente no puede confirmarlo:
    solo cuenta una observación de otra familia (o de otro banco) que no figure
    ya en la evidencia del recurso.
    """
    texto = " ".join((recurso["fuente_observada"], recurso["criterio_revisado"],
                      recurso["evidencia_y_pendientes"], recurso["edicion_fuente"])).lower()
    citadas = {familia for familia, pistas in FAMILIAS_CITADAS.items()
               if any(pista in texto for pista in pistas)}
    if "media de dos" in texto or "dos ofertas" in texto or "dos referencias" in texto:
        citadas.add("comercial")
    return citadas


def observaciones_de_cierre() -> dict[str, list[dict]]:
    """Referencias oficiales ya documentadas al cerrar un precio sin cambiarlo.

    Al cierre, una referencia oficial dentro del ±15 % se registró como
    ``mantener_sin_cambio_coherente`` en vez de como confirmación explícita.
    Es la misma evidencia y debe contar igual: se incorpora aquí para no
    mantener dos estados distintos ante el mismo hecho.
    """
    salida: dict[str, list[dict]] = defaultdict(list)
    if not ADJUDICACION.exists():
        return salida
    for fila in leer(ADJUDICACION):
        if fila["decision"] != "mantener_sin_cambio_coherente":
            continue
        precio = numero(fila["precio_fuente"])
        if precio is None:
            continue
        salida[fila["codigo_recurso"]].append({
            "codigo": fila["codigo_fuente"],
            "familia": familia(fila["fuente"], ""),
            "precio": precio,
            "unidad": fila["unidad"],
            "url": f"adjudicación de cierre: {fila['fuente']}",
            "fichero": ADJUDICACION.name,
            "detalle": fila["criterio"][:90],
            "de_cierre": True,
        })
    return salida


def es_independiente(obs: dict, citadas: set[str]) -> bool:
    """¿Aporta esta observación una verificación que el precio aún no tenía?"""
    if obs["familia"].startswith("comercial"):
        return "comercial" not in citadas
    return obs["familia"] not in citadas


def revisiones_manuales() -> dict[str, dict]:
    """Correcciones humanas al cribado automático (código → veredicto y motivo).

    El cribado propone; ninguna coincidencia se acepta sin revisar el producto.
    Estas filas dejan constancia de los casos descartados a mano para que no se
    vuelvan a proponer como confirmación en el siguiente banco que se ingiera.
    """
    salida = {}
    for ruta in sorted(glob.glob(str(DOC / REVISION_MANUAL_GLOB))):
        for fila in leer(Path(ruta)):
            salida[fila["codigo_recurso"]] = fila
    return salida


def verificar() -> list[dict]:
    registro = {f["codigo_recurso"]: f for f in leer(REGISTRO)}
    matriz = {f["codigo_recurso"]: f for f in leer(MATRIZ) if f["pais_codigo"] == "ES"}
    fuentes = observaciones_de_fuentes()
    bcca = observaciones_de_cribado()
    cierre = observaciones_de_cierre()
    manuales = revisiones_manuales()
    filas = []
    for codigo, recurso in sorted(registro.items()):
        revisado = numero(recurso["precio_revisado"])
        url_propia = recurso["fuente_observada"].strip()
        propia = familia("", url_propia) if url_propia else "sin_documento"
        candidatas = (list(fuentes.get(codigo, [])) + list(bcca.get(codigo, []))
                      + list(cierre.get(codigo, [])))
        citadas = familias_citadas(recurso)
        independientes, descartadas = [], []
        for obs in candidatas:
            if obs["url"] and obs["url"] == url_propia:
                descartadas.append(f"{obs['familia']}: mismo documento")
                continue
            if (obs["unidad"]
                    and normalizar_unidad(obs["unidad"]) != normalizar_unidad(recurso["unidad"])):
                descartadas.append(f"{obs['familia']}: unidad {obs['unidad']} ≠ {recurso['unidad']}")
                continue
            if not obs.get("de_cierre") and not es_independiente(obs, citadas):
                descartadas.append(f"{obs['familia']}: ya sostiene el precio")
                continue
            independientes.append(obs)
        if recurso["estado_auditoria"] == "confirmado_referencia":
            veredicto, delta, elegida = "ya_confirmado", None, None
            independientes = []
        elif revisado is None:
            veredicto, delta, elegida = "sin_precio_revisado", None, None
        else:
            dentro = [o for o in independientes
                      if abs(o["precio"] / revisado - 1) <= BANDA]
            oficiales = [o for o in dentro if o["familia"] in FAMILIAS_CONFIRMAN]
            if oficiales:
                elegida = min(oficiales, key=lambda o: abs(o["precio"] / revisado - 1))
                veredicto, delta = "confirmado_independiente", elegida["precio"] / revisado - 1
            elif dentro:
                # Coincide, pero solo con comercios: se registra el contraste y no
                # se eleva a confirmado porque no hay referencia oficial detrás.
                elegida = min(dentro, key=lambda o: abs(o["precio"] / revisado - 1))
                veredicto, delta = "contraste_comercial", elegida["precio"] / revisado - 1
            elif independientes:
                elegida = min(independientes, key=lambda o: abs(o["precio"] / revisado - 1))
                veredicto, delta = "divergencia_verificada", elegida["precio"] / revisado - 1
            else:
                veredicto, delta, elegida = "solo_fuente_propia", None, None
        filas.append({
            "codigo_recurso": codigo,
            "categoria": recurso["categoria"],
            "unidad": recurso["unidad"],
            "usos": recurso["partidas_que_lo_usan"],
            "estado_actual": recurso["estado_auditoria"],
            "precio_revisado": recurso["precio_revisado"],
            "precio_matriz": matriz[codigo]["precio_referencia"],
            "familia_propia": propia,
            "familias_citadas": ",".join(sorted(citadas)),
            "observaciones_totales": len(candidatas),
            "observaciones_independientes": len(independientes),
            "familia_independiente": elegida["familia"] if elegida else "",
            "precio_independiente": f"{elegida['precio']:.4f}".rstrip("0").rstrip(".") if elegida else "",
            "delta_pct": f"{delta * 100:+.1f}" if delta is not None else "",
            "codigo_independiente": elegida.get("codigo", "") if elegida else "",
            "detalle_independiente": elegida["detalle"] if elegida else "",
            "veredicto": manuales.get(codigo, {}).get("veredicto") or veredicto,
            "revision_manual": manuales.get(codigo, {}).get("motivo", ""),
            "descartes": " | ".join(descartadas[:3]),
        })
    return filas


def confirmaciones(filas: list[dict], registro: dict[str, dict]) -> list[dict]:
    """Filas listas para el aplicador de confirmaciones."""
    salida = []
    for fila in filas:
        if fila["veredicto"] != "confirmado_independiente":
            continue
        recurso = registro[fila["codigo_recurso"]]
        if recurso["estado_auditoria"] != "en_revision":
            continue
        independiente = Decimal(fila["precio_independiente"])
        salida.append({
            "codigo_recurso": fila["codigo_recurso"],
            "precio": f"{independiente:.4f}".rstrip("0").rstrip("."),
            "fuente": fila["familia_independiente"],
            "codigo_fuente": fila["codigo_independiente"] or fila["familia_independiente"],
            "criterio": (f"Verificación cruzada: el precio revisado de {recurso['precio_revisado']} "
                         f"EUR se sostiene con una observación independiente de "
                         f"{independiente} EUR ({fila['delta_pct']} %, "
                         f"{fila['familia_independiente']})."),
            "reserva": ("Referencia operativa contrastada; no acredita una media nacional ni el "
                        "coste de un proveedor concreto. IVA y transporte siguen sin confirmar."),
            "incluye_iva": "no_confirmado",
            "incluye_transporte": "no_confirmado",
        })
    return salida


QUE_FALTA = {
    ("sin_precio_revisado", "maquinaria"): (
        "Precio de adquisición, vida útil y horas/año para un modelo de coste horario propio.",
        "alta"),
    ("sin_precio_revisado", "materiales"): (
        "Cotización o banco que publique la especificación exacta del recurso.",
        "media"),
    ("solo_fuente_propia", "maquinaria"): (
        "Segunda referencia de alquiler 2026 comparable en potencia y alcance.",
        "alta"),
    ("solo_fuente_propia", "materiales"): (
        "Segunda fuente independiente: otro banco oficial o proveedor distinto del citado.",
        "media"),
    ("solo_fuente_propia", "mano_obra"): (
        "Convenio provincial aplicable al oficio, para sustituir el escenario de coste.",
        "media"),
    ("contraste_comercial", "materiales"): (
        "Referencia oficial (banco o proveedor distinto) que respalde la oferta ya contrastada.",
        "media"),
    ("contraste_comercial", "maquinaria"): (
        "Referencia oficial de alquiler 2026 que respalde la oferta ya contrastada.",
        "alta"),
    ("contraste_comercial", "mano_obra"): (
        "Convenio aplicable que respalde el escenario de coste ya contrastado.",
        "media"),
    ("divergencia_verificada", "materiales"): (
        "Resolver la divergencia con la especificación del banco (presentación, formato, gama).",
        "media"),
    ("divergencia_verificada", "maquinaria"): (
        "Igualar el alcance de la máquina (potencia, consumibles, operador) antes de comparar.",
        "alta"),
    ("divergencia_verificada", "mano_obra"): (
        "Verificar la categoría del oficio en el convenio antes de aceptar la referencia.",
        "media"),
}


def escribir_pendientes(filas: list[dict], registro: dict[str, dict]) -> int:
    """Cola de trabajo explícita: qué falta en cada recurso no verificado."""
    salida = []
    for fila in filas:
        if fila["veredicto"] in ("confirmado_independiente", "ya_confirmado"):
            continue
        recurso = registro[fila["codigo_recurso"]]
        que_falta, esfuerzo = QUE_FALTA.get(
            (fila["veredicto"], recurso["categoria"]),
            ("Definir el recurso y su fuente antes de asignar precio.", "alta"))
        if recurso["partidas_que_lo_usan"].strip() == "0":
            esfuerzo = "baja"
        salida.append({
            "codigo_recurso": fila["codigo_recurso"],
            "categoria": fila["categoria"],
            "unidad": fila["unidad"],
            "usos": fila["usos"],
            "descripcion": recurso["descripcion"][:120],
            "situacion": fila["veredicto"],
            "precio_matriz": fila["precio_matriz"],
            "precio_revisado": fila["precio_revisado"],
            "familia_propia": fila["familia_propia"],
            "que_falta": que_falta,
            "esfuerzo": esfuerzo,
        })
    salida.sort(key=lambda f: ({"alta": 0, "media": 1, "baja": 2}[f["esfuerzo"]],
                               -int(f["usos"] or 0)))
    with PENDIENTES.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=list(salida[0]), delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(salida)
    return len(salida)


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    analizador.add_argument("--salida", type=Path, default=SALIDA)
    analizador.add_argument("--aplicar", action="store_true",
                            help="escribe además la tabla de confirmaciones")
    argumentos = analizador.parse_args()
    filas = verificar()
    with argumentos.salida.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=list(filas[0]), delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)
    cuenta = defaultdict(int)
    for fila in filas:
        cuenta[fila["veredicto"]] += 1
    print(f"{len(filas)} recursos verificados: " +
          ", ".join(f"{k} {v}" for k, v in sorted(cuenta.items(), key=lambda kv: -kv[1])))
    if argumentos.aplicar:
        registro = {f["codigo_recurso"]: f for f in leer(REGISTRO)}
        nuevas = confirmaciones(filas, registro)
        if not nuevas and CONFIRMACIONES.exists():
            print(f"Sin confirmaciones nuevas: se conserva el lote aplicado en "
                  f"{CONFIRMACIONES.relative_to(ROOT)}")
            return 0
        # El lote es acumulativo: conserva las confirmaciones ya aplicadas.
        existentes = leer(CONFIRMACIONES) if CONFIRMACIONES.exists() else []
        vistos = {f["codigo_recurso"] for f in existentes}
        nuevas = existentes + [f for f in nuevas if f["codigo_recurso"] not in vistos]
        with CONFIRMACIONES.open("w", encoding="utf-8-sig", newline="") as manejador:
            escritor = csv.DictWriter(manejador, fieldnames=CAMPOS_CONFIRMACION,
                                      delimiter=";", lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(nuevas)
        print(f"Escritas {len(nuevas)} confirmaciones en {CONFIRMACIONES.relative_to(ROOT)}: "
              f"{[f['codigo_recurso'] for f in nuevas]}")
    registro = {f["codigo_recurso"]: f for f in leer(REGISTRO)}
    pendientes = escribir_pendientes(filas, registro)
    print(f"Cola de trabajo: {pendientes} recursos en {PENDIENTES.relative_to(ROOT)}")
    print(f"Escrito {argumentos.salida}; no se ha modificado ningún precio ni estado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
