"""Sales tax estadounidense por estado (Fase 2 de EE. UU.).

El peligro que estos tests vigilan es el que el análisis señaló: aplicar un
porcentaje sobre el total como si fuera un IVA. En la mayoría de los estados
el contratista no cobra «sales tax» al cliente en una reforma, así que el
total de un presupuesto de Texas o Florida no puede llevar un impuesto
fantasma; y donde el impuesto existe, su base puede ser solo materiales,
solo mano de obra o una fracción de los ingresos brutos (Arizona, 65 %).

También se vigila lo contrario: sin modo elegido, un documento
estadounidense anterior al motor sigue calculando como siempre, y ningún
otro mercado hereda reglas de este módulo.

Importes en dólares, con dos decimales exactos.
"""
from __future__ import annotations

import io
import json
from datetime import date
from decimal import Decimal

import pytest
from pypdf import PdfReader

from app.services.calculations import calcular_totales
from app.services.fiscalidad_eeuu import (
    BASES_US,
    CODIGOS_ESTADO_EEUU,
    ESTADOS_EEUU,
    base_gravada_eeuu,
    calcular_fiscalidad_eeuu,
    estado_por_codigo,
    estimar_venta_materiales,
)

from app.models import Cliente, Configuracion


def _f(**kw):
    base = dict(
        pais_codigo="US",
        base_imponible=Decimal("10000"),
        venta_materiales=Decimal("5500"),
        tipo_pct=Decimal("8.20"),
        us_tax_base="full",
        estado_codigo="TX",
        us_tax_fraccion=Decimal("1"),
    )
    base.update(kw)
    return calcular_fiscalidad_eeuu(**base)


# ─────────────────────────────────────────────────────────────────────────────
# Solo rige en EE. UU. y solo con modo elegido
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pais", ["GB", "IE", "AU", "CA", "VE", "ES", "", None])
def test_fuera_de_eeuu_no_se_aplica_nada(pais):
    f = _f(pais_codigo=pais, us_tax_base="none")
    assert f.aplica is False
    assert f.impuesto_importe == Decimal("0")
    assert f.leyenda == ""
    assert f.avisos == ()


@pytest.mark.parametrize("modo", ["", None, "inventado"])
def test_sin_modo_el_documento_queda_como_estaba(modo):
    """Documentos anteriores al motor: ni se enteran de que existe."""
    assert _f(us_tax_base=modo).aplica is False


# ─────────────────────────────────────────────────────────────────────────────
# Los cinco modos sobre la misma base
# ─────────────────────────────────────────────────────────────────────────────

def test_none_no_cobra_impuesto_al_cliente():
    f = _f(us_tax_base="none")
    assert f.base_gravada == Decimal("0")
    assert f.impuesto_importe == Decimal("0.00")
    assert f.total_a_cobrar == Decimal("10000.00")
    assert f.sin_impuesto_al_cliente is True
    assert "No sales tax is charged on this contract" in f.leyenda


def test_materials_grava_solo_el_precio_de_los_materiales():
    f = _f(us_tax_base="materials")
    assert f.base_gravada == Decimal("5500.00")
    assert f.impuesto_importe == Decimal("451.00")   # 8,2 % de 5 500
    assert f.total_a_cobrar == Decimal("10451.00")
    assert "materials only" in f.leyenda and "TX" in f.leyenda


def test_labor_grava_el_resto():
    f = _f(us_tax_base="labor")
    assert f.base_gravada == Decimal("4500.00")
    assert f.impuesto_importe == Decimal("369.00")
    assert "labor only" in f.leyenda


def test_full_grava_materiales_y_mano_de_obra():
    f = _f(us_tax_base="full", estado_codigo="WA", tipo_pct=Decimal("9.57"))
    assert f.base_gravada == Decimal("10000.00")
    assert f.impuesto_importe == Decimal("957.00")


def test_gross_receipts_arizona_grava_el_65_por_ciento():
    f = _f(us_tax_base="gross_receipts", estado_codigo="AZ",
           tipo_pct=Decimal("8.54"), us_tax_fraccion=Decimal("0.65"))
    assert f.base_gravada == Decimal("6500.00")
    assert f.impuesto_importe == Decimal("555.10")
    assert "65% of the contract amount" in f.leyenda
    assert f.nombre_impuesto == "Transaction privilege tax"


