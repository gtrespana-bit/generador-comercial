"""Presupuesto de muestra comercial (E1-052).

El «PDF de ejemplo» que enlaza la landing debe cumplir dos cosas a la vez:
ser un documento comercial creíble y no contener ningún dato personal real.
Estas pruebas garantizan que el archivo versionado sigue siendo un PDF válido
y que su contenido (empresa, cliente, contacto e importes) es ficticio.
"""
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.main import app

RUTA_PDF = Path(__file__).resolve().parent.parent / "app" / "static" / "pdf" / "presupuesto-ejemplo.pdf"

# Marcadores de datos ficticios que deben aparecer en el documento.
MARCADORES_FICTICIOS = (
    "Construcciones El Samán",   # empresa inventada
    "J-00000000-0",              # RIF marcador, imposible de confundir
    "ejemplo.com",               # dominio de ejemplo reservado (RFC 2606)
    "Familia Rodríguez",         # cliente genérico sin documento real
    "P-2026-001",
    "Documento de muestra",      # nota de honestidad
    "ficticios",
)


def _texto(datos: bytes) -> str:
    import io

    reader = PdfReader(io.BytesIO(datos))
    return "\n".join((pag.extract_text() or "") for pag in reader.pages)


def test_pdf_estatico_es_valido_y_ficticio():
    assert RUTA_PDF.exists(), "Falta el PDF de ejemplo; regenera con tools/generar_presupuesto_muestra.py"
    datos = RUTA_PDF.read_bytes()
    assert datos.startswith(b"%PDF"), "El archivo versionado no es un PDF válido"
    assert len(datos) > 20_000, "El PDF parece vacío o truncado"
    texto = _texto(datos)
    for marcador in MARCADORES_FICTICIOS:
        assert marcador in texto, f"Falta el marcador {marcador!r} en el PDF"


def test_generador_produce_pdf_valido():
    from app.services.presupuesto_muestra import construir

    datos = construir()
    assert datos.startswith(b"%PDF")
    texto = _texto(datos)
    for marcador in MARCADORES_FICTICIOS:
        assert marcador in texto, f"Falta el marcador {marcador!r} en el PDF generado"


def test_muestra_usa_solo_datos_ficticios():
    """La fuente de la muestra no contiene ningún dato personal real."""
    from app.services import presupuesto_muestra as m

    assert m.EMPRESA_RIF == "J-00000000-0"
    assert m.EMPRESA_EMAIL.endswith("@ejemplo.com")
    assert m.EMPRESA_WEB.endswith("ejemplo.com")
    assert m.CLIENTE_NOMBRE == "Familia Rodríguez"
    # El documento declara explícitamente que todo es ficticio.
    assert "ficticios" in m.NOTA_ILUSTRATIVA


def test_landing_enlaza_el_pdf_de_ejemplo():
    with TestClient(app) as client:
        r = client.get("/conocer")
    assert r.status_code == 200
    assert "/static/pdf/presupuesto-ejemplo.pdf" in r.text


def test_pdf_de_ejemplo_se_sirve_como_pdf():
    with TestClient(app) as client:
        r = client.get("/static/pdf/presupuesto-ejemplo.pdf")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content.startswith(b"%PDF")


# ---------------------------------------------------------------------------
# El ejemplo en inglés (mismo presupuesto, otra redacción)
# ---------------------------------------------------------------------------

RUTA_PDF_EN = RUTA_PDF.with_name("presupuesto-ejemplo-en.pdf")

# Los nombres propios y los códigos no se traducen, así que deben estar en los
# dos idiomas. La nota que declara que todo es ficticio sí cambia de lengua y
# se comprueba aparte.
MARCADORES_FICTICIOS_NEUTROS = tuple(
    m for m in MARCADORES_FICTICIOS if m not in ("Documento de muestra", "ficticios")
)

MARCADORES_EN = (
    "PRELIMINARIES AND DEMOLITION",
    "Full apartment refurbishment",
    "Demolition of internal partitions",
    "Quartz worktop",
    "Sample document generated with CotizaT",
)


