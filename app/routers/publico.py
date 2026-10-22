"""Rutas públicas: landing, legales, propuestas compartidas y descarga de archivos."""  # E4-001 — router por dominio

from fastapi import APIRouter, Form, HTTPException, Request

from ..indexnow import CLAVE as _CLAVE_INDEXNOW
from ..indexnow import RUTA_CLAVE as _RUTA_CLAVE_INDEXNOW

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)

router = APIRouter()

@router.get("/archivos/{object_key:path}")
def descargar_archivo_privado(
    object_key: str,
    download: int = 0,
    db: Session = Depends(get_db),
):
    """Proxy privado: autoriza por membresía/tenant antes de leer el objeto."""
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    try:
        key = validate_tenant_object_key(object_key, organizacion_id)
    except StorageError:
        return Response(status_code=404)
    metadata = (
        db.query(ArchivoAlmacenado)
        .filter(ArchivoAlmacenado.object_key == key)
        .first()
    )
    if metadata is None or metadata.categoria == "manifiestos-importacion":
        return Response(status_code=404)
    backend = common.get_storage_backend()
    try:
        contenido = backend.read(key)
    except StorageError:
        return Response(status_code=404)
    nombre = Path(metadata.nombre_original or "archivo").name.replace('"', "")
    disposicion = "attachment" if download else "inline"
    headers = {
        "Cache-Control": "private, max-age=300",
        "Content-Disposition": f"{disposicion}; filename*=UTF-8''{quote(nombre, safe='')}",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "sandbox",
        "Cross-Origin-Resource-Policy": "same-origin",
    }
    return Response(
        contenido,
        media_type=metadata.content_type or "application/octet-stream",
        headers=headers,
    )


@router.get("/archivos-legado/{legacy_path:path}")
def descargar_archivo_legado_privado(
    legacy_path: str,
    download: int = 0,
    db: Session = Depends(get_db),
):
    """Compatibilidad web autorizada para referencias locales anteriores."""
    clean = str(legacy_path or "").strip().replace("\\", "/").lstrip("/")
    path = (UPLOADS_DIR / clean).resolve()
    try:
        invalido = (
            not clean
            or "//" in clean
            or ".." in clean.split("/")
            or UPLOADS_DIR.resolve() not in path.parents
            or not path.is_file()
            or path.stat().st_size > 12 * 1024 * 1024
        )
    except OSError:
        invalido = True
    if invalido:
        return Response(status_code=404)
    referencias = {f"uploads/{clean}", f"static/uploads/{clean}", clean}
    if not any(_archivo_referenciado(db, referencia) for referencia in referencias):
        return Response(status_code=404)
    try:
        contenido = path.read_bytes()
    except OSError:
        return Response(status_code=404)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    disposicion = "attachment" if download else "inline"
    return Response(
        contenido,
        media_type=mime,
        headers={
            "Cache-Control": "private, max-age=300",
            "Content-Disposition": f"{disposicion}; filename*=UTF-8''{quote(path.name, safe='')}",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
            "Cross-Origin-Resource-Policy": "same-origin",
        },
    )


# ---------------------------------------------------------------------------
# Páginas públicas: landing y legales (E1-018/019/020/056)
# ---------------------------------------------------------------------------
# No tocan datos de tenant ni sesión: solo renderizan contenido estático con
# la identidad del producto. Por eso no dependen de get_db y están declaradas
# como fronteras públicas en la auditoría de protección de rutas.

def _resolver_pais_landing(request: Request) -> tuple[dict | None, str]:
    """Resuelve el país SOLO desde ``?pais=``.

    La cookie no cambia el HTML de ``/``: una URL, un contenido (SEO).
    El país de la cookie sigue sirviendo para el registro y para ``/pago``.
    """
    from ..paises import PAISES

    raw_q = str(request.query_params.get("pais", "") or "").strip().upper()
    if raw_q and raw_q in PAISES:
        return PAISES[raw_q], raw_q
    return None, ""


def _web_publico():
    """Mejor esfuerzo: contenido gobernado desde /admin si la tabla existe.

    Nunca rompe una página si la base no está disponible o aún no se ha
    migrado. En PostgreSQL una sesión pública solo ve publicado/activo (RLS).
    """
    from ..database import SessionLocal
    from ..services.web_publica import contexto_web_publico

    try:
        with SessionLocal() as db:
            return contexto_web_publico(db)
    except Exception:
        return None


def _idioma_de(request: Request | None) -> str:
    """Idioma ya resuelto por el middleware (``request.state.lang``)."""
    try:
        return getattr(getattr(request, "state", None), "lang", "") or "es"
    except Exception:
        return "es"


def _indices_catalogos(idioma: str) -> list[dict]:
    """Índices de los catálogos de precios publicados (para la home genérica)."""
    from ..seo_precios import indices_catalogo

    try:
        return indices_catalogo("en" if idioma == "en" else "es")
    except Exception:
        return []


