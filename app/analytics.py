"""Medición de audiencia con Google Analytics 4 (etiqueta gtag.js).

El ID de medición (``G-XXXXXXXXXX``) se configura con la variable de entorno
``COTIZAT_GA_ID``. Mientras no esté definida:

- no se renderiza ninguna etiqueta en las plantillas (``ga_id`` queda vacío);
- la política CSP se mantiene estricta, sin abrir dominios externos.

Al configurarla se renderiza la etiqueta estándar de Google y se abre en CSP
lo imprescindible para que gtag.js pueda cargarse y enviar las mediciones.
"""
from __future__ import annotations

import os
import re

# IDs de medición típicos: GA4 (G-…), Google Tag (GT-…), Ads (AW-…) y
# el histórico Universal Analytics (UA-…, con formato UA-XXXXX-Y).
# Longitud acotada por seguridad: el valor se incrusta dentro de un
# literal JS y en una URL.
_ID_RE = re.compile(r"(?:G|GT|AW|UA)-[A-Za-z0-9-]{2,32}$")

# Hosts que Google recomienda permitir para la etiqueta GA4. La lista de
# connect-src incluye los dominios regionales (*.google-analytics.com) que
# usa la medición y el recolector de Google Signals.
SCRIPT_HOSTS = ("https://www.googletagmanager.com",)
CONNECT_HOSTS = (
    "https://www.google-analytics.com",
    "https://*.google-analytics.com",
    "https://*.analytics.google.com",
    "https://*.googletagmanager.com",
)


def ga_measurement_id() -> str:
    """ID de medición válido o cadena vacía si no hay uno configurado."""
    candidate = os.environ.get("COTIZAT_GA_ID", "").strip()
    return candidate if _ID_RE.match(candidate) else ""


def _csp_hosts(hosts: tuple[str, ...]) -> str:
    return " " + " ".join(hosts) if hosts else ""


def csp_script_src_extra() -> str:
    """Hosts extra para ``script-src`` (cadena vacía si GA está inactivo)."""
    return _csp_hosts(SCRIPT_HOSTS) if ga_measurement_id() else ""


def csp_connect_src_extra() -> str:
    """Hosts extra para ``connect-src`` (cadena vacía si GA está inactivo)."""
    return _csp_hosts(CONNECT_HOSTS) if ga_measurement_id() else ""


# ── Eventos de conversión de un solo uso (servidor → página siguiente) ───────

#: Cookie efímera con el nombre del evento a emitir en la próxima página
#: renderizada. La fija el servidor tras completar una acción (registro,
#: login, cobro) y la consume el partial ``_ga.html``; el middleware de
#: seguridad la borra en esa misma respuesta HTML para no repetirla.
GA_COOKIE_EVENTO = "cotizat_ga_evento"

#: Cookie persistente que recuerda que la conversión ``purchase`` ya se
#: emitió: la página de éxito de Stripe se puede recargar y no debemos
#: contar el mismo cobro dos veces.
GA_MARCADOR_PURCHASE = "cotizat_ga_purchase"

#: Nombres de evento que el servidor puede encolar. Coinciden con los
#: nombres reservados de GA4, así se pueden marcar como «eventos clave»
#: (conversiones) sin renombrar nada en la consola de Google.
EVENTOS_SERVIDOR = frozenset({"sign_up", "login", "purchase"})


def evento_permitido(nombre: str) -> bool:
    return nombre in EVENTOS_SERVIDOR


def evento_pendiente(cookies) -> str:
    """Evento encolado en la cookie, si es uno de los permitidos."""
    nombre = str((cookies or {}).get(GA_COOKIE_EVENTO, "") or "")
    return nombre if evento_permitido(nombre) else ""


def encolar_evento_ga(response, nombre: str) -> bool:
    """Encola un evento GA4 para la siguiente página HTML.

    Devuelve False sin tocar la respuesta si GA no está configurado o el
    nombre no está en el catálogo permitido: fuera de esos eventos no se
    emite nada nunca.
    """
    if not ga_measurement_id() or not evento_permitido(nombre):
        return False
    response.set_cookie(
        GA_COOKIE_EVENTO, nombre, max_age=600, path="/", httponly=True,
        samesite="lax",
    )
    return True


def encolar_purchase_unico(request, response) -> bool:
    """Encola ``purchase`` una única vez por navegador (recargas no cuentan)."""
    if request.cookies.get(GA_MARCADOR_PURCHASE):
        return False
    if not encolar_evento_ga(response, "purchase"):
        return False
    response.set_cookie(
        GA_MARCADOR_PURCHASE, "1", max_age=365 * 24 * 3600, path="/",
        httponly=True, samesite="lax",
    )
    return True
