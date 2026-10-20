"""Paquetes editoriales de los 17 mercados hispanos posteriores a España.

La estructura de presentación se comparte, no las decisiones editoriales.
Los precios se leen del mismo CSV que importa el producto. No se rellenan
huecos con conversiones, respaldos regionales ni rangos inventados.
Venezuela tiene otra fuente y se identifica expresamente como tarifa interna.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path

from .fechas_texto import consulta_es, mes_anio_es
from .paises import PAISES
from .seo_latam_contenido import MERCADOS

RAIZ = Path(__file__).resolve().parents[1]
MATRIZ = RAIZ / "basedatos_partidas/salida/precios_recursos_latam.csv"
RECURSOS_VE = RAIZ / "basedatos_partidas/datos/recursos.json"
OFICIOS = ("MO-OF1", "MO-AYU", "MO-OF1-PIN", "MO-OF1-PLO", "MO-OF1-ELE")


def _numero(valor: str) -> Decimal | None:
    try:
        numero = Decimal(valor)
        return numero if numero.is_finite() and numero > 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def importe(valor: str | Decimal, codigo: str) -> str:
    """Dos decimales de cálculo en tablas horarias, con separadores del mercado."""
    pais = PAISES[codigo]
    texto = f"{Decimal(valor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"
    texto = texto.replace(",", "M").replace(".", pais["separador_decimal"])
    return texto.replace("M", pais["separador_miles"]) + " " + pais["moneda"]


@lru_cache(maxsize=1)
def _matriz() -> dict[str, dict[str, dict]]:
    mercados: dict[str, dict[str, dict]] = {}
    try:
        with MATRIZ.open(encoding="utf-8-sig", newline="") as archivo:
            for fila in csv.DictReader(archivo, delimiter=";"):
                codigo = fila.get("pais_codigo", "")
                pais = PAISES.get(codigo)
                # Nunca mezclar mercado, moneda, unidad o referencias provisionales.
                if (codigo not in MERCADOS or codigo == "VE" or not pais
                        or fila.get("moneda") != pais["moneda"]
                        or fila.get("categoria") != "mano_obra"
                        or fila.get("unidad_fuente") != "h"
                        or fila.get("confianza") not in {"referencia", "derivado"}
                        or _numero(fila.get("precio_referencia", "")) is None):
                    continue
                mercados.setdefault(codigo, {})[fila["codigo_recurso"]] = fila
    except (OSError, csv.Error):
        # Una ausencia de artefactos no debe convertirse en cifras ficticias.
        return {}
    return mercados


@lru_cache(maxsize=1)
def _base_venezuela() -> dict[str, dict]:
    try:
        with RECURSOS_VE.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        if datos.get("_moneda") != "USD":
            return {}
        return {
            codigo: fila for codigo, fila in datos.get("mano_obra", {}).items()
            if fila.get("unidad") == "h" and _numero(str(fila.get("precio", ""))) is not None
        }
    except (OSError, ValueError, AttributeError):
        return {}


@lru_cache(maxsize=1)
def _revision_venezuela() -> str:
    """Mes de la revisión declarada del cuadro base VE («agosto de 2026»).

    Vive en la clave ``_revision`` de recursos.json («2026-08 · segunda
    ronda…»): la tabla lo deriva de los datos en vez de llevar el mes
    escrito a mano en dos sitios (Fase 2). Cadena vacía si no se puede
    leer o no se entiende: la guía no inventa la fecha.
    """
    try:
        with RECURSOS_VE.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return mes_anio_es(str(datos.get("_revision") or ""))
    except (OSError, ValueError, AttributeError):
        return ""


def tabla_mano_obra(codigo: str) -> dict:
    revision_ve = _revision_venezuela() if codigo == "VE" else ""
    fechas: list[str] = []
    filas = []
    for recurso in OFICIOS:
        if codigo == "VE":
            fila = _base_venezuela().get(recurso)
            if fila:
                filas.append([
                    recurso, _nombre_oficio(recurso, codigo),
                    importe(str(fila["precio"]), codigo) + "/h",
                    "No documentado", "Tarifa interna, no coste empresa validado",
                    f"Revisión del cuadro: {revision_ve}" if revision_ve
                    else "Revisión del cuadro sin fecha documentada",
                ])
        else:
            fila = _matriz().get(codigo, {}).get(recurso)
            if not fila:
                continue
            fechas.append(fila.get("fecha_consulta") or "")
            minimo, maximo = _numero(fila.get("precio_min", "")), _numero(fila.get("precio_max", ""))
            central = Decimal(fila["precio_referencia"])
            rango = "Sin rango documentado"
            if minimo is not None and maximo is not None and minimo <= central <= maximo:
                rango = ("Sin dispersión documentada" if minimo == maximo else
                         f"{importe(minimo, codigo)}–{importe(maximo, codigo)}/h")
            filas.append([
                recurso, _nombre_oficio(recurso, codigo), importe(central, codigo) + "/h", rango,
                "Derivado de otro oficio" if fila["confianza"] == "derivado" else "Referencia del modelo",
                fila.get("fecha_consulta") or "Sin fecha documentada",
            ])
    # La nota deriva su fecha de los datos (Fase 2): cuando la matriz se
    # reconsulte, la guía dirá el mes nuevo sin tocar código.
    if not filas:
        nota = ("Datos no disponibles en este despliegue. Confirma los costes "
                "con tu empresa; no se publican cifras de respaldo.")
    elif codigo == "VE":
        declarada = (
            f"revisión declarada de {revision_ve}" if revision_ve
            else "sin fecha de revisión declarada"
        )
        nota = (
            f"Cuadro base USD de Venezuela, {declarada}. No es una encuesta "
            "salarial ni una referencia validada de coste empresa. No hay "
            "rango nacional documentado."
        )
    else:
        consulta = consulta_es(fechas)
        nota = (
            (f"Precios consultados {consulta}. " if consulta else "")
            + "Fuente: matriz nacional CotizaT, investigación de jornales y revisión de coste empresa (ronda 7). "
            "El rango es el del catálogo, no un intervalo estadístico ni una tarifa por ciudad. "
            "Las fechas de consulta se conservan: publicar en octubre no actualiza esos precios."
        )
    return {
        "cabecera": ["Código", "Oficio", "Tarifa interna" if codigo == "VE" else "Coste empresa modelado",
                     "Rango de referencia", "Naturaleza del dato", "Consulta de la fuente"],
        "filas": filas,
        "nota": nota,
    }


def _nombre_oficio(recurso: str, codigo: str) -> str:
    if recurso == "MO-OF1-PLO":
        return PAISES[codigo]["vocab"].split(",")[-1].strip().capitalize()
    return {
        "MO-OF1": "Oficial de primera", "MO-AYU": "Ayudante",
        "MO-OF1-PIN": "Oficial pintor", "MO-OF1-ELE": "Oficial electricista",
    }[recurso]


def _ejemplo_cuadrilla(codigo: str) -> str:
    if codigo == "VE":
        base = _base_venezuela()
        valores = [str(base.get(recurso, {}).get("precio", "")) for recurso in OFICIOS[:2]]
    else:
        base = _matriz().get(codigo, {})
        valores = [base.get(recurso, {}).get("precio_referencia", "") for recurso in OFICIOS[:2]]
    numeros = [_numero(valor) for valor in valores]
    if any(numero is None for numero in numeros):
        return "No hay una pareja de tarifas verificable en los artefactos del despliegue. Usa 8/R horas por integrante y por unidad, con R como producción hipotética por jornada de ocho horas; sustituye las tarifas por costes confirmados de tu equipo."
    coste = sum(numeros, Decimal(0)) * Decimal("0.4")
    return (
        "Ejemplo didáctico, no rendimiento recomendado ni precio de mercado: supón un oficial y un ayudante "
        "que completan 20 m² en una jornada de ocho horas. Cada integrante consume 8/20 = 0,4 h/m². "
        f"Con los valores de la tabla, la mano de obra del ejemplo sería {importe(coste, codigo)}/m² "
        "(0,4 × la suma de ambas tarifas). Faltan materiales, equipo, otros costes y margen. "
        "Si la producción baja a 10 m², esas horas por unidad se duplican. No presupuestes esa producción "
        "sin medir tu cuadrilla en las condiciones de la obra."
    )


def _base(codigo: str, slug: str, titulo: str, lead: str, tipo: str) -> dict:
    pais = PAISES[codigo]
    return {
        "slug": slug, "pais": codigo, "pais_nombre": pais["nombre"],
        "pais_path": f"/{codigo.lower()}/", "kicker": f"{pais['nombre']} · {tipo}",
        "h1": titulo, "title": titulo + " | CotizaT", "lead": lead,
        "description": f"{titulo}. Datos y método en {pais['moneda']}, sin facturación fiscal.",
        # Ninguna pieza técnica se presenta automáticamente como tutorial normativo.
        "schema_howto": False,
    }


def _labor(codigo: str, perfil: dict) -> dict:
    pais = PAISES[codigo]
    titulo = f"Mano de obra de construcción en {pais['nombre']}: referencias 2026"
    slug = f"mano-obra-construccion-{perfil['slug']}"
    lead = (
        f"Cómo estudiar la mano de obra en {pais['nombre']} sin confundir jornal, coste empresa y precio de venta. "
        f"Tabla en {pais['moneda']} leída del catálogo, con naturaleza del dato y fecha de consulta visibles. "
        "No es una promesa de tarifas vigentes ni de precios por ciudad."
    )
    articulo = _base(codigo, slug, titulo, lead, "Mano de obra")
    articulo["secciones"] = [
        ("Qué comprobar en este mercado", [perfil["labor"]]),
        ("Tabla del catálogo y fecha real de los datos", [{"tabla": tabla_mano_obra(codigo)}]),
        ("Metodología: qué incluye y qué no", [
            "En los dieciséis mercados con matriz nacional, el modelo parte de jornales investigados, "
            "aplica un factor de coste empresa y divide por ocho horas. Los factores aproximan aportes y "
            "prestaciones del contexto investigado; no sustituyen una liquidación individual ni garantizan "
            "ocho horas facturables por día. Venezuela queda fuera de ese modelo: solo se muestra la tarifa "
            "interna del cuadro base. No se convierte una cifra regional para simular una investigación local.",
            "Referencia del modelo no significa observación directa de una factura de contratista. Derivado "
            "de otro oficio significa que no se investigó un jornal independiente para esa especialidad. "
            "Si mínimo y máximo coinciden, no se conoce una dispersión. Los valores no incluyen el margen "
            "comercial ni determinan por sí solos transporte, herramienta o precio final del servicio.",
        ]),
        ("Convertir la hora a coste de una partida", [_ejemplo_cuadrilla(codigo)]),
        ("Revisar antes de enviar un precio al cliente", [
            "Pide una cotización o acuerdo actual de tu equipo, define qué gastos incluye y estima la "
            "producción útil en la obra. Si ya usas un coste empresa cargado, no vuelvas a aplicar las mismas "
            "prestaciones como otro porcentaje. Conserva fuente y fecha del coste propio; si el valor deja de "
            "servir, sustitúyelo antes de emitir una nueva propuesta. La tabla pública no demuestra que esos "
            "precios estén cargados en tu cuenta ni en la base de producción.",
        ]),
    ]
    articulo["faq"] = [
        {"q": "¿Son precios de hoy o salarios mínimos oficiales?", "a": "No. Son referencias históricas del catálogo con su fecha de consulta, no una tabla salarial normativa vigente ni precios garantizados."},
        {"q": "¿Puedo usar el valor horario como precio al cliente?", "a": "No directamente. Revisa producción, materiales, equipo y otros costes; después decide margen y tratamiento del impuesto del documento."},
        {"q": "¿Un rango igual en ambos extremos significa que no hay variación?", "a": "No. Significa que la fuente no documenta dispersión para esa referencia. No se inventa una banda para completarla."},
    ]
    return articulo


def _editorial(codigo: str, especificacion: tuple, tipo: str) -> dict:
    slug, titulo, lead, secciones = especificacion
    articulo = _base(codigo, slug, titulo, lead, tipo)
    articulo["secciones"] = [(titulo, [texto]) for titulo, texto in secciones]
    if tipo == "Documento comercial":
        articulo["secciones"].append(("Lista de revisión de la propuesta", [{"tabla": {
            "cabecera": ["Revisión", "Comprobación antes del envío"],
            "filas": [
                ["Identificación", f"Empresa, {PAISES[codigo]['id_fiscal']} cuando corresponda, cliente, obra, número y fecha"],
                ["Cantidades", "Unidad, medición y alcance de cada partida; no solo un importe global"],
                ["Opciones", "Una alternativa incluida; opcionales separados del total contratado"],
                ["Resumen", f"Importes en {PAISES[codigo]['moneda']}, base, impuesto revisado y total"],
                ["Condiciones", "Vigencia, exclusiones, pagos y versión inequívoca del documento"],
            ],
            "nota": "Es una estructura de revisión, no un archivo PDF descargable, contrato homologado ni factura fiscal.",
        }}]))
    else:
        articulo["secciones"].append(("Comprobar el rendimiento antes de fijar la venta", [
            _ejemplo_cuadrilla(codigo),
            "El ejemplo solo estudia la mano de obra. El APU completo debe añadir los consumos de material "
            "y equipo pertinentes, sin duplicar transporte, pérdidas o prestaciones ya incluidas. Un margen "
            "sobre coste no es el mismo porcentaje que margen sobre venta: especifica qué operación usas "
            "antes de comparar el beneficio esperado con el total comercial.",
        ]))
    articulo["faq"] = [
        {"q": "¿Esta guía sustituye revisión técnica, laboral o tributaria?", "a": "No. Organiza un presupuesto comercial de obra privada. Los criterios de contrato y obligaciones locales requieren validación profesional."},
        {"q": "¿Cómo llevo el método a CotizaT?", "a": "Selecciona el mercado de tu empresa, comprueba moneda y recursos, registra mediciones y partidas y revisa el documento antes de enviarlo. No se promete cálculo normativo ni facturación electrónica."},
    ]
    return articulo


@lru_cache(maxsize=1)
def _articulos() -> dict[str, dict]:
    articulos = {}
    for codigo, perfil in MERCADOS.items():
        propios = []
        if perfil.get("documento"):
            propios.append(_editorial(codigo, perfil["documento"], "Documento comercial"))
        propios.append(_labor(codigo, perfil))
        propios.append(_editorial(codigo, perfil["tecnica"],
                                  "Documento comercial" if codigo == "DO" else "Análisis técnico"))
        relacionados = [(a["h1"], f"/{codigo.lower()}/guia/{a['slug']}") for a in propios]
        if perfil.get("existente"):
            relacionados.append(("Guía inicial del mercado", f"/{codigo.lower()}/guia/{perfil['existente']}"))
        for articulo in propios:
            articulo["related"] = [
                ("Software de presupuestos", f"/{codigo.lower()}/software-presupuestos"),
                ("Análisis de precios unitarios", f"/{codigo.lower()}/apu"),
                ("Presupuestos de remodelación", f"/{codigo.lower()}/remodelacion"),
            ] + [(nombre, ruta) for nombre, ruta in relacionados if ruta.rsplit("/", 1)[-1] != articulo["slug"]]
            articulos[articulo["slug"]] = articulo
    return articulos


def articulo(slug: str) -> dict | None:
    return _articulos().get(slug)


def guias() -> list[dict]:
    return list(_articulos().values())


def contexto_local(codigo: str, tema: str = "") -> list[tuple[str, list[str]]]:
    """Objeción propia también en landing y hubs, no solo en el artículo."""
    perfil = MERCADOS.get(codigo)
    if not perfil:
        return []
    especificacion = perfil["tecnica"]
    if tema in {"software-presupuestos", "remodelacion"} and perfil.get("documento"):
        especificacion = perfil["documento"]
    return [(especificacion[1], [especificacion[2], perfil["labor"]])]