def _contexto_landing(request: Request, pais_forzado: str | None = None) -> dict:
    """Contexto de la landing. El subdirectorio (/co/) manda sobre la query."""
    from ..paises import (
        PAIS_GENERICO,
        PAISES,
        lista_paises,
        mercados_destacados,
        mercados_por_bloque,
    )
    from ..seo import contexto_seo
    from ..services.landing_ejemplo import contexto_ejemplo

    idioma = _idioma_de(request)
    # Qué mercados se pintan y en qué orden. La plantilla no puede decidirlo
    # con un ``paises[:6]``: el orden de validación deja fuera a los cinco
    # mercados de habla inglesa en todas las páginas. El mercado de la propia
    # página va primero entre los accesos directos.
    codigo_actual = str(pais_forzado or "").strip().upper() or _resolver_pais_landing(request)[1]
    destacados = mercados_destacados(idioma, codigo_actual)
    bloques_mercados = mercados_por_bloque(idioma)

    if pais_forzado:
        codigo = str(pais_forzado).strip().upper()
        if codigo in PAISES:
            ctx = {
                "pais_actual": PAISES[codigo],
                "pais_codigo": codigo,
                "pais_generico": PAIS_GENERICO,
                "paises": lista_paises(),
                "destacados": destacados,
                "mercados_bloques": bloques_mercados,
                "ej": contexto_ejemplo(codigo, idioma),
                # Sin Inter: el hero usa la fuente del sistema. JSON-LD al
                # final del body para no retrasar el descubrimiento del CSS.
                "seo_skip_fonts": True,
                "seo_defer_jsonld": True,
            }
            ctx.update(contexto_seo(request, codigo=codigo))
            if not ctx.get("catalogo_precios"):
                # Sin catálogo propio: al menos el índice de todos los
                # catálogos publicados, para no dejar la home sin puente.
                ctx["indices_catalogos"] = _indices_catalogos(idioma)
            web = _web_publico()
            if web:
                ctx["web"] = web
            return ctx
    pais_actual, pais_codigo = _resolver_pais_landing(request)
    ctx = {
        "pais_actual": pais_actual,
        "pais_codigo": pais_codigo,
        "pais_generico": PAIS_GENERICO,
        "paises": lista_paises(),
        "destacados": destacados,
        "mercados_bloques": bloques_mercados,
        "ej": contexto_ejemplo(pais_codigo, idioma),
        # Sin Inter: el hero usa la fuente del sistema. JSON-LD al
        # final del body para no retrasar el descubrimiento del CSS.
        "seo_skip_fonts": True,
        "seo_defer_jsonld": True,
    }
    ctx.update(contexto_seo(request, codigo=pais_codigo))
    if not ctx.get("catalogo_precios"):
        ctx["indices_catalogos"] = _indices_catalogos(idioma)
    web = _web_publico()
    if web:
        ctx["web"] = web
    return ctx


def _landing_con_pais(request: Request, codigo: str):
    """Renderiza la landing para un subdirectorio /co/, /us/ ... y fija cookie."""
    from ..paises import PAISES

    codigo = str(codigo).strip().upper()
    if codigo not in PAISES:
        raise HTTPException(status_code=404)
    # Un mercado de habla inglesa no tiene versión en español: /us/ a secas
    # dejaría la interfaz en español por la cookie. Se manda a la canónica
    # (/en-us/), salvo que ya venga de ahí, que es cuando se sirve.
    if PAISES[codigo].get("idioma") == "en":
        original = str(getattr(request.state, "ruta_original", "") or "")
        if not original.lower().startswith("/en"):
            from ..seo import ruta_mercado

            return RedirectResponse(ruta_mercado(codigo), status_code=301)
    # El copy, la canónica y el hreflang en inglés los resuelve contexto_seo()
    # a partir de request.state.lang (ver app/seo_en.py).
    ctx = _contexto_landing(request, pais_forzado=codigo)
    resp = TEMPLATES.TemplateResponse(request, "landing.html", ctx)
    # Solo si cambia el valor: un Set-Cookie innecesario en cada visita
    # impediría que el CDN sirviera la copia cacheada (Fase 1.2).
    if request.cookies.get("cotizat_pais") != codigo:
        resp.set_cookie(
            "cotizat_pais",
            codigo,
            max_age=365 * 24 * 3600,
            path="/",
            samesite="lax",
            httponly=False,
        )
    return resp


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home_publica(request: Request):
    """Página de inicio pública: la landing comercial es la puerta de entrada.

    Quien llega sin sesión ve qué ofrece el producto, por qué elegirlo y cómo
    empezar. El panel de trabajo vive en ``/inicio``, ya con sesión iniciada.

    Si llega con ?pais=XX válido, se redirige 301 al subdirectorio /xx/ (SEO)
    y fija la cookie. Así ?pais= queda como legacy pero el canónico es /co/.
    """
    raw_q = str(request.query_params.get("pais", "") or "").strip().upper()
    from ..paises import PAISES

    if raw_q and raw_q in PAISES:
        # 301 al subdirectorio canónico para SEO (mantiene query demo_* si viene)
        qs = str(request.url.query or "")
        # limpia pais de la query para no duplicar
        try:
            from urllib.parse import parse_qs, urlencode

            qdict = parse_qs(qs, keep_blank_values=True)
            qdict.pop("pais", None)
            resto = urlencode(qdict, doseq=True)
            dest = f"/{raw_q.lower()}/" + (f"?{resto}" if resto else "")
        except Exception:
            dest = f"/{raw_q.lower()}/"
        resp = RedirectResponse(dest, status_code=301)
        resp.set_cookie(
            "cotizat_pais",
            raw_q,
            max_age=365 * 24 * 3600,
            path="/",
            samesite="lax",
            httponly=False,
        )
        return resp
    # El copy, la canónica y el hreflang en inglés los resuelve contexto_seo()
    # a partir de request.state.lang (ver app/seo_en.py).
    ctx = _contexto_landing(request)
    return TEMPLATES.TemplateResponse(request, "landing.html", ctx)


