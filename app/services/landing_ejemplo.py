"""Ejemplos de la landing adaptados a la moneda y el idioma del país.

La landing vende el producto con dos ejemplos: un presupuesto completo de
remodelación de baño y un análisis de precios unitarios (APU) real del
catálogo. Hasta ahora todos los importes estaban grabados en dólares:
quien abría la página desde Colombia o México veía un ejemplo en una moneda
que no es la suya y con IVA ajeno.

Este módulo convierte los ejemplos a la moneda del país visitante usando la
tasa de referencia verificada del servicio de tasas (la misma que la app
ofrece al configurar la organización) y los formatea con los símbolos
inequívocos y decimales de cada moneda: ``2.512,52 US$``, ``7.864.401 COL$``,
``42.863,68 MX$``. También traduce los nombres de las partidas del catálogo
base (venezolano) al habla del país (friso → pañete / aplanado) con el
servicio de traducción real, y adapta IVA, razón social y ciudad.

Reglas aritméticas: los totales visibles se derivan de las filas visibles
(los importes se redondean a los decimales de la moneda y los subtotales son
la suma exacta de lo que se muestra), para que un presupuesto de ejemplo de
una herramienta de presupuestos sume bien en cualquier moneda.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..utils import decimales_moneda, fmt_num, simbolo_moneda
from .tasa import TASAS_ACTUALIZADAS, tasa_sugerida
from .traduccion import traducir

# ─────────────────────────────────────────────────────────────────────────────
# Presupuesto de ejemplo (remodelación de baño) — base USD del catálogo
#
# Cada partida: (nombre, unidad, cantidad, precio_unitario, coste_interno).
# El beneficio de fila = importe − coste. Los importes provienen de partidas
# reales del catálogo con margen del 35 % s/coste (elección de la empresa).
# "tiempo" es el desglose horas oficiales+ayudante de la partida.
# ─────────────────────────────────────────────────────────────────────────────

_CAPITULOS: list[tuple[str, list[tuple]]] = [
    (
        "Demoliciones y desmontajes",
        [
            ("Picado de enchapado cerámico en pared y su capa de pega", "m²", 20, 6.52, 96.58, "14 h · 0+14"),
            ("Demolición de piso cerámico y su capa de pega", "m²", 6, 5.06, 22.49, "3,2 h · 0+3,2"),
            ("Desmontaje de aparato sanitario y su grifería", "ud", 3, 4.74, 10.53, "2 h · 1+1"),
        ],
    ),
    (
        "Instalaciones (plomería del baño)",
        [
            ("Tubería de agua de PPR de 20 mm, empotrada, incluso roza y resane", "m", 12, 8.09, 71.94, "5,5 h · 3,1+2,4"),
            ("Punto de agua fría y caliente para aparato sanitario", "ud", 3, 39.56, 87.90, "5,7 h · 3,3+2,4"),
            ("Llave de escuadra para aparato", "ud", 4, 14.70, 43.55, "2,4 h · 1,6+0,8"),
            ("Punto de desagüe para inodoro", "ud", 1, 18.62, 13.79, "0,7 h · 0,5+0,2"),
            ("Instalación de inodoro con su conexión de agua y desagüe", "ud", 1, 29.32, 21.71, "1,8 h · 1,2+0,6"),
            ("Instalación de lavamanos con su grifería y desagüe", "ud", 1, 42.20, 31.26, "2,1 h · 1,4+0,7"),
            ("Instalación de ducha o regadera con su grifería", "ud", 1, 22.60, 16.74, "1,7 h · 1,1+0,6"),
        ],
    ),
    (
        "Aislamientos e impermeabilizaciones",
        [
            ("Impermeabilización de piso de baño o ducha bajo enchapado", "m²", 6, 19.32, 85.88, "4,1 h · 2,5+1,6"),
            ("Mortero impermeabilizante en área húmeda, base para enchapado", "m²", 8, 11.89, 70.47, "4,4 h · 2,6+1,8"),
        ],
    ),
    (
        "Revestimientos y acabados",
        [
            ("Friso de mortero maestreado sobre paramento interior, 1,5 cm", "m²", 22, 8.71, 141.87, "16,5 h · 9,9+6,6"),
            ("Enchapado de porcelanato de gran formato en pared", "m²", 18, 13.28, 177.07, "18,9 h · 11,2+7,7"),
            ("Enchapado de zona de ducha sobre impermeabilización", "m²", 4, 17.14, 50.78, "4,1 h · 2,7+1,4"),
            ("Colocación de piso de porcelanato de gran formato, en capa fina", "m²", 6, 11.43, 50.80, "5,4 h · 2,7+2,7"),
            ("Piso cerámico en área húmeda con pendiente a desagüe", "m²", 6, 16.40, 72.88, "5,6 h · 3,7+1,9"),
        ],
    ),
]

# Productos a elección del cliente: (nombre, imagen, unidad, cantidad, precio).
# En el ejemplo los productos también llevan el margen ilustrativo del 35 %.
_PRODUCTOS: list[tuple[str, str, str, float, float]] = [
    ("Porcelanato de gran formato 60×120 cm (pared)", "img/prod-porcelanato-pared.jpg", "m²", 18, 24.00),
    ("Porcelanato 60×60 cm (piso)", "img/prod-porcelanato-piso.jpg", "m²", 12, 18.00),
    ("Columna de ducha termostática", "img/prod-columna-ducha.jpg", "ud", 1, 180.00),
    ("Mueble de baño con lavamanos, 60 cm", "img/prod-mueble-bano.jpg", "ud", 1, 150.00),
    ("Inodoro de tanque, una pieza", "img/prod-inodoro.jpg", "ud", 1, 95.00),
]

_MARGEN_ILUSTRATIVO = 0.35  # margen s/coste aplicado por la empresa del ejemplo

_HORAS_TOTALES = 98  # Σ horas-hombre de las partidas del ejemplo
_DURACION_TXT = "≈ 6 días"

_EMPRESA = "Construcciones Alfa"
_OBRA = "Remodelación de baño"
_RESIDENCIA = "Res. Los Naranjos"

# ─────────────────────────────────────────────────────────────────────────────
# APU de ejemplo — partida real del catálogo (muro de cerramiento de bloque)
# ─────────────────────────────────────────────────────────────────────────────

_APU_CODIGO = "14.04.01.060"
_BASE_DATOS = Path(__file__).resolve().parents[2] / "basedatos_partidas"
_GRUPO_ETIQUETA = {"materiales": "Material", "mano_obra": "Mano de obra", "maquinaria": "Equipo"}
# Unidades del cuadro de recursos → glifos con superíndice para la web
_UNIDADES_WEB = {"m2": "m²", "m3": "m³", "cm2": "cm²", "kg/cm2": "kg/cm²"}


def _unidad_web(u: str) -> str:
    u = str(u or "").strip()
    return _UNIDADES_WEB.get(u, u)


@lru_cache(maxsize=1)
def _apu_base() -> dict | None:
    """APU base en USD, leído del catálogo real (descompuesto + recursos)."""
    try:
        ruta = _BASE_DATOS / "datos" / "descompuestos" / f"{_APU_CODIGO}.json"
        partida = json.loads(ruta.read_text(encoding="utf-8"))
        cuadro = json.loads(
            (_BASE_DATOS / "datos" / "recursos.json").read_text(encoding="utf-8")
        )
        indice: dict[str, tuple[str, dict]] = {}
        for grupo in ("materiales", "mano_obra", "maquinaria"):
            for ref, datos in (cuadro.get(grupo) or {}).items():
                indice[ref] = (grupo, datos)
        filas = []
        for r in partida.get("recursos", []):
            grupo, info = indice.get(r["ref"], (None, None))
            if info is None:
                continue
            descripcion = str(info.get("descripcion") or r["ref"])
            corto = descripcion.split(",")[0].split(". ")[0].strip().rstrip(".")
            for bruto, bonito in (("kg/cm2", "kg/cm²"), ("m2", "m²"), ("m3", "m³")):
                corto = corto.replace(bruto, bonito)
            filas.append(
                {
                    "grupo": grupo,
                    "nombre": corto,
                    "rendimiento": float(r["rendimiento"]),
                    "unidad_rend": _unidad_web(info.get("unidad")),
                    "precio_usd": float(info.get("precio") or 0),
                }
            )
        return {
            "codigo": partida.get("codigo") or _APU_CODIGO,
            "titulo": str(partida.get("titulo") or "").rstrip("."),
            "unidad": _unidad_web(partida.get("unidad") or "m²"),
            "descripcion": str(partida.get("descripcion") or ""),
            "complementarios_pct": float(partida.get("complementarios_pct") or 0),
            "margen": float(partida.get("margen") or 0.30),
            "filas": filas,
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Formateo por moneda
# ─────────────────────────────────────────────────────────────────────────────


def _fmt_cant(v: float) -> str:
    return str(int(v)) if float(v) == int(v) else fmt_num(v, 2)


def _monto(valor: float, moneda: str, dec: int) -> str:
    return f"{fmt_num(valor, dec)} {simbolo_moneda(moneda)}"


def _precio_u(valor: float, moneda: str, unidad: str) -> str:
    return f"{fmt_num(valor, 2)} {simbolo_moneda(moneda)}/{unidad}"


@lru_cache(maxsize=32)
def contexto_ejemplo(codigo_pais: str | None) -> dict:
    """Todo lo que la landing muestra del ejemplo, ya formateado por país.

    Nunca lanza: si algo falla (moneda sin tasa, catálogo ausente) degrada a
    USD genérico antes que romper la página pública.
    """
    from ..paises import PAIS_GENERICO, PAISES

    pais = PAISES.get(str(codigo_pais or "").strip().upper()) if codigo_pais else None
    if pais is None:
        pais = PAIS_GENERICO
    codigo = pais.get("codigo") or ""

    moneda = pais.get("moneda") or "USD"
    tasa = 1.0 if moneda == "USD" else (tasa_sugerida(moneda) or 1.0)
    if moneda != "USD" and tasa == 1.0:
        # Moneda local sin tasa verificada: no se inventa conversión.
        moneda = "USD"
    dec = decimales_moneda(moneda)
    convierte = moneda != "USD"
    iva = int(pais.get("iva") or 16)

    def monto(v: float) -> str:
        return _monto(v, moneda, dec)

    def precio_u(v: float, unidad: str) -> str:
        return _precio_u(v, moneda, unidad)

    # ---- Capítulos y partidas -------------------------------------------------
    caps = []
    total_obra = coste_obra = ben_obra = 0.0
    for idx, (titulo, partidas) in enumerate(_CAPITULOS, start=1):
        filas = []
        sub = sub_coste = sub_ben = 0.0
        for nombre, unidad, cantidad, precio_usd, coste_usd, tiempo in partidas:
            precio = round(precio_usd * tasa, 2)
            importe = round(precio * cantidad, dec)
            coste = round(coste_usd * tasa, dec)
            ben = round(importe - coste, dec)
            sub += importe
            sub_coste += coste
            sub_ben += ben
            filas.append(
                {
                    "nombre": traducir(nombre, codigo),
                    "cant": f"{_fmt_cant(cantidad)} {unidad}",
                    "precio": precio_u(precio, unidad),
                    "importe": monto(importe),
                    "coste": monto(coste),
                    "beneficio": monto(ben),
                    "margen": f"+{int(round(100 * ben / coste))} %" if coste else "",
                    "tiempo": tiempo,
                }
            )
        total_obra = round(total_obra + sub, dec)
        coste_obra = round(coste_obra + sub_coste, dec)
        ben_obra = round(ben_obra + sub_ben, dec)
        caps.append(
            {
                "titulo": f"{idx:02d} · {traducir(titulo, codigo)}",
                "importe": monto(sub),
                "beneficio": f"+ {monto(sub_ben)}",
                "partidas": filas,
            }
        )

    # ---- Productos -------------------------------------------------------------
    productos = []
    total_prod = coste_prod = 0.0
    for nombre, img, unidad, cantidad, precio_usd in _PRODUCTOS:
        precio = round(precio_usd * tasa, 2)
        importe = round(precio * cantidad, dec)
        coste = round(importe / (1 + _MARGEN_ILUSTRATIVO), dec)
        total_prod = round(total_prod + importe, dec)
        coste_prod = round(coste_prod + coste, dec)
        productos.append(
            {
                "nombre": traducir(nombre, codigo),
                "img": img,
                "cant": f"{_fmt_cant(cantidad)} {unidad}",
                "precio": precio_u(precio, unidad),
                "importe": monto(importe),
            }
        )

    subtotal = round(total_obra + total_prod, dec)
    coste_interno = round(coste_obra + coste_prod, dec)
    beneficio = round(subtotal - coste_interno, dec)
    margen_pct = int(round(100 * beneficio / coste_interno)) if coste_interno else 35
    iva_monto = round(subtotal * iva / 100, dec)
    total = round(subtotal + iva_monto, dec)

    # ---- APU real del catálogo ---------------------------------------------------
    apu: dict = {"disponible": False}
    base = _apu_base()
    if base and base["filas"]:
        filas = []
        grupos = {"materiales": 0.0, "mano_obra": 0.0, "maquinaria": 0.0}
        for f in base["filas"]:
            precio = round(f["precio_usd"] * tasa, 2)
            importe = round(precio * f["rendimiento"], dec)
            grupos[f["grupo"]] = round(grupos[f["grupo"]] + importe, dec)
            filas.append(
                {
                    "grupo": _GRUPO_ETIQUETA.get(f["grupo"], "Equipo"),
                    "nombre": f["nombre"],
                    "rend": f"{fmt_num(f['rendimiento'], 2)} {f['unidad_rend']}",
                    "precio": precio_u(precio, f["unidad_rend"]),
                    "importe": monto(importe),
                }
            )
        directo = round(sum(grupos.values()), dec)
        comp = round(directo * base["complementarios_pct"] / 100, dec)
        coste = round(directo + comp, dec)
        margen_apu = base["margen"]
        pv = round(coste * (1 + margen_apu), dec)
        horas_mo = sum(
            f["rendimiento"] for f in base["filas"] if f["grupo"] == "mano_obra"
        )
        apu = {
            "disponible": True,
            "codigo": base["codigo"],
            "titulo": traducir(base["titulo"], codigo),
            "unidad": base["unidad"],
            "descripcion": base["descripcion"],
            "filas": filas,
            "materiales": monto(grupos["materiales"]),
            "mano_obra": monto(grupos["mano_obra"]),
            "equipo": monto(grupos["maquinaria"]),
            "directo": monto(directo),
            "comp_pct": fmt_num(base["complementarios_pct"], 0),
            "comp": monto(comp),
            "coste": monto(coste),
            "margen": f"+{int(round(margen_apu * 100))} %",
            "precio": precio_u(pv, base["unidad"]),
            "horas_mo": f"{fmt_num(horas_mo, 2)} h-hombre/{base['unidad']}",
        }

    # ---- Identidad del ejemplo por país -------------------------------------------
    empresa = _EMPRESA
    razon = str(pais.get("razon_social_ejemplo") or "").strip()
    if razon:
        empresa = f"{empresa}, {razon}"
    ciudad = str(pais.get("ciudad_ejemplo") or "").strip()
    residencia = _RESIDENCIA + (f" · {ciudad}" if ciudad else "")

    fecha_tasa = str(TASAS_ACTUALIZADAS)
    try:
        a, m, d = fecha_tasa.split("-")
        fecha_tasa = f"{d}/{m}/{a}"
    except Exception:
        pass

    return {
        "moneda": moneda,
        "simbolo": simbolo_moneda(moneda),
        "decimales": dec,
        "convierte": convierte,
        "tasa": tasa,
        "tasa_txt": fmt_num(tasa, 2),
        "tasa_fecha": fecha_tasa,
        "iva": iva,
        "iva_txt": f"I.V.A. ({iva} %)",
        "margen_txt": f"+{margen_pct} %",
        "empresa": empresa,
        "ciudad": ciudad,
        "obra": _OBRA,
        "residencia": residencia,
        "moneda_local": pais.get("moneda_local") or "USD",
        # Vocabulario local para el texto de la landing (friso → pañete/aplanado…)
        "term_pared": traducir("Friso", codigo),
        "term_enchapado": traducir("enchapado", codigo),
        # Hero (documento resumido)
        "hero": {
            "caps": [
                {"nombre": c["titulo"].split("· ", 1)[-1], "importe": c["importe"]}
                for c in caps
            ]
            + [{"nombre": "Productos a elección del cliente", "importe": monto(total_prod)}],
            "total": monto(total),
        },
        # Constructor
        "caps": caps,
        "productos": productos,
        "tot": {
            "obra": monto(total_obra),
            "productos": monto(total_prod),
            "subtotal": monto(subtotal),
            "coste": monto(coste_interno),
            "beneficio": monto(beneficio),
            "margen": f"+{margen_pct} % s/coste",
            "iva": monto(iva_monto),
            "total": monto(total),
        },
        "resumen": {
            "margen": f"+{margen_pct} %",
            "beneficio": monto(beneficio),
            "horas": f"{_HORAS_TOTALES} h-hombre",
            "horas_split": "👷 49 h oficial · 🧑 49 h ayudante",
            "duracion": _DURACION_TXT,
            "cuadrilla": "cuadrilla de 2 · 1 oficial + 1 ayudante",
        },
        # Tour
        "tour": {
            "volumen": monto(42500),
            "cap4_titulo": caps[3]["titulo"],
            "cap4": caps[3]["partidas"],
            "total": monto(total),
        },
        "apu": apu,
    }
