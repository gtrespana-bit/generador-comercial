"""Perfiles sociales del producto: una sola lista para todo el sitio.

De aquí salen el ``sameAs`` del JSON-LD de organización, los enlaces del pie
y la verificación de dominio de Meta. Si mañana hay Instagram o YouTube, se
añaden aquí y aparecen en los tres sitios: no hay copias que se
desincronicen.

**Por qué importa el ``sameAs``**: Google usaba (hasta 2023) los enlaces
``rel="me"`` y hoy usa ``sameAs`` para unir las cuentas de una marca con su
entidad. Sin esa señal, la página de Facebook «CotizaT» y cotizat.online son
para el buscador dos cosas distintas con el mismo nombre. No es un factor de
posicionamiento por sí solo, pero sí es lo que permite que el nombre propio
se resuelva a una sola entidad (y lo que evita que un perfil homónimo se
quede el panel de marca).

**Lo que NO hace**: no asocia la página de Facebook con el dominio dentro de
Meta. Eso se hace en Meta Business Manager (Dominios → verificar propiedad)
y solo puede hacerlo quien tiene la cuenta; el resultado es una etiqueta
``<meta name="facebook-domain-verification">`` que este módulo ya emite si
existe la variable de entorno. Ver docs/FACEBOOK_Y_ENTIDAD_2026-10-22.md.
"""
from __future__ import annotations

import os

#: Perfiles oficiales de la marca. Clave estable → URL pública.
PERFILES: dict[str, str] = {
    "facebook": "https://www.facebook.com/profile.php?id=61593422986397",
}

#: Nombre visible de cada perfil, para el pie.
NOMBRES: dict[str, str] = {
    "facebook": "Facebook",
}


def same_as() -> list[str]:
    """URLs de los perfiles, en orden estable (lo que consume ``sameAs``)."""
    return [url for url in PERFILES.values() if url]


def enlaces() -> list[dict]:
    """Perfiles listos para pintar: ``[{"clave", "nombre", "url"}]``."""
    return [
        {"clave": clave, "nombre": NOMBRES.get(clave, clave.title()), "url": url}
        for clave, url in PERFILES.items()
        if url
    ]


def verificacion_dominio_meta() -> str:
    """Token de verificación de dominio de Meta Business Manager, si existe.

    Meta lo entrega al añadir el dominio en *Configuración del negocio →
    Seguridad de la marca → Dominios* y exige publicarlo como
    ``<meta name="facebook-domain-verification" content="…">``. Se lee del
    entorno (``COTIZAT_FACEBOOK_DOMAIN_VERIFICATION``) para no tener que
    tocar código ni compartir el token: lo pega el titular en Vercel y la
    etiqueta aparece en la siguiente compilación.

    Vacío = no se emite la etiqueta (el sitio no finge una verificación que
    no existe).
    """
    return os.environ.get("COTIZAT_FACEBOOK_DOMAIN_VERIFICATION", "").strip()