@router.get("/conocer", include_in_schema=False)
def landing_publica(request: Request):
    """Alias histórico: 301 a la canónica para no duplicar la home."""
    raw_q = str(request.query_params.get("pais", "") or "").strip().upper()
    from ..paises import PAISES

    if raw_q and raw_q in PAISES:
        return RedirectResponse(f"/{raw_q.lower()}/", status_code=301)
    return RedirectResponse("/", status_code=301)


@router.get("/mapa-del-sitio", response_class=HTMLResponse, include_in_schema=False)
def mapa_del_sitio(request: Request):
    from ..paises import lista_paises
    from ..seo import TEMAS, contexto_pagina_estatica, ruta_guia
    from ..seo_articulos import lista_articulos
    from ..seo_contenido import lista_guias

    ctx = contexto_pagina_estatica(request, "mapa-del-sitio")
    ctx["paises"] = lista_paises()
    ctx["guias"] = lista_guias()
    ctx["articulos"] = [
        {**articulo, "ruta": ruta_guia(articulo["slug"], "es")}
        for articulo in lista_articulos()
    ]
    # Guías de los mercados anglófonos (GB + US/IE/AU/CA): el mapa es un
    # enlace interno más hacia los artículos long-tail; la plantilla en
    # inglés los pinta y la española los ignora.
    from ..seo_articulos_mercados_en import guias_de, ruta_articulo
    from ..seo_reino_unido import guias as _guias_uk

    mercado_en = [
        {"h1": a["h1"], "ruta": f"/en-gb/guia/{a['slug']}"} for a in _guias_uk()
    ]
    for codigo in ("US", "IE", "AU", "CA"):
        mercado_en.extend(
            {"h1": a["h1"], "ruta": ruta_articulo(codigo, a["slug"])}
            for a in guias_de(codigo)
        )
    ctx["guias_mercado_en"] = mercado_en
    # Catálogos públicos de precios (Fase 5): enlace interno de entrada a
    # /en-us/prices y sucesores desde la lista «Por país». Solo aparecen
    # los países encendidos en services.precios_publicos.
    from ..services import precios_publicos as _precios

    ctx["catalogos_precios"] = {
        codigo: _precios.ruta_indice(codigo)
        for codigo in _precios.paises_publicados()
    }
    ctx["temas_seo"] = TEMAS
    return TEMPLATES.TemplateResponse(request, "mapa_sitio.html", ctx)


@router.get("/novedades", response_class=HTMLResponse, include_in_schema=False)
def novedades_publicas(request: Request):
    """Changelog público: solo releases marcadas como publicadas (C5)."""
    from ..seo import contexto_pagina_estatica

    web = _web_publico() or {"contenido": {}, "avisos": [], "releases": []}
    ctx = {
        "web": web,
        "releases": web["releases"],
        "avisos_web": web["avisos"],
    }
    ctx.update(contexto_pagina_estatica(request, "novedades"))
    return TEMPLATES.TemplateResponse(request, "novedades.html", ctx)


@router.get("/guia/{slug}", response_class=HTMLResponse, include_in_schema=False)
def guia_publica(slug: str, request: Request):
    from ..paises import PAISES
    from ..seo import contexto_guia, ruta_guia
    from ..seo_contenido import ficha_guia

    # Migración de los artículos hispanos al silo del país. La URL histórica
    # conserva autoridad mediante 301, pero nunca devuelve una segunda copia.
    original = str(getattr(request.state, "ruta_original", "") or request.url.path)
    lang = _idioma_de(request)
    if lang == "es" and original.rstrip("/").startswith("/guia/"):
        ficha = ficha_guia(slug, lang="es")
        pais_codigo = str((ficha or {}).get("pais") or "").strip().upper()
        if pais_codigo and (PAISES.get(pais_codigo) or {}).get("idioma") == "es":
            return RedirectResponse(ruta_guia(slug, "es"), status_code=301)

    ctx = contexto_guia(request, slug)
    if ctx is None:
        return Response("Página no encontrada.", status_code=404)
    plantilla = "seo_guia_en.html" if lang == "en" else "seo_guia.html"
    return TEMPLATES.TemplateResponse(request, plantilla, ctx)


@router.get("/{cc}/guia/{slug}", response_class=HTMLResponse, include_in_schema=False)
def guia_de_mercado(cc: str, slug: str, request: Request):
    """Artículo canónico de mercado: /es/guia/x o /en-gb/guia/x.

    El middleware reescribe ``/en-gb/guia/x`` a ``/gb/guia/x`` antes de
    enrutar. Los mercados hispanos no necesitan reescritura, pero usan la
    misma validación estricta: un artículo de España bajo /mx/ devuelve 404.
    """
    from ..paises import PAISES
    from ..seo import ruta_guia
    from ..seo_contenido import ficha_guia

    codigo = str(cc or "").strip().upper()
    pais = PAISES.get(codigo)
    if not pais:
        return Response("Página no encontrada.", status_code=404)

    lang = str(pais.get("idioma") or "es")
    ficha = ficha_guia(slug, lang=lang)
    if ficha is None or str(ficha.get("pais") or "").strip().upper() != codigo:
        return Response("Página no encontrada.", status_code=404)

    original = str(getattr(request.state, "ruta_original", "") or request.url.path)
    canonica = ruta_guia(slug, lang)
    if lang == "en" and not original.lower().startswith(f"/en-{codigo.lower()}/"):
        return RedirectResponse(canonica, status_code=301)
    if lang == "es" and not original.lower().startswith(f"/{codigo.lower()}/"):
        return RedirectResponse(canonica, status_code=301)
    return guia_publica(slug, request)


