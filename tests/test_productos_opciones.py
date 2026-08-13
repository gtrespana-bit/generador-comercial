import io
from pathlib import Path
from datetime import date
import pytest
from app.models import Presupuesto, Capitulo, PresupuestoItem, PresupuestoItemProducto, Cliente, Configuracion
from app.services.pdf import generar_pdf
from app.services.pdf_interactivo import ContextoInteractivo


def test_productos_multiples_property():
    item = PresupuestoItem(
        nombre="Solado de porcelanato",
        unidad="m2",
        cantidad=50.0,
        precio_unitario=65.0,
        producto_nombre="Porcelanato Calacatta",
        producto_precio=25.0,
        producto_imagen="uploads/products/calacatta.jpg",
    )
    op1 = PresupuestoItemProducto(
        nombre="Porcelanato Calacatta",
        precio=25.0,
        unidad="m2",
        marca="Porcelanosa",
        modelo="Calacatta",
        color="Blanco",
        acabado="Pulido",
        imagen="uploads/products/calacatta.jpg",
        seleccionado=True,
    )
    op2 = PresupuestoItemProducto(
        nombre="Porcelanato Marquina",
        precio=35.0,
        unidad="m2",
        marca="Porcelanosa",
        modelo="Marquina",
        color="Negro",
        acabado="Mate",
        imagen="uploads/products/marquina.jpg",
        seleccionado=False,
    )
    item.productos_opciones = [op1, op2]

    multiples = item.productos_multiples
    assert len(multiples) == 2
    assert item.indice_producto_elegido == 0
    assert item.tiene_producto is True

    # Test clearing options and product fields
    item.producto_nombre = ""
    item.producto_precio = None
    item.producto_imagen = ""
    item.productos_opciones = []
    assert item.tiene_producto is False
    assert len(item.productos_multiples) == 1  # Returns [self] fallback


def test_pdf_generation_con_multiples_productos(tmp_path):
    cliente = Cliente(nombre="Cliente de Lujo", rif="J-12345678")
    presupuesto = Presupuesto(
        numero="P-2026-999",
        titulo="Residencia de Lujo - Reforma Integral",
        fecha=date(2026, 8, 12),
        moneda="USD",
        estado="borrador",
        impuesto_pct=16.0,
        descuento_pct=0.0,
        gastos_indirectos_pct=0.0,
        imprevistos_pct=0.0,
        transporte_monto=0.0,
        otros_cargos_monto=0.0,
        cliente=cliente,
    )
    cap = Capitulo(nombre="PAVIMENTOS Y REVESTIMIENTOS", orden=1)
    item = PresupuestoItem(
        nombre="Solado de gran formato 120x120 cm",
        descripcion="Suministro e instalación de pavimento porcelánico de gran formato sobre mortero de agarre.",
        unidad="m2",
        cantidad=120.0,
        precio_unitario=85.0,
        producto_nombre="Porcelanato Statuario Gold",
        producto_precio=35.0,
        producto_unidad="m2",
        producto_imagen="uploads/products/statuario.jpg",
    )
    op1 = PresupuestoItemProducto(
        nombre="Porcelanato Statuario Gold 120x120",
        precio=35.0,
        unidad="m2",
        marca="Porcelanosa",
        modelo="Statuario Gold",
        color="Blanco / Dorado",
        acabado="Pulido Alto Brillo",
        descripcion="Acabado pulido con veteado dorado de alta definición.",
        imagen="uploads/products/statuario.jpg",
        seleccionado=True,
    )
    op2 = PresupuestoItemProducto(
        nombre="Porcelanato Sahara Noir 120x120",
        precio=45.0,
        unidad="m2",
        marca="Inalco",
        modelo="Sahara Noir",
        color="Negro Veteado",
        acabado="Satinado Silk",
        descripcion="Elegante acabado en mármol negro con betas doradas.",
        imagen="uploads/products/sahara.jpg",
        seleccionado=False,
    )
    item.productos_opciones = [op1, op2]
    cap.partidas = [item]
    presupuesto.capitulos = [cap]

    cfg = Configuracion(empresa_nombre="Constructora de Lujo S.A.", pdf_color="#0F4C81")

    # Generar PDF
    pdf_buf = generar_pdf(presupuesto, cfg)
    assert pdf_buf is not None
    pdf_bytes = pdf_buf.getvalue()
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_sin_acroform_button_no_rompe(monkeypatch):
    """Regresión: ReportLab 4.0/4.1 no tiene AcroForm.button.

    El PDF interactivo con varias opciones de producto no debe fallar
    (AttributeError) al cubrir la tarjeta con el hit-area.
    """
    from reportlab.pdfbase import acroform as acro

    if hasattr(acro.AcroForm, "button"):
        monkeypatch.delattr(acro.AcroForm, "button")
    assert not hasattr(acro.AcroForm, "button")

    cliente = Cliente(nombre="Cliente ReportLab antiguo")
    presupuesto = Presupuesto(
        numero="P-2026-003",
        titulo="Reforma con opciones",
        fecha=date(2026, 8, 12),
        moneda="USD",
        estado="borrador",
        impuesto_pct=16.0,
        cliente=cliente,
    )
    cap = Capitulo(nombre="PAVIMENTOS", orden=1)
    item = PresupuestoItem(
        nombre="Solado de porcelanato",
        unidad="m2",
        cantidad=10.0,
        precio_unitario=98.0,
        producto_nombre="Porcelanato Calacatta",
        producto_precio=68.0,
        producto_unidad="m2",
    )
    item.productos_opciones = [
        PresupuestoItemProducto(nombre="Porcelanato Calacatta", precio=68.0, unidad="m2", seleccionado=True, orden=0),
        PresupuestoItemProducto(nombre="Marquina 60x120", precio=92.0, unidad="m2", seleccionado=False, orden=1),
    ]
    cap.partidas = [item]
    presupuesto.capitulos = [cap]
    cfg = Configuracion(empresa_nombre="Test SL")

    pdf_bytes = generar_pdf(presupuesto, cfg).getvalue()
    assert pdf_bytes.startswith(b"%PDF")
    assert b"sel_p1" in pdf_bytes
    assert b"hit_sel_p1" in pdf_bytes


def test_contexto_interactivo_con_opciones():
    presupuesto = Presupuesto(
        numero="P-2026-998",
        moneda="USD",
    )
    cap = Capitulo(nombre="BANOS", orden=1)
    item = PresupuestoItem(
        nombre="Grifería monomando para lavabo",
        unidad="ud",
        cantidad=4.0,
        precio_unitario=150.0,
        producto_nombre="Monomando Cromo",
        producto_precio=50.0,
    )
    op1 = PresupuestoItemProducto(nombre="Monomando Cromo", precio=50.0, seleccionado=True)
    op2 = PresupuestoItemProducto(nombre="Monomando Negro Mate", precio=85.0, seleccionado=False)
    item.productos_opciones = [op1, op2]
    cap.partidas = [item]
    presupuesto.capitulos = [cap]

    from reportlab.lib import colors
    ctx = ContextoInteractivo(presupuesto, "USD", colors.black, colors.HexColor("#0F4C81"))
    assert ctx.preparar() is True
    pid = ctx.id_partida(item)
    assert pid in ctx.partidas
    assert len(ctx.partidas[pid]["precios"]) == 2
