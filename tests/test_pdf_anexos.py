"""Los anexos PDF se incorporan como páginas del presupuesto.

Antes, marcar «incluir anexos» solo imprimía una lista de nombres: el cliente
veía documentos citados que no recibía. Estas pruebas fijan el comportamiento
nuevo (fusión real + índice explicativo) y sus dos degradaciones: anexo
ilegible y tope de tamaño impuesto por el límite de respuesta de Vercel.
"""
import io
import json
import random
import string
from datetime import date

import pytest
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from app.models import (
    AnexoPresupuesto,
    Capitulo,
    Cliente,
    Configuracion,
    Presupuesto,
    PresupuestoItem,
)
from app.services import pdf as pdf_service
from app.services import pdf_anexos


def _pdf_de_prueba(paginas: int, texto: str = "ANEXO", relleno: int = 0) -> bytes:
    """PDF sintético; ``relleno`` añade líneas de texto para engordarlo."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    if relleno:
        c.setPageCompression(0)
    generador = random.Random(20260814)
    for numero in range(1, paginas + 1):
        c.setFont("Helvetica", 24)
        c.drawString(80, 700, f"{texto} pagina {numero}")
        c.setFont("Helvetica", 5)
        for fila in range(relleno):
            linea = "".join(generador.choice(string.ascii_letters) for _ in range(200))
            c.drawString(15, 15 + (fila % 115) * 5.7, linea)
        c.showPage()
    c.save()
    return buf.getvalue()


def _presupuesto(anexos, incluir=True):
    cliente = Cliente(nombre="Cliente de prueba", rif="J-12345678")
    presupuesto = Presupuesto(
        numero="P-2026-042",
        titulo="Reforma con anexos",
        fecha=date(2026, 8, 14),
        moneda="USD",
        estado="borrador",
        impuesto_pct=16.0,
        cliente=cliente,
        incluir_anexos=incluir,
    )
    cap = Capitulo(nombre="ALBAÑILERÍA", orden=1)
    cap.partidas = [
        PresupuestoItem(
            nombre="Tabique de bloque",
            unidad="m2",
            cantidad=25.0,
            precio_unitario=42.0,
        )
    ]
    presupuesto.capitulos = [cap]
    presupuesto.anexos = [
        AnexoPresupuesto(nombre=nombre, archivo=referencia)
        for nombre, referencia in anexos
    ]
    return presupuesto


def _config():
    return Configuracion(empresa_nombre="Constructora de prueba", pdf_color="#0F4C81")


def _texto_pdf(datos: bytes) -> str:
    return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(datos)).pages)


@pytest.fixture
def almacen(monkeypatch):
    """Sustituye el almacenamiento por un diccionario en memoria."""
    contenido: dict[str, bytes] = {}

    def _read(referencia):
        from app.storage import StorageError

        if referencia not in contenido:
            raise StorageError("El archivo solicitado no existe.")
        return contenido[referencia]

    monkeypatch.setattr(pdf_anexos, "read_reference", _read)
    return contenido


def test_los_anexos_se_incorporan_como_paginas_finales(almacen):
    almacen["storage://a/plano.pdf"] = _pdf_de_prueba(2, "PLANO")
    almacen["storage://a/ficha.pdf"] = _pdf_de_prueba(1, "FICHA")
    presupuesto = _presupuesto(
        [("Plano de planta", "storage://a/plano.pdf"),
         ("Ficha técnica", "storage://a/ficha.pdf")]
    )

    solo = pdf_service.generar_pdf(_presupuesto([]), _config()).getvalue()
    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()

    paginas_base = len(PdfReader(io.BytesIO(solo)).pages)
    lector = PdfReader(io.BytesIO(datos))
    assert len(lector.pages) == paginas_base + 3

    texto = _texto_pdf(datos)
    assert "PLANO pagina 1" in texto
    assert "PLANO pagina 2" in texto
    assert "FICHA pagina 1" in texto


def test_el_indice_explica_como_se_entregan_y_en_que_pagina(almacen):
    almacen["storage://a/plano.pdf"] = _pdf_de_prueba(2, "PLANO")
    presupuesto = _presupuesto([("Plano de planta", "storage://a/plano.pdf")])

    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()
    lector = PdfReader(io.BytesIO(datos))
    texto = "\n".join(p.extract_text() or "" for p in lector.pages)

    assert "Anexos incluidos" in texto
    assert "dentro de este mismo archivo" in texto
    assert "Anexo 1" in texto and "Plano de planta" in texto

    # La página anunciada es la real: allí empieza el anexo.
    inicio = len(lector.pages) - 2 + 1
    assert f"desde la página {inicio}" in texto
    assert "PLANO pagina 1" in (lector.pages[inicio - 1].extract_text() or "")


def test_el_pie_de_pagina_cuenta_el_archivo_completo(almacen):
    """«n/N» debe contar también las páginas de los anexos fusionados."""
    almacen["storage://a/plano.pdf"] = _pdf_de_prueba(3, "PLANO")
    presupuesto = _presupuesto([("Plano de planta", "storage://a/plano.pdf")])

    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()
    lector = PdfReader(io.BytesIO(datos))
    total = len(lector.pages)

    assert f"1/{total}" in (lector.pages[0].extract_text() or "")


def test_un_anexo_ilegible_no_rompe_la_descarga(almacen):
    almacen["storage://a/roto.pdf"] = b"%PDF-1.4 esto no es un PDF valido"
    almacen["storage://a/bueno.pdf"] = _pdf_de_prueba(1, "BUENO")
    presupuesto = _presupuesto(
        [("Documento dañado", "storage://a/roto.pdf"),
         ("Documento bueno", "storage://a/bueno.pdf")]
    )

    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()
    texto = _texto_pdf(datos)

    assert datos.startswith(b"%PDF")
    assert "BUENO pagina 1" in texto
    assert "Documento dañado" in texto
    assert "archivo independiente" in texto


def test_un_anexo_ausente_del_almacenamiento_se_anuncia_aparte(almacen):
    presupuesto = _presupuesto([("Plano perdido", "storage://a/no-existe.pdf")])

    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()
    texto = _texto_pdf(datos)

    assert "Plano perdido" in texto
    assert "archivos independientes" in texto or "archivo independiente" in texto


def test_no_se_supera_el_limite_de_respuesta_de_vercel(almacen, monkeypatch):
    """Un anexo que no cabe se anuncia aparte en lugar de romper la descarga."""
    almacen["storage://a/ligero.pdf"] = _pdf_de_prueba(1, "LIGERO")
    almacen["storage://a/pesado.pdf"] = _pdf_de_prueba(4, "PESADO", relleno=140)
    ligero = len(almacen["storage://a/ligero.pdf"])
    pesado = len(almacen["storage://a/pesado.pdf"])
    assert pesado > ligero * 4

    base = len(pdf_service.generar_pdf(_presupuesto([]), _config()).getvalue())
    # Presupuesto de sobra para el anexo ligero, insuficiente para el pesado.
    tope = base + ligero * 3 + 30_000
    monkeypatch.setattr(pdf_anexos, "LIMITE_TOTAL_BYTES", tope)
    monkeypatch.setattr(pdf_anexos, "LIMITE_DURO_BYTES", tope + 40_000)

    presupuesto = _presupuesto(
        [("Catálogo pesado", "storage://a/pesado.pdf"),
         ("Ficha ligera", "storage://a/ligero.pdf")]
    )
    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()
    texto = _texto_pdf(datos)

    assert len(datos) <= tope + 40_000
    assert "PESADO pagina 1" not in texto
    assert "LIGERO pagina 1" in texto
    assert "tamaño máximo de este PDF" in texto


def test_sin_marcar_la_opcion_el_pdf_no_cambia(almacen):
    almacen["storage://a/plano.pdf"] = _pdf_de_prueba(2, "PLANO")
    presupuesto = _presupuesto(
        [("Plano de planta", "storage://a/plano.pdf")], incluir=False
    )

    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()
    texto = _texto_pdf(datos)

    assert "Anexos incluidos" not in texto
    assert "PLANO pagina 1" not in texto


def test_recorrido_http_subir_anexo_y_descargar_el_pdf_con_sus_paginas():
    """Recorrido real: subir el anexo, marcar la casilla y descargar el PDF."""
    from fastapi.testclient import TestClient

    from app.main import app

    estructura = [{
        "nombre": "CAPÍTULO CON ANEXOS",
        "partidas": [{
            "partida_id": "", "nombre": "Partida con anexo", "descripcion": "",
            "unidad": "m2", "cantidad": 5, "precio": 30.0,
            "tipo_partida": "included", "seleccionada": True,
        }],
    }]
    comun = {
        "client_id": "1", "titulo": "Presupuesto con anexos",
        "fecha": date.today().isoformat(), "validez_dias": "30",
        "moneda": "USD", "impuesto_pct": "16", "descuento_pct": "0",
        "estado": "borrador", "estructura_json": json.dumps(estructura),
    }
    with TestClient(app) as client:
        creado = client.post("/presupuestos/nuevo", data=comun, follow_redirects=False)
        assert creado.status_code == 303
        pid = creado.headers["location"].split("?")[0].split("/")[-1]

        subida = client.post(
            f"/presupuestos/{pid}/anexos",
            data={"nombre": "Memoria de calidades"},
            files={"archivo": ("memoria.pdf", _pdf_de_prueba(2, "MEMORIA"),
                               "application/pdf")},
            follow_redirects=False,
        )
        assert subida.status_code == 303

        sin_marcar = client.get(f"/presupuestos/{pid}/pdf")
        assert sin_marcar.status_code == 200
        assert "MEMORIA pagina 1" not in _texto_pdf(sin_marcar.content)

        marcado = client.post(
            f"/presupuestos/{pid}/editar",
            data={**comun, "incluir_anexos": "1"},
            follow_redirects=False,
        )
        assert marcado.status_code == 303

        descarga = client.get(f"/presupuestos/{pid}/pdf")
        assert descarga.status_code == 200
        assert descarga.headers["content-type"] == "application/pdf"
        # Bajo el tope de 4,5 MB que impone la respuesta de una función Vercel.
        assert len(descarga.content) < pdf_anexos.LIMITE_DURO_BYTES
        texto = _texto_pdf(descarga.content)
        assert "MEMORIA pagina 1" in texto and "MEMORIA pagina 2" in texto
        assert "Memoria de calidades" in texto
        assert "dentro de este mismo archivo" in texto


def test_la_fusion_no_arrastra_javascript_del_anexo(almacen):
    """Un anexo con acciones JavaScript no inyecta código en el presupuesto."""
    base = _pdf_de_prueba(1, "CONJS")
    escritor = PdfWriter(clone_from=io.BytesIO(base))
    escritor.add_js("app.alert('anexo');")
    escritor.add_annotation(
        page_number=0,
        annotation={
            "/Type": "/Annot",
            "/Subtype": "/Link",
            "/Rect": [10, 10, 100, 40],
            "/A": {"/S": "/JavaScript", "/JS": "app.alert('clic');"},
        },
    )
    salida = io.BytesIO()
    escritor.write(salida)
    almacen["storage://a/js.pdf"] = salida.getvalue()

    presupuesto = _presupuesto([("Anexo con macro", "storage://a/js.pdf")])
    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()

    assert "CONJS pagina 1" in _texto_pdf(datos)
    assert b"app.alert" not in datos


def test_el_pdf_interactivo_conserva_su_formulario_al_fusionar(almacen):
    """La fusión no puede desactivar el recálculo del PDF interactivo."""
    from app.models import PresupuestoItemProducto

    almacen["storage://a/plano.pdf"] = _pdf_de_prueba(1, "PLANO")
    presupuesto = _presupuesto([("Plano", "storage://a/plano.pdf")])
    partida = presupuesto.capitulos[0].partidas[0]
    partida.productos_opciones = [
        PresupuestoItemProducto(nombre="Bloque liso", precio=10.0, unidad="m2",
                                seleccionado=True),
        PresupuestoItemProducto(nombre="Bloque visto", precio=18.0, unidad="m2"),
    ]

    datos = pdf_service.generar_pdf(presupuesto, _config()).getvalue()

    lector = PdfReader(io.BytesIO(datos))
    campos = lector.get_fields() or {}
    for campo in ("sel_p1", "pu_p1", "imp_p1", "cap_c1", "tot_total"):
        assert campo in campos, campo
    raiz = lector.trailer["/Root"]
    formulario = raiz["/AcroForm"].get_object()
    assert bool(formulario.get("/NeedAppearances"))
    assert len(formulario["/CO"]) >= 1          # orden de recálculo intacto
    assert "/JavaScript" in raiz["/Names"].get_object()
    assert "PLANO pagina 1" in _texto_pdf(datos)
