"""Normalización de correo y detección de desechables para el alta.

La prueba gratuita se concede **una vez por identidad de correo**. Para que eso
signifique algo hay que decidir cuándo dos correos son la misma persona: si
`fulano@gmail.com` y `f.u.l.a.n.o+cotizat@gmail.com` cuentan como identidades
distintas, la restricción única de la base no protege de nada y el sistema es
teatro.

Este módulo contiene esa decisión, aislada y sin dependencias de base de datos
ni de red, porque es la pieza que más se va a tocar con el tiempo (cada mes
aparecen dominios desechables nuevos) y la que más barato sale probar.

Dos reglas deliberadamente conservadoras:

* **Se normaliza poco y con criterio.** Solo se aplican transformaciones que
  son ciertas por el funcionamiento del proveedor, no heurísticas. Pasarse de
  listo aquí tiene un coste asimétrico: fundir dos correos distintos en la
  misma identidad deja a un cliente legítimo sin su prueba y sin entender por
  qué, y ese fallo es silencioso.
* **La lista de desechables no pretende ser exhaustiva.** Es imposible y no
  hace falta: cierra el abuso barato de un clic. Quien registre un dominio
  propio para conseguir siete días gratis ya está invirtiendo más de lo que
  vale la prueba.
"""
from __future__ import annotations

#: Proveedores que ignoran los puntos del usuario: `f.u.l.a.n.o@` y `fulano@` son el
#: mismo buzón. Es una propiedad documentada del proveedor, no una suposición.
#: Fuera de esta lista los puntos se respetan: en un dominio corporativo
#: `fulano.detal@` y `fulanodetal@` pueden ser dos personas distintas.
_DOMINIOS_SIN_PUNTOS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
    }
)

#: Alias equivalentes del mismo proveedor, para que no cuenten como dos altas.
_DOMINIOS_EQUIVALENTES = {
    "googlemail.com": "gmail.com",
}

#: Proveedores que soportan subdirecciones con `+`: todo lo que sigue al signo
#: es una etiqueta del propio usuario y el correo llega al mismo buzón. Es el
#: truco más habitual para multiplicar registros, y el más fácil de cerrar.
#:
#: Outlook y Yahoo también lo admiten, pero de forma menos uniforme según la
#: antigüedad de la cuenta; se incluyen porque el riesgo de recortar la
#: etiqueta es bajo: como mucho se unifican dos correos del mismo buzón.
_DOMINIOS_CON_SUBDIRECCION = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "outlook.com",
        "hotmail.com",
        "live.com",
        "yahoo.com",
        "proton.me",
        "protonmail.com",
        "icloud.com",
        "fastmail.com",
    }
)

#: Correo de usar y tirar. Un buzón que se autodestruye en diez minutos no
#: identifica a nadie: conceder pruebas a estos dominios equivale a no tener
#: control ninguno, porque el mismo navegador genera una identidad nueva cada
#: vez sin coste. Se bloquea el registro (decisión del titular).
_DOMINIOS_DESECHABLES = frozenset(
    {
        "0-mail.com",
        "10minutemail.com",
        "20minutemail.com",
        "33mail.com",
        "anonbox.net",
        "burnermail.io",
        "dispostable.com",
        "emailondeck.com",
        "fakeinbox.com",
        "getairmail.com",
        "getnada.com",
        "guerrillamail.com",
        "guerrillamail.info",
        "guerrillamail.net",
        "guerrillamail.org",
        "inboxbear.com",
        "jetable.org",
        "mailcatch.com",
        "maildrop.cc",
        "mailinator.com",
        "mailnesia.com",
        "mailsac.com",
        "mintemail.com",
        "mohmal.com",
        "moakt.com",
        "mytemp.email",
        "sharklasers.com",
        "spam4.me",
        "spamgourmet.com",
        "temp-mail.io",
        "temp-mail.org",
        "tempail.com",
        "tempinbox.com",
        "tempmail.com",
        "tempmail.dev",
        "tempmailo.com",
        "throwawaymail.com",
        "trashmail.com",
        "trashmail.de",
        "trbvm.com",
        "yopmail.com",
        "yopmail.fr",
        "yopmail.net",
    }
)

#: Sufijos de dominios cuyos subdominios son todos desechables (`*.mailinator.com`).
_SUFIJOS_DESECHABLES = (
    ".mailinator.com",
    ".yopmail.com",
    ".trashmail.com",
    ".33mail.com",
)


def partes_correo(email: str) -> tuple[str, str]:
    """Devuelve `(usuario, dominio)` en minúsculas, o `("", "")` si no es válido.

    No valida el correo a fondo —de eso ya se encarga el proveedor de
    autenticación—, solo lo parte para poder normalizarlo.
    """
    limpio = (email or "").strip().lower()
    if limpio.count("@") != 1:
        return "", ""
    usuario, dominio = limpio.split("@", 1)
    usuario = usuario.strip()
    dominio = dominio.strip().strip(".")
    if not usuario or not dominio or "." not in dominio:
        return "", ""
    return usuario, dominio


def es_desechable(email: str) -> bool:
    """Indica si el correo pertenece a un proveedor de usar y tirar."""
    _, dominio = partes_correo(email)
    if not dominio:
        return False
    if dominio in _DOMINIOS_DESECHABLES:
        return True
    return any(dominio.endswith(sufijo) for sufijo in _SUFIJOS_DESECHABLES)


def normalizar_email(email: str) -> str:
    """Reduce un correo a la identidad real del buzón que hay detrás.

    Aplica, en este orden: minúsculas y recorte, unificación de dominios
    equivalentes, borrado de la subdirección `+etiqueta` y borrado de los
    puntos del usuario, cada uno **solo** en los dominios donde el proveedor
    garantiza esa equivalencia.

    Si el correo no se puede interpretar se devuelve tal cual en minúsculas:
    ante la duda, no se fusionan identidades.

    >>> normalizar_email("Fulano.Detal+cotizat@GMail.com")
    'fulanodetal@gmail.com'
    >>> normalizar_email("fulano.detal@miempresa.com")
    'fulano.detal@miempresa.com'
    """
    usuario, dominio = partes_correo(email)
    if not usuario:
        return (email or "").strip().lower()

    dominio = _DOMINIOS_EQUIVALENTES.get(dominio, dominio)

    if dominio in _DOMINIOS_CON_SUBDIRECCION and "+" in usuario:
        usuario = usuario.split("+", 1)[0]

    if dominio in _DOMINIOS_SIN_PUNTOS:
        usuario = usuario.replace(".", "")

    if not usuario:
        # `+etiqueta@gmail.com` o `.@gmail.com` no dejan usuario: sin identidad
        # que registrar, se devuelve el original para no colisionar con otros.
        return (email or "").strip().lower()

    return f"{usuario}@{dominio}"