def test_la_base_gravada_congelada_manda_sobre_el_reparto():
    """La factura no recalcula: hereda la base que el presupuesto calculó."""
    f = _f(us_tax_base="materials", base_gravada=Decimal("4000"))
    assert f.base_gravada == Decimal("4000.00")
    assert f.impuesto_importe == Decimal("328.00")


# ─────────────────────────────────────────────────────────────────────────────
# Estimación del precio de venta de los materiales
# ─────────────────────────────────────────────────────────────────────────────

def test_estimar_venta_materiales_reparte_por_coste_y_suma_productos():
    # Obra 9 000 con mitad de coste en materiales → 4 500; productos íntegros.
    assert estimar_venta_materiales(
        Decimal("9000"), Decimal("1000"), Decimal("3000"), Decimal("6000")
    ) == Decimal("5500.00")


def test_sin_costes_no_se_inventa_el_reparto():
    assert estimar_venta_materiales(
        Decimal("9000"), Decimal("1000"), Decimal("0"), Decimal("0")
    ) == Decimal("1000.00")
    assert estimar_venta_materiales(
        Decimal("9000"), Decimal("0"), Decimal("0"), Decimal("0")
    ) == Decimal("0.00")


def test_la_estimacion_nunca_superala_base():
    assert estimar_venta_materiales(
        Decimal("1000"), Decimal("500"), Decimal("900"), Decimal("100")
    ) == Decimal("1500.00")


def test_base_gravada_acota_la_fraccion():
    assert base_gravada_eeuu("gross_receipts", Decimal("1000"), 0, Decimal("2")) == Decimal("1000.00")
    assert base_gravada_eeuu("materials", Decimal("1000"), Decimal("9999")) == Decimal("1000.00")


# ─────────────────────────────────────────────────────────────────────────────
# Avisos y leyendas
# ─────────────────────────────────────────────────────────────────────────────

def test_sin_estado_avisa_y_la_nota_del_estado_acompana():
    f = _f(us_tax_base="none", estado_codigo="")
    assert any("No job state" in a for a in f.avisos)
    f_tx = _f(us_tax_base="none", estado_codigo="TX")
    assert any("94-116" in a for a in f_tx.avisos)


def test_modo_con_reparto_sin_costes_avisa():
    f = _f(us_tax_base="materials", venta_materiales=Decimal("0"))
    assert any("could not be estimated" in a for a in f.avisos)


def test_estado_sin_impuesto_estatal_lo_dice_en_la_leyenda():
    f = _f(us_tax_base="none", estado_codigo="OR", tipo_pct=Decimal("0"))
    assert f.leyenda == "Oregon has no statewide sales tax."


def test_el_nombre_del_tributo_es_el_del_estado():
    assert _f(estado_codigo="HI", us_tax_base="gross_receipts").nombre_impuesto == "General excise tax"
    assert _f(estado_codigo="SD", us_tax_base="gross_receipts").nombre_impuesto == "Contractor's excise tax"
    assert _f(estado_codigo="FL", us_tax_base="none").nombre_impuesto == "Sales tax"


# ─────────────────────────────────────────────────────────────────────────────
# La tabla de defaults investigada
# ─────────────────────────────────────────────────────────────────────────────

def test_tabla_de_estados_completa_y_coherente():
    assert len(ESTADOS_EEUU) == 51                       # 50 estados + DC
    assert len(set(CODIGOS_ESTADO_EEUU)) == 51
    for e in ESTADOS_EEUU:
        assert e.base_defecto in BASES_US and e.base_defecto != ""
        assert Decimal("0") <= e.tipo_medio <= Decimal("11")
        assert Decimal("0") < e.fraccion_defecto <= Decimal("1")
    assert estado_por_codigo("DC") is not None
    assert estado_por_codigo("tx").nombre == "Texas"     # minúsculas toleradas


def test_defaults_por_marco_estatal():
    # Contratista-consumidor (marco mayoritario): no se cobra al cliente.
    for codigo in ("FL", "CA", "TX", "NY", "NJ", "NC", "KS", "IA", "AZ", "CT", "MS", "WV"):
        assert estado_por_codigo(codigo).base_defecto == "none", codigo
    # Los que cobran sobre el contrato.
    assert estado_por_codigo("WA").base_defecto == "full"
    assert estado_por_codigo("HI").base_defecto == "gross_receipts"
    assert estado_por_codigo("NM").base_defecto == "gross_receipts"
    assert estado_por_codigo("SD").base_defecto == "gross_receipts"
    # Dakota del Sur cobra el «excise» del 2 %, no el combinado de ventas.
    assert estado_por_codigo("SD").tipo_medio == Decimal("2.00")
    # Arizona precarga el 65 % para cuando el usuario pase a «gross receipts».
    assert estado_por_codigo("AZ").fraccion_defecto == Decimal("0.65")


# ─────────────────────────────────────────────────────────────────────────────
# El motor de totales aplica el modo (esto es lo que ve el cliente)
# ─────────────────────────────────────────────────────────────────────────────

def _presupuesto_us(**kw):
    """10 000 $ de obra; coste 6 000 (materiales 2 000, mano de obra 4 000).

    Venta estimada de materiales: 10 000 × 2 000/6 000 = 3 333,33.
    """
    from app.models import Capitulo, Presupuesto, PresupuestoItem

    cliente = Cliente(nombre="Test Client")
    p = Presupuesto(
        numero="P-US-1", titulo="Kitchen remodel", fecha=date(2026, 10, 1),
        moneda="USD", estado="borrador",
        impuesto_pct=kw.get("impuesto_pct", 8.2), descuento_pct=0.0,
        cliente=cliente,
        estado_codigo=kw.get("estado_codigo", "TX"),
        us_tax_base=kw.get("us_tax_base", ""),
        us_tax_fraccion=kw.get("us_tax_fraccion", 1.0),
    )
    cap = Capitulo(nombre="FLOORING", orden=1)
    cap.partidas = [PresupuestoItem(
        nombre="Porcelain tile", unidad="m2", cantidad=100.0,
        precio_unitario=100.0, coste_materiales=20.0, coste_mano_obra=40.0,
    )]
    p.capitulos = [cap]
    cfg = Configuracion(empresa_nombre="Sunshine Builders LLC",
                        empresa_pais="Estados Unidos", pdf_color="#0F4C81")
    return p, cfg


def test_totales_sin_modo_siguen_siendo_los_de_siempre():
    p, _cfg = _presupuesto_us(us_tax_base="")
    tot = calcular_totales(p)
    assert tot.impuesto == Decimal("820.00")       # 8,2 % sobre todo
    assert tot.total == Decimal("10820.00")


def test_totales_none_sin_impuesto_fantasma():
    p, _cfg = _presupuesto_us(us_tax_base="none")
    tot = calcular_totales(p)
    assert tot.impuesto == Decimal("0.00")
    assert tot.total == Decimal("10000.00")
    assert tot.us_base_gravada == Decimal("0")


def test_totales_materials_y_labor_reparten_la_base():
    p, _cfg = _presupuesto_us(us_tax_base="materials")
    tot = calcular_totales(p)   # sin pedir costes por categoría: el motor fuerza la pasada
    assert tot.venta_materiales == Decimal("3333.33")
    assert tot.us_base_gravada == Decimal("3333.33")
    assert tot.impuesto == Decimal("273.33")
    p2, _cfg = _presupuesto_us(us_tax_base="labor")
    tot2 = calcular_totales(p2)
    assert tot2.us_base_gravada == Decimal("6666.67")
    assert tot2.impuesto == Decimal("546.67")
    # materiales + mano de obra = el impuesto completo, al céntimo.
    assert tot.impuesto + tot2.impuesto == Decimal("820.00")


def test_totales_gross_receipts_con_fraccion():
    p, _cfg = _presupuesto_us(us_tax_base="gross_receipts", us_tax_fraccion=0.65,
                              estado_codigo="AZ", impuesto_pct=8.54)
    tot = calcular_totales(p)
    assert tot.us_base_gravada == Decimal("6500.00")
    assert tot.impuesto == Decimal("555.10")
    assert tot.total == Decimal("10555.10")


# ─────────────────────────────────────────────────────────────────────────────
# PDF: etiqueta, leyenda y puerta del interactivo
# ─────────────────────────────────────────────────────────────────────────────

def _texto_pdf(buf) -> str:
    lector = PdfReader(io.BytesIO(buf.getvalue()))
    return "\n".join((pg.extract_text() or "") for pg in lector.pages)


def test_pdf_none_no_muestra_impuesto_y_lo_explica():
    from app.services.pdf import generar_pdf

    p, cfg = _presupuesto_us(us_tax_base="none")
    t = _texto_pdf(generar_pdf(p, cfg, lang="en-US"))
    assert "No sales tax is charged on this contract" in t
    assert "not charged to the customer" in t
    assert "820.00" not in t
    assert "10,000.00" in t


def test_pdf_materials_dice_la_base_y_su_importe():
    from app.services.pdf import generar_pdf

    p, cfg = _presupuesto_us(us_tax_base="materials")
    t = _texto_pdf(generar_pdf(p, cfg, lang="en-US"))
    assert "materials only" in t
    assert "273.33" in t
    assert "10,273.33" in t


def test_con_base_parcial_el_pdf_sale_cerrado_y_en_full_interactivo():
    """El JS del PDF interactivo recalcula «base × %»: válido solo en full."""
    from app.models import PresupuestoItemProducto
    from app.services.pdf import generar_pdf

    p, cfg = _presupuesto_us(us_tax_base="materials")
    p.capitulos[0].partidas[0].productos_opciones = [
        PresupuestoItemProducto(nombre="Tile A", precio=12.0, unidad="m2", seleccionado=True),
        PresupuestoItemProducto(nombre="Tile B", precio=30.0, unidad="m2", seleccionado=False),
    ]
    campos = PdfReader(io.BytesIO(generar_pdf(p, cfg, lang="en-US").getvalue())).get_fields()
    assert not campos   # cerrado: sin AcroForm

    p2, cfg2 = _presupuesto_us(us_tax_base="full")
    p2.capitulos[0].partidas[0].productos_opciones = [
        PresupuestoItemProducto(nombre="Tile A", precio=12.0, unidad="m2", seleccionado=True),
        PresupuestoItemProducto(nombre="Tile B", precio=30.0, unidad="m2", seleccionado=False),
    ]
    campos2 = PdfReader(io.BytesIO(generar_pdf(p2, cfg2, lang="en-US").getvalue())).get_fields()
    assert campos2   # full = «base × %»: el JS sí lo modela


# ─────────────────────────────────────────────────────────────────────────────
# HTTP: editor, guardado, detalle, factura, duplicado y configuración
# ─────────────────────────────────────────────────────────────────────────────

def _empresa_eeuu(Session, estado="TX"):
    from app.models import Configuracion  # ya importado arriba; explícito por simetría

    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Estados Unidos"
        cfg.moneda_default = "USD"
        cfg.empresa_estado_eeuu = estado
        db.commit()
        return db.query(Cliente).first().id


def _crear_us(cliente_web, cliente_id, **extra):
    datos = {
        "client_id": str(cliente_id), "titulo": "Kitchen",
        "fecha": date.today().isoformat(), "validez_dias": "30",
        "moneda": "USD", "impuesto_pct": "8.2", "descuento_pct": "0",
        "estado": "borrador",
        "estructura_json": json.dumps([{
            "nombre": "FLOORING",
            "partidas": [{"nombre": "Porcelain tile", "unidad": "sq ft",
                          "cantidad": 100.0, "precio": 100.0, "descripcion": ""}],
        }]),
    }
    datos.update(extra)
    r = cliente_web.post("/presupuestos/nuevo", data=datos, follow_redirects=False)
    assert r.status_code == 303, r.text[:300]
    return int(r.headers["location"].split("?")[0].split("/")[-1])


def test_el_bloque_eeuu_solo_aparece_para_empresas_eeuu(entorno, cliente_web):
    Session, _ids, _rol = entorno
    _empresa_eeuu(Session)
    html = cliente_web.get("/presupuestos/nuevo").text
    assert 'id="us-estado"' in html
    assert "Texas (TX)" in html
    assert 'data-base="gross_receipts"' in html   # los defaults viajan al editor

    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "España"
        db.commit()
    html_es = cliente_web.get("/presupuestos/nuevo").text
    assert 'id="us-estado"' not in html_es


def test_guardar_none_deja_el_total_sin_impuesto_y_el_detalle_lo_explica(entorno, cliente_web):
    from app.models import Presupuesto

    Session, _ids, _rol = entorno
    cliente_id = _empresa_eeuu(Session)
    pid = _crear_us(cliente_web, cliente_id,
                    estado_codigo="TX", us_tax_base="none", us_tax_fraccion_pct="100")

    with Session() as db:
        p = db.get(Presupuesto, pid)
        assert p.estado_codigo == "TX"
        assert p.us_tax_base == "none"
        assert float(p.total) == pytest.approx(10000.0)     # sin el 8,2 % fantasma
        assert float(p.total_listado) == pytest.approx(10000.0)

    detalle = cliente_web.get(f"/presupuestos/{pid}").text
    assert "No sales tax is charged on this contract" in detalle


def test_un_modo_inventado_no_se_guarda(entorno, cliente_web):
    from app.models import Presupuesto

    Session, _ids, _rol = entorno
    cliente_id = _empresa_eeuu(Session)
    pid = _crear_us(cliente_web, cliente_id,
                    estado_codigo="XX", us_tax_base="sobre_el_aire",
                    us_tax_fraccion_pct="250")
    with Session() as db:
        p = db.get(Presupuesto, pid)
        assert (p.estado_codigo or "") == ""
        assert (p.us_tax_base or "") == ""
        assert p.us_tax_fraccion == pytest.approx(1.0)
        # Y el documento calcula como siempre: 8,2 % sobre la base completa.
        assert float(p.total) == pytest.approx(10820.0)


def test_la_factura_hereda_estado_modo_y_base_congelada(entorno, cliente_web):
    from app.models import Factura

    Session, _ids, _rol = entorno
    cliente_id = _empresa_eeuu(Session)
    pid = _crear_us(cliente_web, cliente_id,
                    estado_codigo="WA", us_tax_base="full", impuesto_pct="9.57")
    # El documento de cobro solo nace de un presupuesto aprobado.
    cliente_web.post(f"/presupuestos/{pid}/estado",
                     data={"estado": "aprobado"}, follow_redirects=False)
    r = cliente_web.post(f"/presupuestos/{pid}/factura", follow_redirects=False)
    assert r.status_code in (303, 200), r.text[:200]
    with Session() as db:
        f = db.query(Factura).filter(Factura.presupuesto_id == pid).one()
        assert f.estado_codigo == "WA"
        assert f.us_tax_base == "full"
        assert f.us_base_gravada == pytest.approx(10000.0)
        assert float(f.impuesto_monto) == pytest.approx(957.0)
        assert float(f.total) == pytest.approx(10957.0)


def test_al_duplicar_se_hereda_la_fiscalidad(entorno, cliente_web):
    from app.models import Presupuesto

    Session, _ids, _rol = entorno
    cliente_id = _empresa_eeuu(Session)
    pid = _crear_us(cliente_web, cliente_id,
                    estado_codigo="TX", us_tax_base="none")
    r = cliente_web.post(f"/presupuestos/{pid}/duplicar", follow_redirects=False)
    assert r.status_code == 303, r.text[:200]
    with Session() as db:
        copia = (db.query(Presupuesto)
                 .filter(Presupuesto.id != pid)
                 .order_by(Presupuesto.id.desc()).first())
        assert copia is not None
        assert copia.estado_codigo == "TX"
        assert copia.us_tax_base == "none"
        assert float(copia.total) == pytest.approx(10000.0)


def test_el_estado_habitual_se_guarda_y_se_valida(entorno, cliente_web):
    Session, _ids, _rol = entorno
    _empresa_eeuu(Session, estado="")
    with Session() as db:
        cfg = db.query(Configuracion).first()
        datos = {
            "empresa_nombre": cfg.empresa_nombre or "Builders",
            "empresa_pais": "Estados Unidos",
            "empresa_estado_eeuu": "FL",
            "iva_default": "7",
        }
    r = cliente_web.post("/configuracion", data=datos, follow_redirects=False)
    assert r.status_code in (200, 303), r.text[:200]
    with Session() as db:
        assert db.query(Configuracion).first().empresa_estado_eeuu == "FL"

    datos["empresa_estado_eeuu"] = "ZZ"
    cliente_web.post("/configuracion", data=datos, follow_redirects=False)
    with Session() as db:
        assert (db.query(Configuracion).first().empresa_estado_eeuu or "") == ""


# ─────────────────────────────────────────────────────────────────────────────
# La landing no enseña el error que el motor corrige
# ─────────────────────────────────────────────────────────────────────────────

def test_el_ejemplo_de_la_landing_us_no_cobra_sales_tax():
    from app.services.landing_ejemplo import contexto_ejemplo

    ej = contexto_ejemplo("US", "en")
    assert ej["tot"]["iva"] == ej["tot"]["subtotal"] or "not charged" in ej["iva_txt"]
    assert "not charged" in ej["iva_txt"]
    assert ej["tot"]["total"] == ej["tot"]["subtotal"]
