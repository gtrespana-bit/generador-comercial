"""Medición de audiencia con Google Analytics 4 (etiqueta gtag.js).

El ID de medición (``G-XXXXXXXXXX``) se configura con ``COTIZAT_GA_ID``
(también se aceptan ``GA_MEASUREMENT_ID`` y ``GOOGLE_ANALYTICS_ID``, nombres
que Google y Vercel sugieren a menudo). Mientras no haya un ID válido:

- no se renderiza ninguna etiqueta en las plantillas (``ga_id`` queda vacío);
- la política CSP se mantiene estricta, sin abrir dominios externos.

En producción (``COTIZAT_ENV`` / ``VERCEL_ENV``) se usa por omisión la
propiedad pública de CotizaT ``G-013NT3ZTHP``: el ID de medición no es un
secreto (viaja en el HTML) y así la etiqueta no depende de haber recordado
redesplegar tras añadir la variable. Se apaga con ``COTIZAT_GA_ID=off``.

Al activarse se renderiza la etiqueta estándar de Google y se abre en CSP
lo imprescindible para que gtag.js cargue, pinte el pixel de respaldo y
envíe las mediciones (script, img y connect).
"""
from __future__ import annotations

import os
import re

# IDs de medición típicos: GA4 (G-…), Google Tag (GT-…), Ads (AW-…) y
# el histórico Universal Analytics (UA-…, con formato UA-XXXXX-Y).
# Longitud acotada por seguridad: el valor se incrusta dentro de un
# literal JS y en una URL.
_ID_RE = re.compile(r"(?:G|GT|AW|UA)-[A-Za-z0-9-]{2,32}")

#: Propiedad GA4 de cotizat.online. Es un identificador público (aparece
#: en el HTML de quien visita el sitio); no es una credencial.
ID_PRODUCCION = "G-013NT3ZTHP"

_APAGADO = frozenset({"off", "0", "false", "none", "-", "no"})

# Hosts que Google documenta para la etiqueta GA4 con CSP:
# https://developers.google.com/tag-platform/security/guides/csp
# script-src: gtag.js. img-src: pixel de respaldo (el detector de Google
# lo usa cuando no ejecuta JS). connect-src: recolector y Google Signals.
SCRIPT_HOSTS = (
    "https://www.googletagmanager.com",
    "https://*.googletagmanager.com",
)
IMG_HOSTS = (
    "https://www.google-analytics.com",
    "https://*.google-analytics.com",
    "https://www.googletagmanager.com",
    "https://*.googletagmanager.com",
)
CONNECT_HOSTS = (
    "https://www.google-analytics.com",
    "https://*.google-analytics.com",
    "https://*.analytics.google.com",
    "https://*.googletagmanager.com",
)

_VARS_ID = ("COTIZAT_GA_ID", "GA_MEASUREMENT_ID", "GOOGLE_ANALYTICS_ID")


def _en_produccion() -> bool:
    crudo = os.environ.get("COTIZAT_ENV", "").strip().lower()
    if crudo in {"production", "prod", "produccion", "producción"}:
        return True
    return os.environ.get("VERCEL_ENV", "").strip().lower() == "production"


def _candidato_entorno() -> str:
    for nombre in _VARS_ID:
        valor = os.environ.get(nombre)
        if valor is not None and str(valor).strip():
            return str(valor).strip().strip("\"'")
    return ""


def ga_measurement_id() -> str:
    """ID de medición válido o cadena vacía si GA está apagado."""
    candidate = _candidato_entorno()
    if candidate.lower() in _APAGADO:
        return ""
    if not candidate and _en_produccion():
        candidate = ID_PRODUCCION
    if _ID_RE.fullmatch(candidate):
        return candidate
    hallado = _ID_RE.search(candidate)
    return hallado.group(0) if hallado else ""


def _csp_hosts(hosts: tuple[str, ...]) -> str:
    return " " + " ".join(hosts) if hosts else ""


def csp_script_src_extra() -> str:
    """Hosts extra para ``script-src`` (cadena vacía si GA está inactivo)."""
    return _csp_hosts(SCRIPT_HOSTS) if ga_measurement_id() else ""


def csp_img_src_extra() -> str:
    """Hosts extra para ``img-src`` (pixel de respaldo de gtag)."""
    return _csp_hosts(IMG_HOSTS) if ga_measurement_id() else ""


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