@router.get("/como-funciona", response_class=HTMLResponse, include_in_schema=False)
def como_funciona(request: Request):
    """Guía pública de funciones: catálogo, editor, margen, PDF y cobro."""
    from ..paises import lista_paises
    from ..seo import contexto_pagina_estatica

    # Copy y canónica en inglés: los resuelve contexto_pagina_estatica().
    ctx = contexto_pagina_estatica(request, "como-funciona")
    ctx["paises"] = lista_paises()
    return TEMPLATES.TemplateResponse(request, "como_funciona.html", ctx)


def _redirige_a_slash(codigo: str):
    """301 a la canónica de un mercado, en un solo salto.

    Un mercado de habla inglesa no vive en ``/us/`` sino en ``/en-us/``.
    Redirigir primero a ``/us/`` y desde ahí a ``/en-us/`` encadenaba dos
    301 por visita: Search Console lo apunta como «página con redirección»,
    gasta rastreo y reparte la señal entre tres URLs. Se salta directo a la
    canónica (y de paso ``/en-us`` sin barra deja de responder 200).
    """
    from ..paises import PAISES
    from ..seo import ruta_mercado

    pais = PAISES.get(str(codigo or "").strip().upper()) or {}
    if pais.get("idioma") == "en":
        return RedirectResponse(ruta_mercado(codigo), status_code=301)
    return RedirectResponse(f"/{codigo.lower()}/", status_code=301)


# --- Subdirectorios por país: la canónica lleva barra final ---
@router.get("/ve", include_in_schema=False)
def landing_ve(request: Request):
    return _redirige_a_slash("VE")


@router.get("/ve/", response_class=HTMLResponse, include_in_schema=False)
def landing_ve_slash(request: Request):
    return _landing_con_pais(request, "VE")


@router.get("/co", include_in_schema=False)
def landing_co(request: Request):
    return _redirige_a_slash("CO")


@router.get("/co/", response_class=HTMLResponse, include_in_schema=False)
def landing_co_slash(request: Request):
    return _landing_con_pais(request, "CO")


@router.get("/mx", include_in_schema=False)
def landing_mx(request: Request):
    return _redirige_a_slash("MX")


@router.get("/mx/", response_class=HTMLResponse, include_in_schema=False)
def landing_mx_slash(request: Request):
    return _landing_con_pais(request, "MX")


@router.get("/ec", include_in_schema=False)
def landing_ec(request: Request):
    return _redirige_a_slash("EC")


@router.get("/ec/", response_class=HTMLResponse, include_in_schema=False)
def landing_ec_slash(request: Request):
    return _landing_con_pais(request, "EC")


@router.get("/pe", include_in_schema=False)
def landing_pe(request: Request):
    return _redirige_a_slash("PE")


@router.get("/pe/", response_class=HTMLResponse, include_in_schema=False)
def landing_pe_slash(request: Request):
    return _landing_con_pais(request, "PE")


@router.get("/es", include_in_schema=False)
def landing_es(request: Request):
    return _redirige_a_slash("ES")


@router.get("/es/", response_class=HTMLResponse, include_in_schema=False)
def landing_es_slash(request: Request):
    return _landing_con_pais(request, "ES")


# --- Bloque añadido al expandir a los 18 países (orden ORDEN_SELECTOR).
# Antes solo VE/CO/MX/EC/PE/ES tenían subdirectorio raíz canónico; los
# 12 mercados nuevos (CL, AR, DO, UY, PY, BO, PA, CR, GT, HN, SV, NI)
# caían en 404 al entrar por URL. Con este bucle todos los códigos válidos
# responden /XX/ con la misma plantilla de landing personalizada. Si mañana
# se añade un código a ORDEN_SELECTOR, queda cubierto automáticamente.
from ..paises import ORDEN_SELECTOR as _PAISES_CON_SUBDIRECTORIO  # noqa: E402


for _codigo in _PAISES_CON_SUBDIRECTORIO:
    _codigo = str(_codigo).lower()
    # Evitar duplicar los que ya están definidos arriba
    if _codigo in {"ve", "co", "mx", "ec", "pe", "es"}:
        continue
    _path = f"/{_codigo}"
    _path_slash = f"/{_codigo}/"

    def _make_handler(_c):
        def _handler(request: Request):
            return _redirige_a_slash(_c.upper())
        _handler.__name__ = f"landing_{_c}_redirect"
        return _handler

    def _make_slash_handler(_c):
        def _handler(request: Request):
            return _landing_con_pais(request, _c.upper())
        _handler.__name__ = f"landing_{_c}_slash"
        return _handler

    router.add_api_route(
        _path, _make_handler(_codigo),
        methods=["GET"], include_in_schema=False,
    )
    router.add_api_route(
        _path_slash, _make_slash_handler(_codigo),
        methods=["GET"], response_class=HTMLResponse, include_in_schema=False,
    )


