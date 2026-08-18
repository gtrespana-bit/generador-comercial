"""Envía los correos de CotizaT a un buzón para revisarlos en cliente real.

Utilidad del titular para **ver los correos tal cual llegan** (Gmail, Zoho,
Outlook…), no como se ven en una vista previa HTML. Comparte el catálogo y los
datos de ejemplo con la página `/admin/emails` del panel (misma fuente de
verdad: ``app/services/correos_prueba.py``).

Cómo ejecutarlo (desde la raíz del repositorio, con la clave de Resend en el
entorno):

    RESEND_API_KEY=re_... \
    COTIZAT_EMAIL_FROM="CotizaT <no-responder@send.cotizat.online>" \
    .venv/bin/python tools/enviar_prueba_emails.py

Por omisión manda a ``soporte@cotizat.online``; se puede cambiar con un
argumento:

    .venv/bin/python tools/enviar_prueba_emails.py tu-correo@example.com

``--render-only`` no envía nada: renderiza las plantillas y las guarda en el
directorio de trabajo como ``correo-*.html`` para inspeccionarlas sin red.

Nota: ``RESEND_API_KEY`` es un secreto. Ejecuta esto en TU equipo; no lo pongas
en un chat ni lo commitees nunca.
"""
from __future__ import annotations

import os
import sys
import tempfile
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


def _render_only(destino: str) -> int:
    """Renderiza las 8 plantillas y las guarda como .html (sin red)."""
    from app.services import email as email_module
    from app.services.correos_prueba import catalogo_correos, enviar_correo_prueba

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
        for ficha in catalogo_correos():
            enviar_correo_prueba(ficha["slug"], destino)
    finally:
        email_module._post_resend = original

    print(f"{len(guardados)} correos renderizados en el directorio de trabajo:")
    for ruta in guardados:
        print(f"  - {ruta.name}")
    print(f"\nDestino previsto para el envío real: {destino}")
    return 0


def main() -> int:
    destino = (
        sys.argv[1]
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--")
        else DESTINO_POR_OMISION
    )
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

    from app.services.correos_prueba import catalogo_correos, enviar_correo_prueba

    correos = catalogo_correos()
    print(f"Enviando {len(correos)} correos de prueba a {destino} …\n")
    for ficha in correos:
        try:
            envio_id = enviar_correo_prueba(ficha["slug"], destino)
            print(f"  ✅ {ficha['titulo']}  (id {envio_id})")
        except Exception as exc:  # noqa: BLE001 - el titular ve el fallo concreto
            print(f"  ❌ {ficha['titulo']}: {exc}")
    print("\nListo. Revisa la bandeja de entrada (y spam, por si acaso).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
