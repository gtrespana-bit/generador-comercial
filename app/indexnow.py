"""IndexNow: avisar a Bing (y con él, a Yahoo) sin esperar al rastreo.

IndexNow es el protocolo con el que un sitio avisa de URLs nuevas o
actualizadas; lo escuchan Bing y los buscadores que se alimentan de su
índice (Yahoo entre ellos). Google no participa: su vía sigue siendo el
sitemap enviado en Search Console.

La clave **no es un secreto**: por diseño del protocolo se publica en
``/{clave}.txt`` para demostrar la propiedad del dominio, igual que el
identificador de GA4 vive en ``app/analytics.py``. Por eso es una
constante del repo y no una variable de entorno: tiene que ser la misma
en cada despliegue y la herramienta de envío (``tools/indexnow.py``) la
lee de aquí.
"""

from __future__ import annotations

#: Clave pública IndexNow (hex). Se sirve tal cual en ``RUTA_CLAVE``.
CLAVE = "c2ecc63e4cd4d18c77e5b5e5430d7358"

#: Ruta pública donde los buscadores verifican la propiedad del dominio.
RUTA_CLAVE = f"/{CLAVE}.txt"