def _cadenas_de_la_muestra() -> set[str]:
    """Todo el texto redactado que compone la muestra en castellano."""
    from app.services import presupuesto_muestra as m

    cliente = m._cliente()
    config = m._configuracion()
    presupuesto = m._presupuesto(cliente)
    textos: set[str] = set()
    pila = [presupuesto, cliente, config]
    vistos: set[int] = set()
    while pila:
        obj = pila.pop()
        if obj is None or id(obj) in vistos:
            continue
        vistos.add(id(obj))
        for campo in m._CAMPOS_TEXTO.get(type(obj).__name__, ()):
            valor = getattr(obj, campo, None) or ""
            if valor:
                textos.add(valor)
        for relacion in ("capitulos", "partidas", "mediciones"):
            hijos = getattr(obj, relacion, None)
            if hijos is not None:
                pila.extend(hijos)
    return textos


def test_muestra_en_ingles_es_un_pdf_valido_y_ficticio():
    assert RUTA_PDF_EN.exists(), "Falta el PDF de ejemplo en inglés; regenera con tools/generar_presupuesto_muestra.py"
    datos = RUTA_PDF_EN.read_bytes()
    assert datos.startswith(b"%PDF")
    assert len(datos) > 20_000
    texto = _texto(datos)
    for marcador in MARCADORES_EN:
        assert marcador in texto, f"Falta {marcador!r} en el PDF en inglés"
    # Sigue siendo un documento de muestra: ni un dato real.
    for marcador in MARCADORES_FICTICIOS_NEUTROS:
        assert marcador in texto, f"Falta el marcador {marcador!r} en el PDF en inglés"
    for marcador in ("Sample document generated", "fictitious"):
        assert marcador in texto, f"Falta la nota de muestra en inglés: {marcador!r}"
    # Y no se ha colado nada en castellano.
    for resto in ("Remodelación integral de apartamento", "MUROS Y PARTICIONES",
                  "Encimera de cuarzo", "Forma de pago"):
        assert resto not in texto, f"Queda texto en castellano: {resto!r}"


def test_la_muestra_en_ingles_no_deja_texto_sin_traducir():
    from app.services import presupuesto_muestra as m

    huecos = m._traducir(m._presupuesto(m._cliente()), m._cliente(),
                         m._configuracion(), en=True)
    assert huecos == [], "Textos sin traducir en la muestra: " + "; ".join(huecos)
    # construir() también lo comprueba: un hueco sería un error, no un aviso.
    assert m.construir("en").startswith(b"%PDF")


def test_toda_traduccion_de_la_muestra_se_usa():
    """Ninguna entrada de `_TEXTO_EN` es un texto que ya no esté en la muestra."""
    from app.services import presupuesto_muestra as m

    usados = _cadenas_de_la_muestra()
    muertos = [c for c in m._TEXTO_EN if c not in usados]
    assert not muertos, f"Entradas sin uso en _TEXTO_EN: {muertos}"


def test_los_dos_idiomas_muestran_el_mismo_importe():
    """La traducción cambia la redacción, nunca los números."""
    import re

    def total(ruta):
        texto = _texto(ruta.read_bytes())
        m = re.search(r"(?:PRESUPUESTO TOTAL|ESTIMATE TOTAL)\s*\n?\s*([\d.,]+)", texto)
        assert m, f"No se encuentra el total en {ruta.name}"
        crudo = m.group(1)
        # Español: 40.648,31 · Inglés: 40,648.31
        return float(crudo.replace(".", "").replace(",", ".")) if crudo.count(",") == 1 and crudo.rindex(",") > crudo.rindex(".") else float(crudo.replace(",", ""))

    assert total(RUTA_PDF) == total(RUTA_PDF_EN)


def test_importes_y_fechas_con_el_formato_del_idioma():
    """Un cliente en inglés no puede recibir «35.041,65» ni «15/08/2026»."""
    es = _texto(RUTA_PDF.read_bytes())
    en = _texto(RUTA_PDF_EN.read_bytes())
    assert "35.041,65 USD" in es and "35,041.65 USD" not in es
    assert "35,041.65 USD" in en and "35.041,65 USD" not in en
    assert "15/08/2026" in es
    assert "08/15/2026" in en


def test_landing_en_enlaza_el_pdf_en_ingles():
    with TestClient(app) as client:
        r = client.get("/en/")
    assert r.status_code == 200
    assert "presupuesto-ejemplo-en.pdf" in r.text
    assert 'href="/static/pdf/presupuesto-ejemplo.pdf"' not in r.text


def test_pdf_ejemplo_en_se_sirve_como_pdf():
    with TestClient(app) as client:
        r = client.get("/static/pdf/presupuesto-ejemplo-en.pdf")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content.startswith(b"%PDF")
