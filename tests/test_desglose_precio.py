"""Desglose del precio en el PDF: productos elegidos frente a mano de obra.

La función comercial prometida es un **reparto del precio de venta**: de la
base imponible, una parte corresponde a los productos y materiales elegidos y
el resto a la mano de obra, los recursos y la ejecución de los trabajos. Nunca
se revela el coste interno ni el margen. Estas pruebas fijan las tres reglas
que no deben romperse:

* las dos cifras suman exactamente la base imponible (el céntimo lo absorbe la
  obra);
* sin la casilla marcada el PDF sale como siempre, sin ninguna fila nueva;
* el reparto es de venta (con el descuento ya prorrateado), no de coste.
"""
import io
from datetime import date

from pypdf import PdfReader

from app.models import (
    Capitulo,
    Cliente,
    Configuracion,
    Presupuesto,
    PresupuestoItem,
    PresupuestoItemProducto,
)
from app.services.calculations import D, calcular_totales
from app.services.pdf import generar_pdf
from app.services.pdf_interactivo import ContextoInteractivo


def _presupuesto(desglose=False, descuento=5.0, indirectos=0.0, interactivo=True):
    cliente = Cliente(nombre="Cliente de prueba", rif="J-00000000-0")
    p = Presupuesto(
        numero="P-DESGLOSE-1",
        titulo="Reforma con producto elegido",
        fecha=date(2026, 1, 15),
        moneda="USD",
        estado="borrador",
        impuesto_pct=16.0,
        descuento_pct=descuento,
        gastos_indirectos_pct=indirectos,
        mostrar_resumen_capitulos=False,
        mostrar_desglose_precio=desglose,
        cliente=cliente,
    )
    cap = Capitulo(nombre="PAVIMENTOS", orden=1)
    partida = PresupuestoItem(
        nombre="Solado de porcelanato",
        unidad="m2",
        cantidad=10.0,
        precio_unitario=50.0,
        producto_nombre="Porcelanato blanco",
        producto_precio=12.0,
        producto_coste=9.0,
    )
    if interactivo:
        partida.productos_opciones = [
            PresupuestoItemProducto(nombre="Porcelanato blanco", precio=12.0, seleccionado=True),
            PresupuestoItemProducto(nombre="Porcelanato negro", precio=30.0, seleccionado=False),
        ]
    cap.partidas = [partida]
    p.capitulos = [cap]
    return p, cap, partida


def _texto(pdf_buf) -> str:
    lector = PdfReader(io.BytesIO(pdf_buf.getvalue()))
    return "\n".join((pagina.extract_text() or "") for pagina in lector.pages)


def test_el_reparto_suma_exactamente_la_base_imponible():
    p, _, _ = _presupuesto(desglose=True, descuento=7.5, indirectos=2.5)

    totales = calcular_totales(p)
    productos, obra = p.desglose_precio

    assert D(productos) + D(obra) == D(totales.base)
    assert D(productos) == D(totales.base_productos)
    assert D(obra) == D(totales.base) - D(totales.base_productos)


def test_el_reparto_es_de_venta_no_de_coste():
    """La cifra de productos es la de venta (descontada), nunca el coste."""
    p, _, _ = _presupuesto(desglose=True, descuento=5.0)

    totales = calcular_totales(p)
    productos, _ = p.desglose_precio

    # 10 m2 × 12 USD = 120 USD de producto, menos su parte del 5 % de descuento.
    assert totales.total_productos == D("120")
    assert D(productos) == D("114")
    assert D(productos) != D(totales.coste_productos)


def test_sin_productos_todo_el_precio_es_mano_de_obra():
    p, _, partida = _presupuesto(desglose=True)
    partida.producto_nombre = ""
    partida.producto_precio = None
    partida.productos_opciones = []

    totales = calcular_totales(p)
    productos, obra = p.desglose_precio

    assert D(productos) == D("0")
    assert D(obra) == D(totales.base)


def test_el_pdf_muestra_el_desglose_solo_con_la_casilla():
    cfg = Configuracion(empresa_nombre="Constructora de prueba", pdf_color="#0F4C81")
    # Sin alternativas de producto el PDF es estático: las cifras son texto.
    apagado = _texto(generar_pdf(_presupuesto(desglose=False, interactivo=False)[0], cfg))
    assert "Productos y materiales" not in apagado
    assert "Mano de obra" not in apagado

    encendido = _texto(generar_pdf(_presupuesto(desglose=True, interactivo=False)[0], cfg))
    assert "Productos y materiales seleccionados" in encendido
    assert "Mano de obra, recursos y" in encendido
    # Las cifras del reparto, con su porcentaje sobre la base imponible.
    assert "114,00 USD" in encendido and "(24,0 %)" in encendido
    assert "361,00 USD" in encendido and "(76,0 %)" in encendido
    # La nota explica que el reparto es sobre la base imponible, no el coste.
    assert "reparte la base imponible" in encendido


