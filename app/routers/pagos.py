"""Compra de planes con pago manual: el cliente elige método, declara la
verificación y adjunta su comprobante (E1-059 cobro manual)."""

from __future__ import annotations

import io
import json
import logging
from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Form, Request

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..services import auditoria
from ..datos_pago import (
    PLANES,
    PLAN_PENDIENTE_COOKIE,
    es_metodo_online,
    metodo_info,
    metodos_para_pais,
    plan_info,
)

router = APIRouter()

log = logging.getLogger("cotizat.pagos")

_EXT_IMG = {".png", ".jpg", ".jpeg", ".webp"}
_MAX_COMPROBANTE = 12 * 1024 * 1024


def _plan_o_redirect(request: Request, plan: str):
    """Devuelve (ficha|None) y redirige a /pago si el plan no existe."""
    try:
        return plan_info(plan)
    except KeyError:
        return None


def codigo_pais_compra(db, request: Request) -> str:
    """Resuelve el país del comprador para elegir los métodos de pago.

    Prioridad: el país configurado en la organización (``empresa_pais``), que
    es lo que de verdad describe al cliente con sesión iniciada; si no hay,
    la cookie ``cotizat_pais`` que dejó la landing. Devuelve ``""`` cuando no
    se puede resolver, y entonces el checkout cae en el genérico.
    """
    from ..paises import PAISES
    from ..services.traduccion import codigo_desde_pais

    cfg = db.query(Configuracion).first()
    if cfg is not None:
        codigo = codigo_desde_pais(getattr(cfg, "empresa_pais", "") or "")
        if codigo in PAISES:
            return codigo
    cookie = str(request.cookies.get("cotizat_pais", "") or "").strip().upper()
    return cookie if cookie in PAISES else ""


def _cookie_secure() -> bool:
    """Flag `Secure` de las cookies, coherente con el resto de la app."""
    try:
        return SupabaseAuthSettings.from_environment().cookie_secure
    except AuthNotConfigured:
        return True


