"""Avisos al buzón del titular: venta confirmada y alta de cuenta.

El titular se enteraba de la primera venta por un correo de Stripe, no por su
producto. Este módulo cierra ese hueco desde el lado del servidor: cuando una
compra queda **activa** (Stripe por webhook o comprobante activado a mano) y
cuando alguien **se registra** o **empieza la prueba**, sale un correo al buzón
de soporte con el detalle.

Reglas que se respetan aquí, y son las mismas del resto de avisos internos:

- **Nunca lanzan.** El hecho ya está guardado en la base (la licencia concedida
  o la cuenta creada); un fallo de correo no puede deshacerlo ni devolver un
  error a quien acaba de pagar.
- **Nunca bloquean lo importante.** El envío es una llamada HTTP con tiempo de
  espera; quien llama desde una ruta asíncrona lo hace en un hilo aparte.
- **Sin secretos ni datos de negocio del cliente.** El aviso lleva el plan, el
  importe, el método y a quién facturar; nada de presupuestos ni catálogos.

El destino por omisión es el buzón de soporte (``COTIZAT_SUPPORT_EMAIL``,
``soporte@cotizat.online``) y se puede desviar con ``COTIZAT_AVISOS_EMAIL``.
"""
from __future__ import annotations

import logging

log = logging.getLogger("cotizat.avisos")


def url_panel_absoluta(path: str) -> str:
    """URL del panel para un correo; si no hay origen público, la ruta relativa.

    ``COTIZAT_PUBLIC_URL`` es obligatoria en producción, pero no en local ni en
    pruebas. Un aviso no debe quedarse sin enlace (ni romperse) por eso.
    """
    try:
        from ..auth import public_app_url

        return public_app_url(path)
    except Exception:
        return str(path or "")


def _plan_y_metodo(compra) -> tuple[str, str]:
    from ..datos_pago import metodo_info, plan_info

    try:
        plan_nombre = str(plan_info(compra.plan)["nombre"])
    except KeyError:
        plan_nombre = str(compra.plan or "Plan")
    try:
        metodo_nombre = str(metodo_info(compra.metodo_pago)["nombre"])
    except KeyError:
        metodo_nombre = str(compra.metodo_pago or "")
    return plan_nombre, metodo_nombre


def avisar_venta(
    db,
    *,
    compra,
    licencia=None,
    renovacion: bool = False,
    origen: str = "",
    idioma: str = "es",
) -> str:
    """Envía el aviso de venta confirmada. Devuelve el id o ``""``.

    ``licencia`` aporta el período pagado (inicio → vence); si no llega, se usa
    el que la compra guarda copiado, que es el que ve el cliente en su recibo.
    """
    from .email import (
        EmailNotConfigured,
        EmailSendError,
        EmailValidationError,
        enviar_aviso_venta_por_email,
    )
    from ..models import Organizacion
    from ..utils import fmt_monto

    try:
        organizacion = (
            getattr(licencia, "organizacion", None)
            or db.get(Organizacion, compra.organizacion_id)
        )
        plan_nombre, metodo_nombre = _plan_y_metodo(compra)
        moneda = (
            (getattr(licencia, "moneda", "") if licencia else "")
            or compra.moneda
            or "USD"
        )
        importe = (
            (getattr(licencia, "importe", 0) if licencia else 0) or compra.importe or 0
        )
        inicio = getattr(licencia, "inicio", None) or getattr(compra, "licencia_inicio", None)
        vence = getattr(licencia, "vence", None) or getattr(compra, "licencia_vence", None)
        periodo_texto = (
            f"{inicio:%d/%m/%Y} → {vence:%d/%m/%Y}" if inicio and vence else ""
        )
        return enviar_aviso_venta_por_email(
            organizacion_nombre=organizacion.nombre if organizacion else "",
            comprador_email=str(getattr(compra, "creada_por_email", "") or ""),
            plan_nombre=plan_nombre,
            importe_texto=fmt_monto(importe, moneda),
            metodo_nombre=metodo_nombre,
            periodo_texto=periodo_texto,
            compra_id=int(getattr(compra, "id", 0) or 0),
            renovacion=bool(renovacion),
            origen=origen,
            panel_url=url_panel_absoluta("/admin/ingresos?tab=ventas"),
            idioma=idioma,
        )
    except (EmailNotConfigured, EmailValidationError, EmailSendError) as exc:
        log.warning("Venta de la compra %s sin aviso por correo (%s).", getattr(compra, "id", "?"), exc)
    except Exception:
        log.exception("Error avisando de la venta de la compra %s.", getattr(compra, "id", "?"))
    return ""


def avisar_registro(
    *,
    email: str,
    nombre: str = "",
    pais: str = "",
    origen: str = "registro",
    organizacion_nombre: str = "",
    prueba_texto: str = "",
    idioma: str = "es",
) -> str:
    """Envía el aviso de alta nueva (cuenta o prueba). Devuelve el id o ``""``."""
    from .email import (
        EmailNotConfigured,
        EmailSendError,
        EmailValidationError,
        enviar_aviso_registro_por_email,
    )

    try:
        return enviar_aviso_registro_por_email(
            email=email,
            nombre=nombre,
            pais=pais,
            origen=origen,
            organizacion_nombre=organizacion_nombre,
            prueba_texto=prueba_texto,
            panel_url=url_panel_absoluta("/admin/clientes"),
            idioma=idioma,
        )
    except (EmailNotConfigured, EmailValidationError, EmailSendError) as exc:
        log.warning("Alta de %s sin aviso por correo (%s).", email, exc)
    except Exception:
        log.exception("Error avisando del alta de %s.", email)
    return ""
