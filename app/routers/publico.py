"""Rutas públicas: landing, legales, propuestas compartidas y descarga de archivos."""  # E4-001 — router por dominio

from fastapi import APIRouter, Form, Request

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


def _contexto_landing(request: Request, pais_forzado: str | None = None) -> dict:
    """Contexto de la landing. El subdirectorio (/co/) manda sobre la query."""
    from ..paises import PAIS_GENERICO, PAISES, lista_paises
    from ..seo import contexto_seo
    from ..services.landing_ejemplo import contexto_ejemplo

    if pais_forzado:
        codigo = str(pais_forzado).strip().upper()
        if codigo in PAISES:
            ctx = {
                "pais_actual": PAISES[codigo],
                "pais_codigo": codigo,
                "pais_generico": PAIS_GENERICO,
                "paises": lista_paises(),
                "ej": contexto_ejemplo(codigo),
            }
            ctx.update(contexto_seo(request, codigo=codigo))
            return ctx
    pais_actual, pais_codigo = _resolver_pais_landing(request)
    ctx = {
        "pais_actual": pais_actual,
        "pais_codigo": pais_codigo,
        "pais_generico": PAIS_GENERICO,
        "paises": lista_paises(),
        "ej": contexto_ejemplo(pais_codigo),
    }
    ctx.update(contexto_seo(request, codigo=pais_codigo))
    return ctx


def _landing_con_pais(request: Request, codigo: str):
    """Renderiza la landing para un subdirectorio /co/, /mx/ ... y fija cookie."""
    from ..paises import PAISES

    codigo = str(codigo).strip().upper()
    if codigo not in PAISES:
        return Response("Página no encontrada.", status_code=404)
    ctx = _contexto_landing(request, pais_forzado=codigo)
    # hreflang + canonical se inyectan en el template via ctx
    resp = TEMPLATES.TemplateResponse(request, "landing.html", ctx)
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
    from ..seo import TEMAS, contexto_pagina_estatica
    from ..seo_articulos import lista_articulos
    from ..seo_contenido import lista_guias

    ctx = contexto_pagina_estatica(request, "mapa-del-sitio")
    ctx["paises"] = lista_paises()
    ctx["guias"] = lista_guias()
    ctx["articulos"] = lista_articulos()
    ctx["temas_seo"] = TEMAS
    return TEMPLATES.TemplateResponse(request, "mapa_sitio.html", ctx)


@router.get("/guia/{slug}", response_class=HTMLResponse, include_in_schema=False)
def guia_publica(slug: str, request: Request):
    from ..seo import contexto_guia

    ctx = contexto_guia(request, slug)
    if ctx is None:
        return Response("Página no encontrada.", status_code=404)
    return TEMPLATES.TemplateResponse(request, "seo_guia.html", ctx)


@router.get("/como-funciona", response_class=HTMLResponse, include_in_schema=False)
def como_funciona(request: Request):
    """Guía pública de funciones: catálogo, editor, margen, PDF y cobro."""
    from ..paises import lista_paises
    from ..seo import contexto_pagina_estatica

    ctx = contexto_pagina_estatica(request, "como-funciona")
    ctx["paises"] = lista_paises()
    return TEMPLATES.TemplateResponse(request, "como_funciona.html", ctx)


def _redirige_a_slash(codigo: str):
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
    ficha = ficha_tema(codigo, tema)
    if ficha is None:
        return Response("Página no encontrada.", status_code=404)
    ctx = contexto_seo(request, codigo=codigo, tema=tema)
    ctx.update(
        {
            "pais_actual": PAISES.get(codigo),
            "pais_codigo": codigo,
            "pais_generico": PAIS_GENERICO,
            "paises": lista_paises(),
            "ej": contexto_ejemplo(codigo),
            "ficha": ficha,
            "guias": lista_guias(),
        }
    )
    resp = TEMPLATES.TemplateResponse(request, "seo_hub.html", ctx)
    if codigo:
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


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request):
    """Sitemap con landings de país, páginas de intención, hreflang y lastmod."""
    from ..seo import urls_sitemap

    entradas = urls_sitemap(request)
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
    return Response("\n".join(xml) + "\n", media_type="application/xml")


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
