"""Precios públicos del catálogo por país (Fase 5 — SEO programático).

Publica una página por partida y país con el precio unitario que la app
usa de verdad en ese mercado: mismo descompuesto, mismos precios de
recursos por país, misma fórmula ``(directo + complementarios) ×
(1 + margen)`` que al construir ``partidas.csv`` (verificado al céntimo
contra la base). Los datos salen de los ficheros del repo
(``basedatos_partidas/datos`` y ``salida/precios_recursos_*.csv``): la
base de datos de los clientes no se toca y las páginas son cacheables
por CDN porque país e idioma viven en la URL.

Guardia anti-contenido-fino (es código, no intención): una partida solo
existe como URL en un país si tiene el precio COMPLETO ahí (todos sus
recursos con precio), al menos 3 líneas de descompuesto, descripción en
el idioma del mercado de al menos 120 caracteres y, en mercados de
habla inglesa, ningún resto de español en título, descripción, nombres
de recursos ni de su apartado o capítulo (las traducciones salen de las tablas del titular vía
``services.traduccion``; lo que no esté traducido, no se publica). Un
apartado solo existe si conserva al menos 3 partidas publicables.

Encender un país es añadirlo a ``PAISES_PRECIOS_PUBLICOS`` y solo eso:
rutas, sitemap e hreflang lo recogen solos. Orden de encendido,
verificando cada país antes del siguiente: primero los cinco
mercados ingleses (US → GB → CA → AU → IE, 2026-10-21) y después los
hispanos con matriz propia (ES → MX → CO → AR → CL → PE → EC → DO →
UY → PY → BO → PA → CR → GT → HN → SV → NI). Venezuela no tiene
matriz en el repo —la app cotiza VE con los precios base USD de
``recursos.json``—: se encenderá cuando tenga la suya.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from ..paises import PAISES
from .traduccion import traducir, traducir_recurso_por_codigo
from .unidades_precio import (
    cantidad_mostrada,
    es_imperial_codigo,
    precio_mostrado,
    rendimiento_mostrado,
    rendimiento_recurso_mostrado,
    unidad_mostrada,
)

# Interruptor por país (ver docstring del módulo).
PAISES_PRECIOS_PUBLICOS: tuple[str, ...] = ("US", "GB", "CA", "AU", "IE", "ES", "MX", "CO", "AR", "CL", "PE")

_MIN_LINEAS = 3
_MIN_DESCRIPCION = 120
_MIN_PARTIDAS_APARTADO = 3

_RAIZ = Path(__file__).resolve().parents[2]
_DATOS = _RAIZ / "basedatos_partidas" / "datos"
_SALIDA = _RAIZ / "basedatos_partidas" / "salida"

_GRUPOS = ("materiales", "mano_obra", "maquinaria")

# Detector de restos en español sobre textos ya traducidos: regla de
# tildes/eñe + vocabulario inequívoco. Si algo suena a español, la
# partida no se publica en ese mercado (mejor perder 2 URLs que colar
# una página en «inglés» con prosa sin traducir).
_RE_PALABRA = re.compile(r"[a-záéíóúñü]+")
_ACENTOS = frozenset("áéíóúñ")
_ES_FUERTE = frozenset(
    {
        "de", "la", "el", "con", "para", "por", "los", "las", "una", "uno",
        "del", "que", "incluye", "incluir", "medido", "medida", "existente",
        "previa", "previo", "obra", "unidad", "precio", "presupuesto",
        "partida", "recursos", "instalacion", "instalaciones", "segun",
        "sobre", "hasta", "desde", "espesor", "mortero", "hormigon",
        "colocacion", "suministro", "ejecucion", "superficie", "pared",
        "techo", "suelo", "puerta", "ventana", "tuberia", "cable",
    }
)


def _sin_restos_es(texto: str) -> bool:
    for palabra in _RE_PALABRA.findall((texto or "").lower()):
        if palabra in _ES_FUERTE or any(c in _ACENTOS for c in palabra):
            return False
    return True


def _slug(texto: str, maximo: int = 84) -> str:
    plano = unicodedata.normalize("NFKD", str(texto or ""))
    plano = "".join(c for c in plano if not unicodedata.combining(c)).lower()
    plano = re.sub(r"[^a-z0-9]+", "-", plano).strip("-")
    plano = re.sub(r"-{2,}", "-", plano)
    if len(plano) > maximo:
        plano = plano[:maximo].rsplit("-", 1)[0].strip("-")
    return plano


def _numero(valor) -> float:
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


@lru_cache(maxsize=1)
def _recursos() -> dict[str, dict]:
    bruto = json.loads((_DATOS / "recursos.json").read_text(encoding="utf-8"))
    salida: dict[str, dict] = {}
    for grupo in _GRUPOS:
        for codigo, ficha in (bruto.get(grupo) or {}).items():
            salida[codigo] = {
                "grupo": grupo,
                "unidad": str(ficha.get("unidad") or ""),
                "descripcion": str(ficha.get("descripcion") or ""),
            }
    return salida


@lru_cache(maxsize=1)
def _precios() -> dict[str, dict[str, tuple[float, str]]]:
    """{PAIS: {codigo_recurso: (precio_referencia, fecha_consulta)}}."""
    salida: dict[str, dict[str, tuple[float, str]]] = {}
    for ruta in sorted(_SALIDA.glob("precios_recursos_*.csv")):
        with ruta.open(encoding="utf-8-sig", newline="") as fh:
            for fila in csv.DictReader(fh, delimiter=";"):
                pais = str(fila.get("pais_codigo") or "").strip().upper()
                ref = str(fila.get("codigo_recurso") or "").strip()
                if not pais or not ref:
                    continue
                salida.setdefault(pais, {})[ref] = (
                    _numero(fila.get("precio_referencia")),
                    str(fila.get("fecha_consulta") or "").strip(),
                )
    return salida


@lru_cache(maxsize=1)
def _catalogo() -> tuple[dict, ...]:
    partidas = []
    for ruta in sorted((_DATOS / "descompuestos").glob("*.json")):
        d = json.loads(ruta.read_text(encoding="utf-8"))
        partidas.append(
            {
                "codigo": str(d.get("codigo") or ""),
                "capitulo": str(d.get("capitulo") or ""),
                "subcapitulo": str(d.get("subcapitulo") or ""),
                "apartado": str(d.get("apartado") or ""),
                "unidad": str(d.get("unidad") or ""),
                "titulo": str(d.get("titulo") or ""),
                "descripcion": str(d.get("descripcion") or ""),
                "margen": float(d.get("margen") or 0),
                "compl_pct": float(d.get("complementarios_pct") or 0),
                "lineas": tuple(
                    (str(r.get("ref") or ""), float(r.get("rendimiento") or 0))
                    for r in d.get("recursos", [])
                ),
            }
        )
    partidas.sort(key=lambda p: p["codigo"])
    return tuple(partidas)


@lru_cache(maxsize=1)
def _nombres_clasificacion() -> dict[tuple[str, ...], str]:
    arbol = json.loads((_DATOS / "clasificacion.json").read_text(encoding="utf-8"))
    salida: dict[tuple[str, ...], str] = {}
    for cap, ficha_cap in (arbol.get("capitulos") or {}).items():
        salida[(cap,)] = str(ficha_cap.get("nombre") or "")
        for sub, ficha_sub in (ficha_cap.get("subcapitulos") or {}).items():
            salida[(cap, sub)] = str(ficha_sub.get("nombre") or "")
            for apa, nombre in (ficha_sub.get("apartados") or {}).items():
                salida[(cap, sub, apa)] = str(nombre or "")
    return salida


def tema_precios(codigo_pais: str) -> str:
    """Segmento de URL según el idioma del mercado: prices / precios."""
    pais = PAISES.get(str(codigo_pais or "").strip().upper()) or {}
    return "prices" if pais.get("idioma") == "en" else "precios"


def ruta_indice(codigo_pais: str) -> str:
    from ..seo import ruta_mercado

    return ruta_mercado(codigo_pais, tema_precios(codigo_pais))


def ruta_apartado(codigo_pais: str, slug_apartado: str) -> str:
    from ..seo import ruta_mercado

    return ruta_mercado(
        codigo_pais, f"{tema_precios(codigo_pais)}/{slug_apartado}"
    )


def ruta_partida(codigo_pais: str, slug_apartado: str, slug_partida: str) -> str:
    from ..seo import ruta_mercado

    return ruta_mercado(
        codigo_pais, f"{tema_precios(codigo_pais)}/{slug_apartado}/{slug_partida}"
    )


def _titulo_limpio(texto: str) -> str:
    return str(texto or "").strip().rstrip(".").strip()


# Etiquetas de unidad en inglés para la presentación pública. La app
# muestra los códigos del catálogo tal cual («ud»), pero en un título
# público «per ud» delata el origen y «ml» en Reino Unido se lee
# mililitro. Solo presentación: el dato del catálogo no se toca.
_UNIDAD_EN = {"ud": "ea", "glb": "lot", "ml": "m"}


def _unidad_visible(unidad: str, imperial: bool, idioma: str) -> str:
    visible = unidad_mostrada(unidad, imperial)
    if idioma == "en":
        return _UNIDAD_EN.get(visible.strip().lower(), visible)
    return visible


def _partida_publicable(bruta: dict, cc: str, precios_pais: dict, recursos: dict):
    """Ficha pública de la partida en el país, o None si no pasa la guardia."""
    pais = PAISES[cc]
    idioma = str(pais.get("idioma") or "es")
    imperial = es_imperial_codigo(cc)
    unidad = bruta["unidad"]

    lineas = []
    grupos = {g: 0.0 for g in _GRUPOS}
    directo = 0.0
    horas_mo = 0.0
    fecha_max = ""
    for ref, rendimiento in bruta["lineas"]:
        recurso = recursos.get(ref)
        precio_fecha = precios_pais.get(ref)
        if recurso is None or precio_fecha is None or precio_fecha[0] <= 0:
            return None
        precio, fecha = precio_fecha
        importe = rendimiento * precio
        directo += importe
        grupos[recurso["grupo"]] += importe
        if recurso["grupo"] == "mano_obra":
            horas_mo += rendimiento
        if fecha > fecha_max:
            fecha_max = fecha
        nombre = traducir_recurso_por_codigo(recurso["descripcion"], ref, cc)
        if idioma == "en" and not _sin_restos_es(nombre):
            return None
        lineas.append(
            {
                "nombre": nombre,
                "grupo": recurso["grupo"],
                "unidad": unidad_mostrada(recurso["unidad"], imperial),
                "rendimiento": rendimiento_recurso_mostrado(
                    rendimiento, recurso["unidad"], unidad, imperial
                ),
                "precio": precio_mostrado(precio, recurso["unidad"], imperial),
                "importe": precio_mostrado(importe, unidad, imperial),
            }
        )
    if len(lineas) < _MIN_LINEAS:
        return None

    titulo = _titulo_limpio(traducir(bruta["titulo"], cc))
    descripcion = traducir(bruta["descripcion"], cc).strip()
    if idioma == "en":
        if titulo == _titulo_limpio(bruta["titulo"]) or descripcion == bruta["descripcion"].strip():
            return None
        if not _sin_restos_es(f"{titulo} {descripcion}"):
            return None
    if len(descripcion) < _MIN_DESCRIPCION:
        return None

    complementarios = directo * bruta["compl_pct"] / 100.0
    pu = (directo + complementarios) * (1 + bruta["margen"])
    horas_mostradas = rendimiento_mostrado(horas_mo, unidad, imperial) or 0.0
    uds_dia_cuadrilla = 0.0
    if horas_mo > 0:
        uds_dia_cuadrilla = cantidad_mostrada(16.0 / horas_mo, unidad, imperial)

    return {
        "codigo": bruta["codigo"],
        "titulo": titulo,
        "descripcion": descripcion,
        "unidad": _unidad_visible(unidad, imperial, idioma),
        "moneda": str(pais.get("moneda") or ""),
        "pu": precio_mostrado(pu, unidad, imperial),
        "directo": precio_mostrado(directo, unidad, imperial),
        "complementarios": precio_mostrado(complementarios, unidad, imperial),
        "compl_pct": bruta["compl_pct"],
        "grupos": {
            g: precio_mostrado(v, unidad, imperial) for g, v in grupos.items()
        },
        "lineas": lineas,
        "horas_mo": horas_mostradas,
        "uds_dia_cuadrilla": uds_dia_cuadrilla,
        "fecha_revision": fecha_max,
        "_clave_apartado": (bruta["capitulo"], bruta["subcapitulo"], bruta["apartado"]),
        "_capitulo": bruta["capitulo"],
    }


# Índices precalculados que viajan con el código, UN FICHERO POR PAÍS
# (``tools/generar_precios_publicos.py``). Construir un país en vivo
# cuesta hasta ~7 s —la capa de variante del inglés pasa por miles de
# cadenas— y en una instancia fría de Vercel la primera petición pagaba
# los cinco países sin llegar a calentar: las páginas salieron con 404
# por timeout el primer día. El JSON se lee en milisegundos; si falta
# o está dañado se calcula en vivo (red de seguridad, mismo patrón que
# ``cifras_catalogo.json``). La deriva la caza el test que compara el
# artefacto con el cálculo en vivo. Nació como un único JSON; al
# encender los 22 mercados con matriz habría rondado los 90 MB, así
# que cada país lleva el suyo (~4 MB): el proceso solo parsea los
# países que sirve y git solo versiona el país que cambia.
_DIR_PRECALCULADO = _DATOS / "precios_publicos"


@lru_cache(maxsize=32)
def _indice_desde_artefacto(cc: str) -> dict | None:
    try:
        bruto = json.loads(
            (_DIR_PRECALCULADO / f"{cc}.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None
    if not bruto:
        return None
    try:
        indice = dict(bruto)
        # JSON no admite claves tupla: viajan como "apartado|partida"
        # (los slugs solo llevan [a-z0-9-], el separador es seguro).
        indice["partidas"] = {
            tuple(clave.split("|", 1)): ficha
            for clave, ficha in (bruto.get("partidas") or {}).items()
        }
        indice["por_codigo"] = {
            codigo: tuple(destino)
            for codigo, destino in (bruto.get("por_codigo") or {}).items()
        }
    except (AttributeError, TypeError, ValueError):
        return None
    return indice if indice["partidas"] else None


def generar_artefacto() -> dict:
    """Serializa los índices calculados en vivo para el JSON precalculado."""
    paises = {}
    for cc in PAISES_PRECIOS_PUBLICOS:
        indice = _indice_en_vivo(cc)
        if indice is None:
            continue
        copia = dict(indice)
        copia["partidas"] = {
            f"{slug_ap}|{slug_p}": ficha
            for (slug_ap, slug_p), ficha in indice["partidas"].items()
        }
        copia["por_codigo"] = {
            codigo: list(destino)
            for codigo, destino in indice["por_codigo"].items()
        }
        paises[cc] = copia
    return {"paises": paises}


def _indice(cc: str) -> dict | None:
    cc = str(cc or "").strip().upper()
    if cc not in PAISES_PRECIOS_PUBLICOS or cc not in PAISES:
        return None
    return _indice_desde_artefacto(cc) or _indice_en_vivo(cc)


@lru_cache(maxsize=8)
def _indice_en_vivo(cc: str) -> dict | None:
    cc = str(cc or "").strip().upper()
    if cc not in PAISES_PRECIOS_PUBLICOS or cc not in PAISES:
        return None
    precios_pais = _precios().get(cc) or {}
    recursos = _recursos()
    nombres = _nombres_clasificacion()
    idioma = str(PAISES[cc].get("idioma") or "es")

    def nombre_destino(clave: tuple[str, ...]) -> str | None:
        original = nombres.get(clave) or ""
        if not original:
            return None
        destino = traducir(original, cc).strip()
        if idioma == "en" and (destino == original or not _sin_restos_es(destino)):
            return None
        return destino

    por_apartado: dict[tuple[str, ...], list[dict]] = {}
    for bruta in _catalogo():
        ficha = _partida_publicable(bruta, cc, precios_pais, recursos)
        if ficha is not None:
            por_apartado.setdefault(ficha["_clave_apartado"], []).append(ficha)

    apartados: dict[str, dict] = {}
    partidas: dict[tuple[str, str], dict] = {}
    por_codigo: dict[str, tuple[str, str]] = {}
    capitulos: dict[str, dict] = {}
    slugs_apartado: dict[str, tuple[str, ...]] = {}
    total = 0
    fecha_pais = ""

    for clave in sorted(por_apartado):
        fichas = por_apartado[clave]
        if len(fichas) < _MIN_PARTIDAS_APARTADO:
            continue
        nombre_apartado = nombre_destino(clave)
        nombre_capitulo = nombre_destino((clave[0],))
        if not nombre_apartado or not nombre_capitulo:
            continue
        slug_ap = _slug(nombre_apartado)
        if not slug_ap:
            continue
        if slug_ap in slugs_apartado and slugs_apartado[slug_ap] != clave:
            slug_ap = f"{slug_ap}-{''.join(clave)}"
        slugs_apartado[slug_ap] = clave

        slugs_partida: dict[str, str] = {}
        resumen_partidas = []
        for ficha in fichas:
            slug_p = _slug(ficha["titulo"])
            if not slug_p:
                continue
            if slug_p in slugs_partida and slugs_partida[slug_p] != ficha["codigo"]:
                slug_p = f"{slug_p}-{ficha['codigo'].replace('.', '')}"
            slugs_partida[slug_p] = ficha["codigo"]
            ficha = {k: v for k, v in ficha.items() if not k.startswith("_")}
            ficha["slug"] = slug_p
            ficha["slug_apartado"] = slug_ap
            partidas[(slug_ap, slug_p)] = ficha
            por_codigo[ficha["codigo"]] = (slug_ap, slug_p)
            resumen_partidas.append(
                {
                    "slug": slug_p,
                    "titulo": ficha["titulo"],
                    "pu": ficha["pu"],
                    "unidad": ficha["unidad"],
                    "moneda": ficha["moneda"],
                }
            )
            total += 1
            if ficha["fecha_revision"] > fecha_pais:
                fecha_pais = ficha["fecha_revision"]

        if not resumen_partidas:
            continue
        apartados[slug_ap] = {
            "slug": slug_ap,
            "clave": "-".join(clave),
            "nombre": nombre_apartado,
            "capitulo_codigo": clave[0],
            "capitulo": nombre_capitulo,
            "partidas": resumen_partidas,
        }
        capitulo = capitulos.setdefault(
            clave[0],
            {"codigo": clave[0], "nombre": nombre_capitulo, "apartados": []},
        )
        capitulo["apartados"].append(
            {
                "slug": slug_ap,
                "nombre": nombre_apartado,
                "n_partidas": len(resumen_partidas),
            }
        )

    if not partidas:
        return None
    return {
        "cc": cc,
        "apartados": apartados,
        "apartados_por_clave": {
            ficha["clave"]: slug for slug, ficha in apartados.items()
        },
        "partidas": partidas,
        "por_codigo": por_codigo,
        "capitulos": [capitulos[c] for c in sorted(capitulos)],
        "total_partidas": total,
        "total_apartados": len(apartados),
        "fecha_revision": fecha_pais,
    }


def paises_publicados() -> tuple[str, ...]:
    return tuple(cc for cc in PAISES_PRECIOS_PUBLICOS if _indice(cc) is not None)


def resumen(codigo_pais: str) -> dict | None:
    indice = _indice(codigo_pais)
    if indice is None:
        return None
    return {
        "cc": indice["cc"],
        "capitulos": indice["capitulos"],
        "total_partidas": indice["total_partidas"],
        "total_apartados": indice["total_apartados"],
        "fecha_revision": indice["fecha_revision"],
    }


def apartado(codigo_pais: str, slug: str) -> dict | None:
    indice = _indice(codigo_pais)
    if indice is None:
        return None
    return indice["apartados"].get(str(slug or ""))


def partida(codigo_pais: str, slug_apartado: str, slug: str) -> dict | None:
    indice = _indice(codigo_pais)
    if indice is None:
        return None
    ficha = indice["partidas"].get((str(slug_apartado or ""), str(slug or "")))
    if ficha is None:
        return None
    ficha = dict(ficha)
    ficha["apartado"] = indice["apartados"].get(ficha["slug_apartado"]) or {}
    ficha["hermanas"] = [
        p
        for p in (ficha["apartado"].get("partidas") or [])
        if p["slug"] != ficha["slug"]
    ]
    return ficha


def alternates(codigo_partida: str) -> list[dict]:
    """Rutas de la misma partida en los demás países publicados (hreflang)."""
    from ..seo import hreflang_pais

    salida = []
    for cc in paises_publicados():
        destino = (_indice(cc) or {}).get("por_codigo", {}).get(codigo_partida)
        if destino:
            salida.append(
                {
                    "hreflang": hreflang_pais(cc),
                    "cc": cc,
                    "path": ruta_partida(cc, destino[0], destino[1]),
                }
            )
    return salida


def alternates_apartado(clave: str) -> list[dict]:
    """Rutas del mismo apartado (clave cap-sub-apa) en países publicados."""
    from ..seo import hreflang_pais

    if not clave:
        return []
    salida = []
    for cc in paises_publicados():
        slug = (_indice(cc) or {}).get("apartados_por_clave", {}).get(clave)
        if slug:
            salida.append(
                {
                    "hreflang": hreflang_pais(cc),
                    "cc": cc,
                    "path": ruta_apartado(cc, slug),
                }
            )
    return salida


def urls_sitemap(codigo_pais: str, origen: str) -> list[dict]:
    """Entradas del sitemap del país con la forma de ``seo.urls_sitemap``."""
    indice = _indice(codigo_pais)
    if indice is None:
        return []
    cc = indice["cc"]
    lastmod_pais = indice["fecha_revision"] or "2026-10-19"

    def alts_de(paths: list[dict]) -> list[dict]:
        alts = [
            {"hreflang": a["hreflang"], "href": origen + a["path"]} for a in paths
        ]
        por_defecto = next(
            (a for a in paths if a["cc"] == "US"), paths[0] if paths else None
        )
        if por_defecto is not None:
            alts.append(
                {"hreflang": "x-default", "href": origen + por_defecto["path"]}
            )
        return alts

    from ..seo import hreflang_pais

    salida: list[dict] = [
        {
            "loc": origen + ruta_indice(cc),
            "lastmod": lastmod_pais,
            "changefreq": "monthly",
            "priority": "0.8",
            "alternates": alts_de(
                [
                    {
                        "hreflang": hreflang_pais(otro),
                        "cc": otro,
                        "path": ruta_indice(otro),
                    }
                    for otro in paises_publicados()
                ]
            ),
        }
    ]
    for slug_ap in sorted(indice["apartados"]):
        salida.append(
            {
                "loc": origen + ruta_apartado(cc, slug_ap),
                "lastmod": lastmod_pais,
                "changefreq": "monthly",
                "priority": "0.7",
                "alternates": alts_de(
                    alternates_apartado(indice["apartados"][slug_ap]["clave"])
                ),
            }
        )
    for (slug_ap, slug_p), ficha in sorted(indice["partidas"].items()):
        salida.append(
            {
                "loc": origen + ruta_partida(cc, slug_ap, slug_p),
                "lastmod": ficha["fecha_revision"] or lastmod_pais,
                "changefreq": "monthly",
                "priority": "0.6",
                "alternates": alts_de(alternates(ficha["codigo"])),
            }
        )
    return salida