def _pagina_intencion(request: Request, codigo: str, tema: str):
    from ..paises import ORDEN_SELECTOR, PAIS_GENERICO, PAISES, lista_paises
    from ..seo import TEMAS, contexto_seo, ficha_tema
    from ..seo_contenido import lista_guias
    from ..services.landing_ejemplo import contexto_ejemplo

    codigo = str(codigo or "").strip().upper()
    tema = str(tema or "").strip().lower()
    if tema not in TEMAS:
        return Response("Página no encontrada.", status_code=404)
    if codigo and codigo not in ORDEN_SELECTOR:
        return Response("Página no encontrada.", status_code=404)
    # El copy se pide en el idioma de la petición. Antes se pedía siempre en
    # español y la plantilla inglesa pintaba un H1 en inglés con un cuerpo y
    # un FAQ en español debajo: /en-gb/apu era media página en cada idioma.
    lang = _idioma_de(request)
    ficha = ficha_tema(codigo, tema, lang=lang)
    if ficha is None:
        return Response("Página no encontrada.", status_code=404)
    ctx = contexto_seo(request, codigo=codigo, tema=tema)
    ctx.update(
        {
            "pais_actual": PAISES.get(codigo),
            "pais_codigo": codigo,
            "pais_generico": PAIS_GENERICO,
            "paises": lista_paises(),
            "ej": contexto_ejemplo(codigo, _idioma_de(request)),
            "ficha": ficha,
            "guias": lista_guias(),
        }
    )
    resp = TEMPLATES.TemplateResponse(request, "seo_hub.html", ctx)
    # Solo si cambia el valor: un Set-Cookie innecesario en cada visita
    # impediría que el CDN sirviera la copia cacheada (Fase 1.2).
    if codigo and request.cookies.get("cotizat_pais") != codigo:
        resp.set_cookie(
            "cotizat_pais",
            codigo,
            max_age=365 * 24 * 3600,
            path="/",
            samesite="lax",
            httponly=False,
        )
    return resp


@router.get("/software-presupuestos", response_class=HTMLResponse, include_in_schema=False)
def hub_software(request: Request):
    return _pagina_intencion(request, "", "software-presupuestos")


@router.get("/apu", response_class=HTMLResponse, include_in_schema=False)
def hub_apu(request: Request):
    return _pagina_intencion(request, "", "apu")


@router.get("/remodelacion", response_class=HTMLResponse, include_in_schema=False)
def hub_remodelacion(request: Request):
    return _pagina_intencion(request, "", "remodelacion")


@router.get("/{cc}/software-presupuestos", response_class=HTMLResponse, include_in_schema=False)
def hub_software_pais(cc: str, request: Request):
    return _pagina_intencion(request, cc, "software-presupuestos")


@router.get("/{cc}/apu", response_class=HTMLResponse, include_in_schema=False)
def hub_apu_pais(cc: str, request: Request):
    return _pagina_intencion(request, cc, "apu")


@router.get("/{cc}/remodelacion", response_class=HTMLResponse, include_in_schema=False)
def hub_remodelacion_pais(cc: str, request: Request):
    return _pagina_intencion(request, cc, "remodelacion")


@router.get("/robots.txt", include_in_schema=False)
def robots(request: Request):
    from ..seo import robots_txt

    return Response(robots_txt(request), media_type="text/plain; charset=utf-8")


def _xml_urlset(entradas) -> str:
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for item in entradas:
        xml.append("  <url>")
        xml.append(f"    <loc>{item['loc']}</loc>")
        xml.append(f"    <lastmod>{item['lastmod']}</lastmod>")
        xml.append(f"    <changefreq>{item['changefreq']}</changefreq>")
        xml.append(f"    <priority>{item['priority']}</priority>")
        for alt in item.get("alternates") or []:
            xml.append(
                f'    <xhtml:link rel="alternate" hreflang="{alt["hreflang"]}" '
                f'href="{alt["href"]}"/>'
            )
        xml.append("  </url>")
    xml.append("</urlset>")
    return "\n".join(xml) + "\n"


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request):
    """Sitemap con landings de país, páginas de intención, hreflang y lastmod."""
    from ..seo import urls_sitemap

    return Response(_xml_urlset(urls_sitemap(request)), media_type="application/xml")


@router.get("/sitemap_index.xml", include_in_schema=False)
def sitemap_index(request: Request):
    """Índice de sitemaps: el principal y un hijo por país con precios.

    Con 23 sitemaps (el principal más 22 de precios) el índice es lo que se
    envía una sola vez a Search Console y Bing: cualquier país que se
    encienda mañana entra solo, sin reenviar nada ni tocar el alta. Además
    deja un único `Sitemap:` legible en robots.txt.
    """
    from ..seo import SITEMAP_LASTMOD, origen_canonico

    origen = origen_canonico(request)
    # (url, lastmod): la fecha de revisión de los precios de cada país, no
    # una constante. Un lastmod que no cambia cuando cambia el contenido
    # enseña a Google a ignorarlo, y entonces tampoco sirve el día que sí
    # hay novedades.
    hijos = [(f"{origen}/sitemap.xml", SITEMAP_LASTMOD)]
    try:
        from ..services import precios_publicos as pp

        for cc in pp.paises_publicados():
            resumen = pp.resumen(cc) or {}
            hijos.append(
                (
                    f"{origen}/sitemap-precios-{cc.lower()}.xml",
                    resumen.get("fecha_revision") or SITEMAP_LASTMOD,
                )
            )
    except Exception:
        pass
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for hijo, lastmod in hijos:
        xml.append("  <sitemap>")
        xml.append(f"    <loc>{hijo}</loc>")
        xml.append(f"    <lastmod>{lastmod}</lastmod>")
        xml.append("  </sitemap>")
    xml.append("</sitemapindex>")
    return Response("\n".join(xml) + "\n", media_type="application/xml")


