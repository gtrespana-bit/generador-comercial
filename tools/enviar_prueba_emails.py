"""Envía los 8 correos de CotizaT a un buzón para revisarlos en cliente real.

Utilidad del titular para **ver los correos tal cual llegan** (Gmail, Zoho,
Outlook…), no como se ven en una vista previa HTML. Usa exactamente las mismas
funciones y plantillas que producción: no duplica nada, solo las invoca con
datos de ejemplo.

Cómo ejecutarlo (desde la raíz del repositorio, con la clave de Resend en el
entorno):

    RESEND_API_KEY=re_... \
    COTIZAT_EMAIL_FROM="CotizaT <no-responder@send.cotizat.online>" \
    .venv/bin/python tools/enviar_prueba_emails.py

Por omisión manda a ``soporte@cotizat.online``; se puede cambiar con un
argumento:

    .venv/bin/python tools/enviar_prueba_emails.py tu-correo@example.com

``--render-only`` no envía nada: renderiza las 8 plantillas (mismo contexto que
producción) y las guarda en el directorio de trabajo como ``correo-<n>-*.html``
para inspeccionarlas sin red.

Nota: ``RESEND_API_KEY`` es un secreto. Ejecuta esto en TU equipo; no lo pongas
en un chat ni lo commitees nunca.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# Aislamos la base de datos para no tocar la del desarrollador ni la de
# producción: este script solo necesita las funciones de correo.
os.environ.pop("DATABASE_URL", None)
os.environ.setdefault(
    "COTIZAT_DB",
    str(Path(tempfile.mkdtemp(prefix="cotizat-email-prueba-")) / "prueba.db"),
)

DESTINO_POR_OMISION = "soporte@cotizat.online"
HOY = date.today()

_PDF_PRUEBA = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
    b"trailer<</Root 1 0 R>>\n"
    b"%%EOF\n"
)
_COMPROBANTE_PRUEBA = b"\x89PNG\r\n\x1a\n(comprobante de prueba)"


def _casos() -> list[tuple[str, dict]]:
    """Cada caso: (nombre legible, kwargs de la función de envío)."""
    return [
        (
            "Recordatorio de vencimiento (cron, prueba gratuita)",
            dict(
                organizacion_nombre="Constructora Andina, C.A.",
                plan_nombre="Prueba gratuita",
                es_prueba=True,
                vence=HOY + timedelta(days=5),
                dias_restantes=5,
            ),
        ),
        (
            "Aviso de vencimiento (manual, operador)",
            dict(
                organizacion_nombre="Constructora Andina, C.A.",
                vence=HOY + timedelta(days=3),
                dias_restantes=3,
            ),
        ),
        (
            "Plan activado (con recibo)",
            dict(
                organizacion_nombre="Constructora Andina, C.A.",
                plan_nombre="Plan anual",
                importe_texto="89,00 $",
                metodo_nombre="Pago móvil",
                inicio=HOY,
                vence=HOY + timedelta(days=365),
            ),
        ),
        (
            "Invitación a equipo",
            dict(
                enlace="https://cotizat.online/invitaciones/enlace-de-prueba",
                organizacion_nombre="Constructora Andina, C.A.",
                invitador_nombre="Juan Pérez",
                invitador_email="juan@example.com",
                rol="administrador",
                caduca_el=datetime.now() + timedelta(days=7),
            ),
        ),
        (
            "Envío de presupuesto (cliente)",
            dict(
                asunto="Presupuesto P-2026-016 · Reforma de baño",
                mensaje="Hola, adjuntamos la propuesta de la reforma. Quedamos a tu disposición para cualquier duda.",
                empresa_nombre="Constructora Andina, C.A.",
                cliente_nombre="Cliente Ejemplo",
                presupuesto_numero="P-2026-016",
                presupuesto_titulo="Reforma de baño",
                total_texto="2.500,00 $",
                pdf=_PDF_PRUEBA,
                nombre_pdf="presupuesto_P-2026-016.pdf",
                responder_a=DESTINO_POR_OMISION,
            ),
        ),
        (
            "Respuesta de propuesta (al operador)",
            dict(
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
            ),
        ),
        (
            "Notificación de compra (al operador)",
            dict(
                nombre="Juan Pérez",
                email="juan@example.com",
                organizacion_nombre="Constructora Andina, C.A.",
                plan_nombre="Plan anual",
                importe_texto="89,00 $",
                metodo_nombre="Pago móvil",
                verificacion={
                    "banco_origen": "Banco Provincial",
                    "numero_operacion": "12345678",
                    "fecha_pago": HOY.strftime("%d/%m/%Y"),
                    "nombre_titular": "Juan Pérez",
                },
                comprobante_nombre="comprobante.png",
                comprobante_bytes=_COMPROBANTE_PRUEBA,
            ),
        ),
        (
            "Solicitud de demo (inactivo)",
            dict(
                nombre="Juan Pérez",
                email="juan@example.com",
                empresa="Constructora Andina, C.A.",
                telefono="0412-0000000",
                presupuestos_mes="10",
                mensaje="Me gustaría ver una demostración del producto.",
            ),
        ),
    ]


def _enviadores():
    """Devuelve, para cada caso, la función que lo envía (en el mismo orden)."""
    from app.services import email as email_module

    return [
        email_module.enviar_recordatorio_vencimiento,
        email_module.enviar_aviso_licencia,
        email_module.enviar_activacion_plan_por_email,
        email_module.enviar_invitacion_por_email,
        email_module.enviar_presupuesto_por_email,
        email_module.enviar_respuesta_propuesta_por_email,
        email_module.enviar_compra_por_email,
        email_module.enviar_solicitud_demo_por_email,
    ]


def _invocar(funcion, kwargs, destino: str):
    """Llama a una función de envío resolviendo el destinatario correcto.

    La mayoría de las funciones reciben el destinatario como ``email=``. Las de
    compra y demo, en cambio, ya traen su ``email`` (el comprador/solicitante)
    y envían siempre al buzón de soporte: en esos casos no se inyecta destino.
    """
    if "email" not in kwargs:
        kwargs["email"] = destino
    return funcion(**kwargs)


def _render_only(destino: str) -> int:
    """Renderiza las 8 plantillas y las guarda como .html (sin red)."""
    from app.services import email as email_module

    # Las funciones validan la configuración antes de llamar a `_post_resend`,
    # que aquí está sustituido: bastan valores de pega para que la validación
    # pase sin tocar la red.
    os.environ.setdefault("RESEND_API_KEY", "re_prueba")
    os.environ.setdefault("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")

    guardados: list[Path] = []

    def _capturar(settings, *, to, subject, html, text, **__kwargs):
        nombre = "".join(
            c if c.isalnum() or c in "-_" else "-" for c in subject.lower()
        )[:60].strip("-")
        ruta = Path.cwd() / f"correo-{nombre}.html"
        ruta.write_text(html, encoding="utf-8")
        guardados.append(ruta)
        return "render-only"

    original = email_module._post_resend
    email_module._post_resend = _capturar
    try:
        for (_nombre, kwargs), funcion in zip(_casos(), _enviadores()):
            _invocar(funcion, kwargs, destino)
    finally:
        email_module._post_resend = original

    print(f"{len(guardados)} correos renderizados en el directorio de trabajo:")
    for ruta in guardados:
        print(f"  - {ruta.name}")
    print(f"\nDestino previsto para el envío real: {destino}")
    return 0


def main() -> int:
    destino = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else DESTINO_POR_OMISION
    if "--render-only" in sys.argv:
        return _render_only(destino)

    if not os.environ.get("RESEND_API_KEY"):
        print("Falta RESEND_API_KEY en el entorno. No se puede enviar.")
        print("Ejecuta con:")
        print("  RESEND_API_KEY=re_... COTIZAT_EMAIL_FROM='CotizaT <...>' "
              ".venv/bin/python tools/enviar_prueba_emails.py")
        return 2
    if not os.environ.get("COTIZAT_EMAIL_FROM"):
        print("Falta COTIZAT_EMAIL_FROM en el entorno.")
        return 2

    casos = _casos()
    enviadores = _enviadores()
    print(f"Enviando {len(casos)} correos de prueba a {destino} …\n")
    for (_nombre, kwargs), funcion in zip(casos, enviadores):
        try:
            envio_id = _invocar(funcion, kwargs, destino)
            print(f"  ✅ {_nombre}  (id {envio_id})")
        except Exception as exc:  # noqa: BLE001 - el titular ve el fallo concreto
            print(f"  ❌ {_nombre}: {exc}")
    print("\nListo. Revisa la bandeja de entrada (y spam, por si acaso).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