def _set_plan_pendiente_cookie(response, plan: str) -> None:
    """Recuerda el plan elegido para retomarlo tras el alta de la cuenta."""
    response.set_cookie(
        PLAN_PENDIENTE_COOKIE,
        plan,
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def _clear_plan_pendiente_cookie(response) -> None:
    """Elimina la intención de compra (compra completada o descartada)."""
    response.delete_cookie(
        PLAN_PENDIENTE_COOKIE,
        path="/",
        secure=_cookie_secure(),
        httponly=True,
        samesite="lax",
    )


@router.get("/pago/elegir", include_in_schema=False)
def elegir_plan(request: Request, plan: str = ""):
    """Recuerda el plan elegido y lleva al checkout.

    El checkout exige sesión y organización; esta ruta guarda la intención en
    una cookie ANTES de eso, de modo que sobreviva al registro, la confirmación
    de email y el alta de empresa, y pueda retomarse desde el panel.
    """
    if _plan_o_redirect(request, plan) is None:
        return RedirectResponse("/pago", status_code=303)
    response = RedirectResponse(f"/pago/comprar?plan={quote(plan)}", status_code=303)
    _set_plan_pendiente_cookie(response, plan)
    return response


@router.post("/pago/descartar", include_in_schema=False)
def descartar_plan_pendiente():
    """Descarta la intención de compra recordada en la cookie."""
    response = RedirectResponse("/inicio", status_code=303)
    _clear_plan_pendiente_cookie(response)
    return response


@router.get("/pago/comprar", response_class=HTMLResponse, include_in_schema=False)
def comprar_plan(
    request: Request, plan: str = "", db: Session = Depends(get_db_renovacion)
):
    """Página de compra: resumen del plan + métodos de pago + formulario."""
    ficha = _plan_o_redirect(request, plan)
    if ficha is None:
        return RedirectResponse("/pago", status_code=303)

    organizacion = db.get(Organizacion, int(db.info.get("organizacion_id") or 0))
    usuario = db.get(Usuario, int(db.info.get("usuario_id") or 0))
    codigo = codigo_pais_compra(db, request)
    metodos = metodos_para_pais(codigo or None)
    from ..services.stripe_pagos import stripe_configurado

    stripe_disponible = stripe_configurado() and "stripe" in metodos
    if not stripe_disponible:
        # Sin claves de Stripe no se ofrece la tarjeta: el checkout degrada a
        # los canales manuales (o al respaldo cripto) en vez de un botón roto.
        metodos = {
            clave: ficha
            for clave, ficha in metodos.items()
            if not ficha.get("online")
        }

    return TEMPLATES.TemplateResponse(
        request,
        "pago/comprar.html",
        {
            "plan": plan,
            "plan_ficha": ficha,
            "metodos": metodos,
            "metodos_json": json.dumps(metodos, ensure_ascii=False),
            "pais_codigo": codigo,
            "stripe_disponible": stripe_disponible,
            "organizacion_nombre": organizacion.nombre if organizacion else "",
            "usuario_email": usuario.email if usuario else "",
            "hoy": date.today().isoformat(),
            "error": request.query_params.get("error", ""),
        },
    )


def _validar_comprobante(nombre: str, datos: bytes) -> str:
    """Valida imagen o PDF y devuelve el MIME; vacío si no es válido."""
    nombre = str(nombre or "").strip()
    if not nombre:
        return ""
    ext = Path(nombre).suffix.lower()
    if not datos or len(datos) > _MAX_COMPROBANTE:
        return ""
    if ext in _EXT_IMG:
        try:
            from PIL import Image as PILImage

            with PILImage.open(io.BytesIO(datos)) as imagen:
                formato = str(imagen.format or "").upper()
                ancho, alto = imagen.size
                if ancho <= 0 or alto <= 0 or ancho * alto > 40_000_000:
                    return ""
                imagen.verify()
        except Exception:
            return ""
        return {
            "PNG": "image/png",
            "JPEG": "image/jpeg",
            "WEBP": "image/webp",
        }.get(formato, "")
    if ext == ".pdf" and datos.startswith(b"%PDF-"):
        return "application/pdf"
    return ""


@router.post("/pago/comprar", include_in_schema=False)
async def registrar_compra(
    request: Request,
    plan: str = Form(""),
    metodo_pago: str = Form(""),
    db: Session = Depends(get_db_renovacion),
):
    """Registra la compra: guarda comprobante, crea la compra y notifica."""
    from ..services.compras import GestionCompraError, crear_compra
    from ..services.email import (
        EmailNotConfigured,
        EmailValidationError,
        enviar_compra_por_email,
    )
    from ..utils import fmt_monto

    form = await request.form()
    ficha = _plan_o_redirect(request, plan)
    if ficha is None:
        return RedirectResponse("/pago", status_code=303)
    try:
        ficha_metodo = metodo_info(metodo_pago)
    except KeyError:
        ficha_metodo = None
    if ficha_metodo is None:
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error=Selecciona un método de pago.",
            status_code=303,
        )
    if es_metodo_online(metodo_pago):
        # Los métodos en línea (Stripe) no pasan por este formulario de
        # comprobante: su cobro se inicia en /pago/stripe/crear-sesion y se
        # confirma por webhook.
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error="
            "Ese método se paga con tarjeta. Usa el botón «Pagar con tarjeta».",
            status_code=303,
        )

    # Datos de verificación: solo los campos declarados para el método.
    verificacion = {}
    for campo, _etiqueta, _tipo, _placeholder in ficha_metodo["verificacion"]:
        valor = str(form.get(campo) or "").strip()
        if valor:
            verificacion[campo] = valor[:300]

    # Comprobante. Cada método publica su propio campo de archivo con nombre
    # único (``comprobante_<clave>``), así que se lee solo el del método
    # elegido. Antes, los cuatro paneles compartían ``name="comprobante"`` y el
    # navegador enviaba una parte por cada método (tres vacías); el enlace del
    # ``UploadFile`` resultaba ambiguo y, salvo con el último método, el
    # servidor recibía el archivo vacío y rechazaba la compra con
    # «Adjunta el comprobante de pago para continuar» aunque se hubiera subido.
    datos_comprobante = b""
    nombre_comprobante = ""
    mime_comprobante = ""
    parte = form.get(f"comprobante_{metodo_pago}")
    # ``request.form()`` devuelve un UploadFile cuando el campo trae archivo y
    # una cadena vacía cuando no se seleccionó nada.
    if parte is not None and not isinstance(parte, str):
        nombre_comprobante = Path(parte.filename or "").name[:255]
        datos_comprobante = await parte.read()
        mime_comprobante = _validar_comprobante(nombre_comprobante, datos_comprobante)
        if not mime_comprobante:
            return RedirectResponse(
                f"/pago/comprar?plan={quote(plan)}&error="
                "El comprobante debe ser una imagen (PNG, JPG, WEBP) o un PDF "
                "de hasta 12 MB.",
                status_code=303,
            )

    referencia_comprobante = ""
    if datos_comprobante:
        try:
            guardado = save_object(
                db,
                datos_comprobante,
                "comprobantes",
                nombre_comprobante,
                mime_comprobante,
            )
            referencia_comprobante = guardado.reference
        except StorageError:
            return RedirectResponse(
                f"/pago/comprar?plan={quote(plan)}&error="
                "No se pudo guardar el comprobante. Inténtalo de nuevo.",
                status_code=303,
            )

    organizacion_id = int(db.info.get("organizacion_id") or 0)
    usuario = db.get(Usuario, int(db.info.get("usuario_id") or 0))
    organizacion = db.get(Organizacion, organizacion_id)

    try:
        compra = crear_compra(
            db,
            organizacion_id=organizacion_id,
            plan=plan,
            metodo_pago=metodo_pago,
            datos_verificacion=verificacion,
            comprobante_reference=referencia_comprobante,
            comprobante_nombre=nombre_comprobante,
            comprobante_mime=mime_comprobante,
            creada_por_usuario_id=usuario.id if usuario else None,
            creada_por_email=usuario.email if usuario else "",
        )
        db.commit()
    except GestionCompraError as exc:
        db.rollback()
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error={quote(str(exc))}",
            status_code=303,
        )
    auditoria.registrar_evento(
        db,
        "plan.compra_registrada",
        entidad="compra",
        entidad_id=compra.id,
        detalle={"plan": plan, "metodo": metodo_pago},
    )

    # Notificación por email (no bloqueante): la compra ya está registrada.
    try:
        enviar_compra_por_email(
            nombre=usuario.nombre if usuario else "",
            email=usuario.email if usuario else "",
            organizacion_nombre=organizacion.nombre if organizacion else "",
            plan_nombre=ficha["nombre"],
            importe_texto=fmt_monto(ficha["importe"]),
            metodo_nombre=ficha_metodo["nombre"],
            verificacion=verificacion,
            comprobante_nombre=nombre_comprobante,
            comprobante_bytes=datos_comprobante,
        )
    except (EmailNotConfigured, EmailValidationError, StorageError) as exc:
        log.warning("Compra #%s creada sin notificación (%s).", compra.id, exc)

    respuesta = RedirectResponse(f"/pago/confirmacion?id={compra.id}", status_code=303)
    _clear_plan_pendiente_cookie(respuesta)
    return respuesta