@router.get(_RUTA_CLAVE_INDEXNOW, include_in_schema=False)
def clave_indexnow():
    """Verificación de propiedad para IndexNow (Bing/Yahoo).

    El fichero debe contener solo la clave: ni salto de línea ni adornos.
    """
    return Response(_CLAVE_INDEXNOW, media_type="text/plain; charset=utf-8")


_PAGINAS_LEGALES = {
    "terminos": "legal/terminos.html",
    "privacidad": "legal/privacidad.html",
    "soporte": "legal/soporte.html",
    "licencias": "legal/licencias.html",
    "preguntas": "legal/preguntas.html",
}


@router.get("/legal/{pagina}", response_class=HTMLResponse, include_in_schema=False)
def pagina_legal(pagina: str, request: Request):
    plantilla = _PAGINAS_LEGALES.get(pagina)
    if plantilla is None:
        return Response("Página no encontrada.", status_code=404)
    from ..legal import TERMINOS_VERSION, TERMINOS_VERSION_FECHA
    from ..paises import lista_paises
    from ..seo import contexto_pagina_estatica

    # Copy y canónica en inglés: los resuelve contexto_pagina_estatica().
    ctx = contexto_pagina_estatica(request, pagina)
    ctx.update(
        {
            "terminos_version": TERMINOS_VERSION,
            "terminos_version_fecha": TERMINOS_VERSION_FECHA,
            "paises": lista_paises(),
        }
    )
    return TEMPLATES.TemplateResponse(request, plantilla, ctx)


# ---------------------------------------------------------------------------
# Soporte: el formulario de contacto de clientes y visitantes
#
# El canal era el correo a secas: quien tenía un problema dentro de la
# aplicación salía a su cliente de correo y el mensaje dependía de que se
# acordara de copiar la dirección. Aquí hay una página con formulario, funciona
# con o sin sesión, y el mensaje queda guardado en el panel además de enviarse
# al buzón de soporte.
# ---------------------------------------------------------------------------


def _contexto_soporte(request: Request, **extra) -> dict:
    from ..models import TIPOS_SOPORTE
    from ..paises import lista_paises
    from ..seo import contexto_pagina_estatica
    from ..services.prueba_gratuita import dias_de_prueba, prueba_activada

    contexto = contexto_pagina_estatica(request, "contacto")
    # El formulario llega con la pantalla desde la que se escribió: el botón
    # flotante de la aplicación pasa ``?desde=/presupuestos`` para que el
    # titular sepa dónde estaba la persona sin preguntárselo.
    desde = str(
        request.query_params.get("desde") or request.query_params.get("pagina") or ""
    ).strip()[:500]
    if not desde.startswith("/") or desde.startswith("//"):
        desde = ""
    contexto.update(
        {
            "tipos_soporte": TIPOS_SOPORTE,
            "desde": desde,
            "enviado": request.query_params.get("enviado") == "1",
            "referencia": str(request.query_params.get("ref") or "")[:20],
            "error_soporte": str(request.query_params.get("error") or "")[:300],
            "paises": lista_paises(),
            "prueba_gratuita": prueba_activada(),
            "dias_prueba": dias_de_prueba(),
        }
    )
    contexto.update(extra)
    return contexto


def _soporte_con_sesion(request: Request) -> bool:
    """¿Quien pide ``/soporte`` está dentro de la aplicación?

    El enlace «Soporte» y el botón flotante viven en el panel, pero hasta
    ahora llevaban a la página pública, con su barra de marketing y su botón
    de «Acceder»: alguien con la sesión abierta creía que se la habían
    cerrado. Con sesión se sirve la misma página dentro del marco de la
    aplicación; sin sesión, la pública indexable de siempre. En SQLite
    (escritorio) no hay cuentas web: siempre es el panel.
    """
    from ..database import DATABASE_IS_SQLITE

    if DATABASE_IS_SQLITE:
        return True
    try:
        from ..auth import identity_for_request

        identity_for_request(request)
        return True
    except Exception:
        return False


@router.get("/soporte", response_class=HTMLResponse, include_in_schema=False)
def pagina_soporte(request: Request):
    """Página de soporte: el formulario del botón de ayuda.

    Tiene URL propia (se puede guardar en favoritos y enlazar desde un correo)
    y funciona con o sin sesión: quien todavía no es cliente también puede
    escribir. El mensaje se guarda en el panel y se avisa al buzón de soporte.
    Con la sesión abierta se pinta dentro de la aplicación (misma URL y mismo
    formulario); sin sesión, la página pública indexable.
    """
    ctx = _contexto_soporte(request)
    if _soporte_con_sesion(request):
        identidad = getattr(request.state, "supabase_identity", None)
        if identidad is not None:
            # Nombre y correo ya sabidos: que no tenga que teclearlos otra vez.
            ctx.setdefault("nombre_previo", getattr(identidad, "name", "") or "")
            ctx.setdefault("email_previo", getattr(identidad, "email", "") or "")
        return TEMPLATES.TemplateResponse(request, "soporte_panel.html", ctx)
    return TEMPLATES.TemplateResponse(request, "soporte.html", ctx)