def test_el_pdf_interactivo_recalcula_el_desglose_con_el_producto_elegido():
    from reportlab.lib import colors

    p, _, _ = _presupuesto(desglose=True)
    ctx = ContextoInteractivo(
        p, "USD", colors.HexColor("#333333"), colors.HexColor("#0F4C81")
    )
    assert ctx.preparar() is True

    totales = ctx.totales()
    assert round(totales["productos"] + totales["obra"], 2) == totales["base"]
    # 10 m2 × 12 USD de producto con su parte del 5 % de descuento → 114.
    assert ctx.txt_desglose("productos").startswith("114,00 USD")
    assert "(24,0 %)" in ctx.txt_desglose("productos")
    assert ctx.txt_desglose("obra").startswith("361,00 USD")

    # El formulario lleva el campo y su fórmula de recálculo.
    assert "event.value = DESG_TXT(\"productos\");" == ctx.js_desglose("productos")


def test_las_filas_del_desglose_son_campos_recalculables_del_formulario():
    """Con alternativas, las dos filas son campos que se recalculan solos."""
    p, _, _ = _presupuesto(desglose=True)
    buf = generar_pdf(p, Configuracion(empresa_nombre="Obra", pdf_color="#0F4C81"))
    datos = buf.getvalue()

    assert b"desg_productos" in datos and b"desg_obra" in datos
    assert b"DESG_TXT" in datos

    campos = PdfReader(io.BytesIO(datos)).get_fields() or {}
    assert campos["desg_productos"]["/V"] == "114,00 USD  (24,0 %)"
    assert campos["desg_obra"]["/V"] == "361,00 USD  (76,0 %)"
    # Y las etiquetas siguen siendo texto, para cualquier visor.
    texto = _texto(buf)
    assert "Productos y materiales seleccionados" in texto
    assert "Mano de obra, recursos y ejecución de los trabajos" in texto


def test_el_js_del_pdf_interactivo_calcula_igual_que_python(monkeypatch):
    """La misma base, el mismo reparto: Python y el JavaScript del PDF.

    El PDF interactivo recalcula dentro del visor con ``_PLANTILLA_JS``; si
    esa copia del cálculo se separase de ``ContextoInteractivo``, el cliente
    vería una cifra al recibir el documento y otra al cambiar de producto.
    Se ejecuta el propio JavaScript (node) con la selección de producto
    indicada por el campo del formulario.
    """
    import json
    import shutil
    import subprocess

    if shutil.which("node") is None:  # pragma: no cover - depende del entorno
        pytest.skip("node no está disponible")

    def valores_del_js(ctx, seleccion, claves_tot, claves_desg):
        cuerpo = "".join(f'salida.tot["{c}"] = TOT_TXT("{c}");\n' for c in claves_tot)
        cuerpo += "".join(f'salida.desg["{c}"] = DESG_TXT("{c}");\n' for c in claves_desg)
        script = ctx.script_documento() + (
            "\nglobalThis.getField = function (nombre) { return { value: \"__SEL__\" }; };\n"
            "var salida = { tot: {}, desg: {} };\n__CUERPO__\n"
            "console.log(JSON.stringify(salida));\n"
        ).replace("__SEL__", str(seleccion)).replace("__CUERPO__", cuerpo)
        salida = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, timeout=60
        )
        assert salida.returncode == 0, salida.stderr
        return json.loads(salida.stdout.strip().splitlines()[-1])

    from reportlab.lib import colors

    claves_tot = ("subtotal", "adicionales", "descuento", "base", "impuesto", "total")
    claves_desg = ("productos", "obra")
    for seleccion in (0, 1):
        p, _, _ = _presupuesto(desglose=True, descuento=7.5, indirectos=2.5)
        ctx = ContextoInteractivo(
            p, "USD", colors.HexColor("#333333"), colors.HexColor("#0F4C81")
        )
        assert ctx.preparar() is True
        for datos in ctx.partidas.values():
            datos["elegido"] = seleccion
        js = valores_del_js(ctx, seleccion, claves_tot, claves_desg)

        for clave in claves_tot:
            assert ctx.txt_total(clave) == js["tot"][clave], clave
        for clave in claves_desg:
            assert ctx.txt_desglose(clave) == js["desg"][clave], clave
        totales = ctx.totales()
        assert round(totales["productos"] + totales["obra"], 2) == totales["base"]
