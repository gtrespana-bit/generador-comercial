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
