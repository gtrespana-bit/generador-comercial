"""Catálogo de correos de CotizaT para enviarlos de prueba desde el panel.

Cada correo transaccional se describe aquí una sola vez: qué es, a quién va,
con qué datos de ejemplo se rellena y qué función lo envía. Lo usan dos
consumidores que deben coincidir siempre:

- ``app/routers/admin.py`` → página ``/admin/emails`` («Correos»), para que el
  operador envíe cualquiera a su buzón y lo revise en un cliente real.
- ``tools/enviar_prueba_emails.py`` → utilidad de terminal equivalente.

Los datos son de ejemplo y deliberadamente ficticios: este módulo nunca toca la
base de datos ni datos reales de clientes.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

#: Adjuntos mínimos pero válidos para que la prueba ejercite el camino real.
PDF_PRUEBA = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
    b"trailer<</Root 1 0 R>>\n"
    b"%%EOF\n"
)
COMPROBANTE_PRUEBA = b"\x89PNG\r\n\x1a\n(comprobante de prueba)"


def _hoy() -> date:
    return date.today()


# ---------------------------------------------------------------------------
# Constructores de kwargs: uno por correo, con datos de ejemplo.
# ---------------------------------------------------------------------------


def _kwargs_recordatorio(email: str) -> dict:
    return dict(
        email=email,
        organizacion_nombre="Constructora Andina, C.A.",
        plan_nombre="Prueba gratuita",
        es_prueba=True,
        vence=_hoy() + timedelta(days=5),
        dias_restantes=5,
    )


def _kwargs_aviso_licencia(email: str) -> dict:
    return dict(
        email=email,
        organizacion_nombre="Constructora Andina, C.A.",
        vence=_hoy() + timedelta(days=3),
        dias_restantes=3,
    )


def _kwargs_plan_activado(email: str) -> dict:
    return dict(
        email=email,
        organizacion_nombre="Constructora Andina, C.A.",
        plan_nombre="Plan anual",
        importe_texto="89,00 $",
        metodo_nombre="Pago móvil",
        inicio=_hoy(),
        vence=_hoy() + timedelta(days=365),
    )


def _kwargs_invitacion(email: str) -> dict:
    return dict(
        email=email,
        enlace="https://cotizat.online/invitaciones/enlace-de-prueba",
        organizacion_nombre="Constructora Andina, C.A.",
        invitador_nombre="Juan Pérez",
        invitador_email="juan@example.com",
        rol="administrador",
        caduca_el=datetime.now() + timedelta(days=7),
    )


def _kwargs_presupuesto(email: str) -> dict:
    return dict(
        email=email,
        asunto="Presupuesto P-2026-016 · Reforma de baño",
        mensaje="Hola, adjuntamos la propuesta de la reforma. Quedamos a tu disposición para cualquier duda.",
        empresa_nombre="Constructora Andina, C.A.",
        cliente_nombre="Cliente Ejemplo",
        presupuesto_numero="P-2026-016",
        presupuesto_titulo="Reforma de baño",
        total_texto="2.500,00 $",
        pdf=PDF_PRUEBA,
        nombre_pdf="presupuesto_P-2026-016.pdf",
        responder_a=email,
    )


def _kwargs_respuesta_propuesta(email: str) -> dict:
    return dict(
        email=email,
        decision="aceptada",
        empresa_nombre="Constructora Andina, C.A.",
        cliente_nombre="Cliente Ejemplo",
        presupuesto_numero="P-2026-016",
        presupuesto_titulo="Reforma de baño",
        version_numero=2,
        respondido_por_nombre="Ana Cliente",
        respondido_por_email="ana@example.com",
        comentario="Conforme, procedemos.",
        enlace_interno="https://cotizat.online/presupuestos/16#versiones",
    )


def _kwargs_compra(email: str) -> dict:
    # `email` aquí es el del comprador (reply_to); el destino real se pasa
    # como `destino_override`.
    return dict(
        nombre="Juan Pérez",
        email="juan@example.com",
        organizacion_nombre="Constructora Andina, C.A.",
        plan_nombre="Plan anual",
        importe_texto="89,00 $",
        metodo_nombre="Pago móvil",
        verificacion={
            "banco_origen": "Banco Provincial",
            "numero_operacion": "12345678",
            "fecha_pago": _hoy().strftime("%d/%m/%Y"),
            "nombre_titular": "Juan Pérez",
        },
        comprobante_nombre="comprobante.png",
        comprobante_bytes=COMPROBANTE_PRUEBA,
        destino_override=email,
    )


def _kwargs_demo(email: str) -> dict:
    return dict(
        nombre="Juan Pérez",
        email="juan@example.com",
        empresa="Constructora Andina, C.A.",
        telefono="0412-0000000",
        presupuestos_mes="10",
        mensaje="Me gustaría ver una demostración del producto.",
        destino_override=email,
    )


# ---------------------------------------------------------------------------
# Registro: cada entrada describe un correo y cómo enviarlo.
# ---------------------------------------------------------------------------

#: (slug, título, descripción, grupo, builder de kwargs, enviador)
_REGISTRO: tuple[tuple, ...] = (
    (
        "recordatorio",
        "Recordatorio de vencimiento",
        "Cron automático a 5 y 1 día antes de vencer. CTA al checkout.",
        "cliente",
        _kwargs_recordatorio,
        "enviar_recordatorio_vencimiento",
    ),
    (
        "aviso",
        "Aviso de vencimiento (manual)",
        "El que dispara el operador desde el panel de licencias.",
        "cliente",
        _kwargs_aviso_licencia,
        "enviar_aviso_licencia",
    ),
    (
        "plan_activado",
        "Plan activado",
        "Avisa al comprador con su recibo PDF adjunto.",
        "cliente",
        _kwargs_plan_activado,
        "enviar_activacion_plan_por_email",
    ),
    (
        "invitacion",
        "Invitación a equipo",
        "Invita a un colaborador con su enlace de un solo uso.",
        "cliente",
        _kwargs_invitacion,
        "enviar_invitacion_por_email",
    ),
    (
        "presupuesto",
        "Envío de presupuesto",
        "Entrega al cliente un presupuesto PDF (white-label).",
        "cliente",
        _kwargs_presupuesto,
        "enviar_presupuesto_por_email",
    ),
    (
        "respuesta_propuesta",
        "Respuesta de propuesta",
        "Notifica al operador la decisión del cliente.",
        "interno",
        _kwargs_respuesta_propuesta,
        "enviar_respuesta_propuesta_por_email",
    ),
    (
        "compra",
        "Notificación de compra",
        "Notifica al operador una compra con su comprobante.",
        "interno",
        _kwargs_compra,
        "enviar_compra_por_email",
    ),
    (
        "demo",
        "Solicitud de demo",
        "Notifica al operador una solicitud de demostración.",
        "interno",
        _kwargs_demo,
        "enviar_solicitud_demo_por_email",
    ),
)

_ETIQUETAS_GRUPO = {"cliente": "Al cliente", "interno": "Interno (a ti)"}


def catalogo_correos() -> list[dict]:
    """Fichas legibles de los correos, para renderizar el panel."""
    return [
        {
            "slug": slug,
            "titulo": titulo,
            "descripcion": descripcion,
            "grupo": grupo,
            "grupo_label": _ETIQUETAS_GRUPO[grupo],
        }
        for slug, titulo, descripcion, grupo, _builder, _enviador in _REGISTRO
    ]


def _resolver(slug: str):
    """Devuelve (builder, enviador) para un slug, o lanza ValueError."""
    for entrada in _REGISTRO:
        if entrada[0] == slug:
            from app.services import email as email_module

            builder = entrada[4]
            enviador = getattr(email_module, entrada[5])
            return builder, enviador
    raise ValueError(f"Correo de prueba desconocido: {slug}")


def enviar_correo_prueba(slug: str, email: str) -> str:
    """Envía el correo de prueba indicado a ``email`` y devuelve el id.

    Lanza ``ValueError`` si el slug no existe, y las excepciones propias del
    envío (``EmailNotConfigured`` / ``EmailSendError`` / ``EmailValidationError``)
    si la configuración o el proveedor fallan. El llamador decide el manejo.
    """
    builder, enviador = _resolver(slug)
    return enviador(**builder(email))