@router.post("/soporte", response_class=RedirectResponse, include_in_schema=False)
async def enviar_soporte(request: Request):
    """Recibe el mensaje: lo guarda en el panel y avisa al buzón de soporte.

    Sin autenticación (lo usa también quien no tiene cuenta). El aviso por
    correo se intenta primero y el mensaje se guarda en un único INSERT con
    la marca ya puesta: la RLS de la tabla no admite UPDATE ni RETURNING en
    la sesión pública (detalle y garantías en ``app/services/soporte.py``).
    El ``reply_to`` del aviso es el del remitente, así que responder desde
    el buzón contesta directamente.
    """
    from urllib.parse import urlencode

    from ..services.avisos_negocio import url_panel_absoluta
    from ..services.email import EmailNotConfigured, EmailSendError, EmailValidationError
    from ..services.prueba_gratuita import hash_ip
    from ..services.soporte import SoporteError, registrar_mensaje

    form = await request.form()
    nombre = str(form.get("nombre") or "").strip()[:200]
    email = str(form.get("email") or "").strip().lower()[:254]
    tipo = str(form.get("tipo") or "consulta").strip().lower()[:20]
    asunto = str(form.get("asunto") or "").strip()[:200]
    mensaje = str(form.get("mensaje") or "").strip()
    desde = str(form.get("desde") or "").strip()[:500]
    cebo = str(form.get("web") or "").strip()

    def _volver(**parametros) -> RedirectResponse:
        consulta = urlencode({k: v for k, v in parametros.items() if v})
        return RedirectResponse(f"/soporte?{consulta}" if consulta else "/soporte", status_code=303)

    # Trampa para bots: un campo oculto que nadie rellena. Se responde como si
    # se hubiera enviado (para no dar pistas) y no se guarda nada.
    if cebo:
        return _volver(enviado="1")

    if not desde or not desde.startswith("/") or desde.startswith("//"):
        desde = "/soporte"

    # Si quien escribe tiene la sesión abierta, el mensaje llega con su
    # empresa puesta: el titular ve de qué cliente es sin preguntarlo. Sin
    # sesión (una visita desde la web) el mensaje se guarda igual.
    organizacion_id = 0
    try:
        organizacion_id = int(request.cookies.get("cotizat_organization_id") or 0)
    except (TypeError, ValueError):
        organizacion_id = 0

    try:
        from ..database import SessionLocal

        with SessionLocal() as db:
            fila, _aviso = registrar_mensaje(
                db,
                nombre=nombre,
                email=email,
                tipo=tipo,
                mensaje=mensaje,
                asunto=asunto,
                pagina=desde,
                organizacion_id=organizacion_id or None,
                ip_hash=hash_ip(ip_de_request(request)),
                panel_url=url_panel_absoluta("/admin/clientes?tab=soporte"),
            )
            db.commit()
            numero = fila.id
    except SoporteError as exc:
        return _volver(error=str(exc))
    except (EmailNotConfigured, EmailValidationError, EmailSendError):
        # El mensaje ya está guardado; el correo es el aviso, no la verdad.
        numero = 0
    except Exception:
        logger = logging.getLogger("cotizat.publico")
        logger.exception("Error guardando un mensaje de soporte.")
        return _volver(
            error="No hemos podido registrar tu mensaje. Inténtalo de nuevo en un minuto."
        )

    return _volver(enviado="1", ref=str(numero) if numero else "")


# ---------------------------------------------------------------------------
# Página de planes y métodos de pago
# ---------------------------------------------------------------------------

def _pais_pago_publico(request: Request) -> str:
    """País para la página pública de cobro: selector o preferencia guardada.

    Esta ruta no debe abrir una sesión de organización: tiene que seguir
    disponible para renovar aun cuando la licencia esté suspendida.
    """
    from ..paises import PAISES

    elegido = str(request.query_params.get("pais") or "").strip().upper()
    if elegido in PAISES:
        return elegido

    preferido = str(request.cookies.get("cotizat_pais") or "").strip().upper()
    return preferido if preferido in PAISES else "VE"


@router.get("/pago", response_class=HTMLResponse, include_in_schema=False)
def pagina_pago(request: Request):
    """Página pública de planes y métodos de pago.

    Acepta un `msg` en la query para poder explicar cómo se ha llegado aquí:
    quien acaba de crear una organización sin prueba disponible aterriza en
    esta pantalla y merece saber por qué, en vez de encontrarse una lista de
    precios sin contexto.
    """
    from ..paises import PAISES, lista_paises
    from ..seo import contexto_pagina_estatica

    codigo_pais = _pais_pago_publico(request)
    ctx = contexto_pagina_estatica(request, "pago")
    ctx.update(
        {
            "msg": request.query_params.get("msg", "")[:300],
            "pais_pago": PAISES[codigo_pais],
            "paises_pago": lista_paises(),
            "paises": lista_paises(),
        }
    )
    return TEMPLATES.TemplateResponse(request, "pago.html", ctx)


# ---------------------------------------------------------------------------
# Solicitud de demostración (formulario público)
# ---------------------------------------------------------------------------

@router.post("/demo", response_class=RedirectResponse, include_in_schema=False)
async def solicitar_demo(
    request: Request,
    nombre: str = Form(""),
    email: str = Form(""),
    empresa: str = Form(""),
    telefono: str = Form(""),
    presupuestos_mes: str = Form(""),
    mensaje: str = Form(""),
):
    """Recibe la solicitud de demo desde la landing y notifica al equipo.

    Sin autenticación: es un formulario público. Se envía un correo a
    soporte vía Resend con los datos. Si el correo no está configurado,
    la solicitud se pierde silenciosamente (el mailto: sigue como respaldo
    en la plantilla).
    """
    from ..services.email import (
        EmailNotConfigured,
        EmailValidationError,
        enviar_solicitud_demo_por_email,
    )

    nombre = str(nombre or "").strip()
    email = str(email or "").strip().lower()
    empresa = str(empresa or "").strip()
    telefono = str(telefono or "").strip()
    presupuestos_mes = str(presupuestos_mes or "").strip()
    mensaje = str(mensaje or "").strip()

    error = ""
    if not nombre:
        error = "Escribe tu nombre."
    elif not email:
        error = "Escribe tu correo electrónico."
    elif not empresa:
        error = "Escribe el nombre de tu empresa."

    if not error:
        try:
            enviar_solicitud_demo_por_email(
                nombre=nombre,
                email=email,
                empresa=empresa,
                telefono=telefono,
                presupuestos_mes=presupuestos_mes,
                mensaje=mensaje,
                lang=getattr(getattr(request, "state", None), "lang", "es") or "es",
            )
        except (EmailNotConfigured, EmailValidationError) as exc:
            error = str(exc)
        except Exception:
            logger = logging.getLogger("cotizat.publico")
            logger.exception("Error al enviar solicitud de demo.")
            error = "Ocurrió un error al enviar tu solicitud. Intenta de nuevo o escríbenos directamente."

    if error:
        return RedirectResponse(
            f"/?demo_error={quote(error)}#demo",
            status_code=303,
        )

    return RedirectResponse(
        f"/?demo_enviado={quote(nombre)}#demo",
        status_code=303,
    )


@router.get("/us", include_in_schema=False)
def landing_us(request: Request):
    return _redirige_a_slash("US")


@router.get("/us/", response_class=HTMLResponse, include_in_schema=False)
def landing_us_slash(request: Request):
    return _landing_con_pais(request, "US")


@router.get("/gb", include_in_schema=False)
def landing_gb(request: Request):
    return _redirige_a_slash("GB")


@router.get("/gb/", response_class=HTMLResponse, include_in_schema=False)
def landing_gb_slash(request: Request):
    return _landing_con_pais(request, "GB")


@router.get("/au", include_in_schema=False)
def landing_au(request: Request):
    return _redirige_a_slash("AU")


@router.get("/au/", response_class=HTMLResponse, include_in_schema=False)
def landing_au_slash(request: Request):
    return _landing_con_pais(request, "AU")


@router.get("/ca", include_in_schema=False)
def landing_ca(request: Request):
    return _redirige_a_slash("CA")


@router.get("/ca/", response_class=HTMLResponse, include_in_schema=False)
def landing_ca_slash(request: Request):
    return _landing_con_pais(request, "CA")


@router.get("/ie", include_in_schema=False)
def landing_ie(request: Request):
    return _redirige_a_slash("IE")


@router.get("/ie/", response_class=HTMLResponse, include_in_schema=False)
def landing_ie_slash(request: Request):
    return _landing_con_pais(request, "IE")


# --- Piloto en inglés (locale en) ---
@router.get("/en", include_in_schema=False)
def landing_en(request: Request):
    return RedirectResponse("/en/", status_code=301)


@router.get("/en/", response_class=HTMLResponse, include_in_schema=False)
def landing_en_slash(request: Request):
    # «en» a secas resuelve a Estados Unidos en el registro de mercados, así
    # que /en/ y /en-us/ serían la misma página en dos sitios. Se consolida
    # en la del mercado con un 301 para no repartir la autoridad entre las
    # dos ni dejar una URL ambigua compitiendo con las de cada país.
    return RedirectResponse("/en-us/", status_code=301)


# --- Conmutador de idioma -------------------------------------------------
@router.get("/idioma/{idioma}", include_in_schema=False)
def cambiar_idioma(idioma: str, destino: str = "/"):
    """Fija el idioma y devuelve al visitante a la misma página.

    El conmutador no puede limitarse a enlazar ``/en/...``: al volver al
    español (que no lleva prefijo) la cookie seguiría en ``en`` y la interfaz
    no cambiaría. La redirección pasa por aquí para escribir la cookie en los
    dos sentidos y conservar país y query de la página de partida.
    """
    from ..i18n import (
        COOKIE_IDIOMA,
        COOKIE_IDIOMA_MAX_AGE,
        normalizar_idioma,
        ruta_en_idioma,
        ruta_segura,
    )
    from urllib.parse import urlsplit

    lang = normalizar_idioma(idioma)
    # Se sanea el destino tal cual llega: partirlo antes permitiría colar un
    # dominio ajeno (``//malo.com/x`` tiene path ``/x``) y convertir el
    # conmutador en un open redirect.
    ruta = ruta_en_idioma(ruta_segura(destino), lang)
    query = urlsplit(str(destino or "/")).query
    url = ruta + (f"?{query}" if query else "")

    resp = RedirectResponse(url, status_code=307)
    resp.set_cookie(
        COOKIE_IDIOMA,
        lang,
        max_age=COOKIE_IDIOMA_MAX_AGE,
        path="/",
        samesite="lax",
        httponly=False,
    )
    # Utilidad de navegación: no es contenido y no debe competir con la página
    # a la que lleva.
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp
