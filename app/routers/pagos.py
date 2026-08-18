"""Compra de planes con pago manual: el cliente elige método, declara la
verificación y adjunta su comprobante (E1-059 cobro manual)."""

from __future__ import annotations

import io
import json
import logging
from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Form, Request, UploadFile

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..datos_pago import METODOS_PAGO, PLANES, metodo_info, plan_info

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


@router.get("/pago/comprar", response_class=HTMLResponse, include_in_schema=False)
def comprar_plan(request: Request, plan: str = "", db: Session = Depends(get_db)):
    """Página de compra: resumen del plan + métodos de pago + formulario."""
    ficha = _plan_o_redirect(request, plan)
    if ficha is None:
        return RedirectResponse("/pago", status_code=303)

    organizacion = db.get(Organizacion, int(db.info.get("organizacion_id") or 0))
    usuario = db.get(Usuario, int(db.info.get("usuario_id") or 0))
    return TEMPLATES.TemplateResponse(
        request,
        "pago/comprar.html",
        {
            "plan": plan,
            "plan_ficha": ficha,
            "metodos": METODOS_PAGO,
            "metodos_json": json.dumps(METODOS_PAGO, ensure_ascii=False),
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
    comprobante: UploadFile | None = None,
    db: Session = Depends(get_db),
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

    # Datos de verificación: solo los campos declarados para el método.
    verificacion = {}
    for campo, _etiqueta, _tipo, _placeholder in ficha_metodo["verificacion"]:
        valor = str(form.get(campo) or "").strip()
        if valor:
            verificacion[campo] = valor[:300]

    # Comprobante: opcional en el servidor, obligatorio en el servicio.
    datos_comprobante = b""
    nombre_comprobante = ""
    mime_comprobante = ""
    if comprobante is not None and comprobante.filename:
        nombre_comprobante = Path(comprobante.filename).name[:255]
        datos_comprobante = await comprobante.read()
        mime_comprobante = _validar_comprobante(nombre_comprobante, datos_comprobante)
        if not mime_comprobante:
            return RedirectResponse(
                f"/pago/comprar?plan={quote(plan)}&error="
                "El comprobante debe ser una imagen (PNG, JPG, WEBP) o un PDF "
                "de hasta 12 MB.",
                status_code=303,
            )
    else:
        # Formularios pueden no enviar archivo; el servicio lo exige.
        datos_comprobante = b""
        nombre_comprobante = ""
        mime_comprobante = ""

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

    return RedirectResponse(
        f"/pago/confirmacion?id={compra.id}", status_code=303
    )


@router.get("/pago/confirmacion", response_class=HTMLResponse, include_in_schema=False)
def confirmacion_compra(request: Request, id: int = 0, db: Session = Depends(get_db)):
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