@router.get("/pago/confirmacion", response_class=HTMLResponse, include_in_schema=False)
def confirmacion_compra(
    request: Request, id: int = 0, db: Session = Depends(get_db_renovacion)
):
    """Página de éxito: la compra quedó registrada y pendiente de verificación."""
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    compra = db.query(CompraPlan).filter(
        CompraPlan.id == id, CompraPlan.organizacion_id == organizacion_id
    ).first()
    if compra is None:
        return RedirectResponse("/pago", status_code=303)
    try:
        plan_ficha = plan_info(compra.plan)
        metodo_ficha = metodo_info(compra.metodo_pago)
    except KeyError:
        return RedirectResponse("/pago", status_code=303)

    return TEMPLATES.TemplateResponse(
        request,
        "pago/confirmacion.html",
        {
            "compra": compra,
            "plan_nombre": plan_ficha["nombre"],
            "metodo_nombre": metodo_ficha["nombre"],
            "importe_texto": fmt_monto(compra.importe),
            "verificacion": compra.datos_verificacion_dict(),
        },
    )


@router.get("/pago/recibo/{compra_id}.pdf", include_in_schema=False)
def recibo_compra_web(
    compra_id: int, request: Request, db: Session = Depends(get_db_renovacion)
):
    """Recibo de una compra activada, descargable por el propio cliente.

    Es el gemelo de `/admin/licencias/{id}/recibo.pdf`, con la misma
    numeración (`CT-000013`) y el mismo PDF, pero armado desde `compras_plan`
    en vez de `licencias`: esta última está cerrada por RLS al operador, así
    que una ruta de cliente nunca puede leerla. El período concedido se copia
    a la compra al activarla justo para esto.

    El filtro por `organizacion_id` es lo que impide leer el recibo de otro:
    una compra ajena simplemente no existe para esta sesión.
    """
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    compra = (
        db.query(CompraPlan)
        .filter(
            CompraPlan.id == compra_id,
            CompraPlan.organizacion_id == organizacion_id,
        )
        .first()
    )
    if compra is None:
        return _redirect("/configuracion", error="Esa compra no existe.")

    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        return _redirect("/configuracion", error="Esa compra no existe.")

    try:
        licencia = licencia_de_compra(compra)
        buffer = generar_recibo_licencia_pdf(licencia, organizacion)
    except GestionLicenciaError as exc:
        return _redirect("/configuracion", error=str(exc))
    except Exception:
        log.error(
            "Error generando el recibo de la compra #%s:\n%s",
            compra_id,
            traceback.format_exc(),
        )
        return _redirect(
            "/configuracion",
            error="No se pudo generar el recibo. Escríbenos y te lo enviamos.",
        )

    respuesta = _respuesta_pdf(
        buffer, f"recibo-{numero_recibo(licencia)}-{organizacion.slug}.pdf"
    )
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta
