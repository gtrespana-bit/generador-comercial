"""Rutas de precios públicos del catálogo (Fase 5 — SEO programático).

Router propio montado en ÚLTIMO lugar en ``app.main`` a propósito: los
patrones ``/{cc}/precios/...`` capturarían también rutas de la app como
``/partidas/precios/anomalos`` si fueran antes que los routers de
dominio (pasó: lo cazó la suite). Montado el último, cualquier ruta
literal de la app gana siempre y estas solo reciben países de verdad.

El middleware reescribe ``/en-us/prices/...`` a ``/us/prices/...``
igual que con las guías de mercado; la validación sigue ese patrón
estricto: país sin publicar -> 404; prefijo o segmento en el idioma
equivocado -> 301 a la canónica. Qué partidas existen lo decide la
guardia de ``services.precios_publicos``; aquí solo se enruta.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from .common import TEMPLATES
from .publico import _xml_urlset

router = APIRouter()


def _mercado_precios(cc: str, request: Request, construir_ruta):
    """(codigo, respuesta) — respuesta None si la ruta ya es la canónica."""
    from ..paises import PAISES
    from ..services import precios_publicos as pp

    codigo = str(cc or "").strip().upper()
    if codigo not in PAISES or codigo not in pp.paises_publicados():
        # Raise y no Response: el manejador global sirve la 404 HTML con
        # enlaces, la misma que ve quien llega desde un enlace viejo.
        raise HTTPException(status_code=404)
    canonica = construir_ruta(codigo)
    original = str(getattr(request.state, "ruta_original", "") or request.url.path)
    if original.rstrip("/") != canonica.rstrip("/"):
        return codigo, RedirectResponse(canonica, status_code=301)
    return codigo, None


@router.get("/{cc}/prices", response_class=HTMLResponse, include_in_schema=False)
@router.get("/{cc}/precios", response_class=HTMLResponse, include_in_schema=False)
def precios_indice(cc: str, request: Request):
    """Índice de precios del país: /en-us/prices."""
    from ..seo_precios import contexto_indice
    from ..services import precios_publicos as pp

    codigo, respuesta = _mercado_precios(cc, request, pp.ruta_indice)
    if respuesta is not None:
        return respuesta
    ctx = contexto_indice(request, codigo)
    if ctx is None:
        raise HTTPException(status_code=404)
    return TEMPLATES.TemplateResponse(request, "pais_precios.html", ctx)


@router.get("/{cc}/prices/{apartado}", response_class=HTMLResponse, include_in_schema=False)
@router.get("/{cc}/precios/{apartado}", response_class=HTMLResponse, include_in_schema=False)
def precios_apartado(cc: str, apartado: str, request: Request):
    """Hub de apartado: /en-us/prices/{apartado}."""
    from ..seo_precios import contexto_apartado
    from ..services import precios_publicos as pp

    codigo, respuesta = _mercado_precios(
        cc, request, lambda c: pp.ruta_apartado(c, apartado)
    )
    if respuesta is not None:
        return respuesta
    ctx = contexto_apartado(request, codigo, apartado)
    if ctx is None:
        raise HTTPException(status_code=404)
    return TEMPLATES.TemplateResponse(request, "pais_precio_apartado.html", ctx)


@router.get("/{cc}/prices/{apartado}/{partida}", response_class=HTMLResponse, include_in_schema=False)
@router.get("/{cc}/precios/{apartado}/{partida}", response_class=HTMLResponse, include_in_schema=False)
def precios_partida(cc: str, apartado: str, partida: str, request: Request):
    """Partida con su descompuesto: /en-us/prices/{apartado}/{partida}."""
    from ..seo_precios import contexto_partida
    from ..services import precios_publicos as pp

    codigo, respuesta = _mercado_precios(
        cc, request, lambda c: pp.ruta_partida(c, apartado, partida)
    )
    if respuesta is not None:
        return respuesta
    ctx = contexto_partida(request, codigo, apartado, partida)
    if ctx is None:
        raise HTTPException(status_code=404)
    return TEMPLATES.TemplateResponse(request, "pais_precio_partida.html", ctx)


@router.get("/{cc}/labour-rates", response_class=HTMLResponse, include_in_schema=False)
@router.get("/{cc}/mano-de-obra", response_class=HTMLResponse, include_in_schema=False)
def precios_mano_obra(cc: str, request: Request):
    """Coste horario de los oficios del país: /mx/mano-de-obra."""
    from ..mano_obra import contexto_mano_obra, ruta_mano_obra

    codigo, respuesta = _mercado_precios(cc, request, ruta_mano_obra)
    if respuesta is not None:
        return respuesta
    ctx = contexto_mano_obra(request, codigo)
    if ctx is None:
        raise HTTPException(status_code=404)
    return TEMPLATES.TemplateResponse(request, "pais_mano_obra.html", ctx)


@router.get("/{cc}/prices.json", include_in_schema=False)
@router.get("/{cc}/precios.json", include_in_schema=False)
def precios_json(cc: str, request: Request):
    """Catálogo del país en JSON (descarga real para ``Dataset``).

    Estático por despliegue: el catálogo vive en el repositorio y solo cambia
    al publicarlo, así que se cachea un día en el CDN con revalidación
    larga. Es el ``distribution`` que Google Dataset Search necesita; sin una
    descarga real, el ``Dataset`` del HTML no cuenta.
    """
    import json as _json

    from ..services import precios_publicos as pp

    codigo = str(cc or "").strip().upper()
    if codigo not in pp.paises_publicados():
        raise HTTPException(status_code=404)
    datos = pp.exportar(codigo)
    if not datos:
        raise HTTPException(status_code=404)
    return Response(
        _json.dumps(datos, ensure_ascii=False, separators=(",", ":")),
        media_type="application/json; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=3600, s-maxage=86400, "
            "stale-while-revalidate=604800",
            "Content-Disposition": f'inline; filename="precios-{codigo.lower()}.json"',
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/sitemap-precios-{cc}.xml", include_in_schema=False)
def sitemap_precios(cc: str, request: Request):
    """Sitemap hijo con las páginas de precios de un país (Fase 5).

    Se anuncia desde robots.txt; el principal no cambia para no tocar
    lo que Search Console ya conoce.
    """
    from ..seo import origen_canonico
    from ..services import precios_publicos as pp

    entradas = pp.urls_sitemap(
        str(cc or "").strip().upper(), origen_canonico(request)
    )
    if not entradas:
        raise HTTPException(status_code=404)
    return Response(_xml_urlset(entradas), media_type="application/xml")
