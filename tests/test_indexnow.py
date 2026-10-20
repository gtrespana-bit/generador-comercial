"""IndexNow: la clave pública y su ruta de verificación.

La clave no es un secreto (se publica para demostrar la propiedad del
dominio), pero su formato y su ruta son el contrato con Bing/Yahoo: si
el fichero devolviera algo más que la clave, la verificación fallaría
en silencio y los envíos de ``tools/indexnow.py`` serían rechazados.
"""
import re

from app.indexnow import CLAVE, RUTA_CLAVE


def test_la_clave_tiene_el_formato_que_exige_indexnow():
    # IndexNow admite de 8 a 128 caracteres hexadecimales.
    assert re.fullmatch(r"[0-9a-f]{8,128}", CLAVE)
    assert RUTA_CLAVE == f"/{CLAVE}.txt"


def test_la_ruta_sirve_solo_la_clave(cliente_web):
    respuesta = cliente_web.get(RUTA_CLAVE)
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/plain")
    # Ni salto de línea ni adornos: el verificador compara el cuerpo entero.
    assert respuesta.text == CLAVE


def test_robots_y_sitemap_siguen_vivos(cliente_web):
    robots = cliente_web.get("/robots.txt")
    assert robots.status_code == 200
    assert "Sitemap:" in robots.text

    sitemap = cliente_web.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "<urlset" in sitemap.text
