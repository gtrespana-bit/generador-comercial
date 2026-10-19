"""RCT e inversión del sujeto pasivo irlandesas.

El RCT se parece al CIS británico lo justo para resultar peligroso: quien
reutilice la lógica británica descontará los materiales de la base y
retendrá de menos en cada factura, porque en Irlanda la retención cae sobre
el importe íntegro sin IVA. Este test se centra en eso, en que ningún otro
mercado herede reglas irlandesas, en la leyenda que Revenue exige para la
inversión del sujeto pasivo y en la regla de los dos tercios, que puede
obligar a facturar al 23 % una operación cotizada al 13,5 %.

Importes en euros, con dos decimales exactos.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.fiscalidad_irlanda import (
    LEYENDA_INVERSION_IE,
    TIPO_RCT_SIN_REGISTRO,
    calcular_fiscalidad_ie,
    inversion_sujeto_pasivo_procede_ie,
)
from app.services.pdf import generar_factura_pdf, generar_pdf


def _f(**kw):
    base = dict(
        pais_codigo="IE",
        base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"),
        iva_pct=Decimal("13.5"),
    )
    base.update(kw)
    return calcular_fiscalidad_ie(**base)


# ─────────────────────────────────────────────────────────────────────────────
# Solo rige en Irlanda
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pais", ["GB", "US", "AU", "CA", "VE", "ES", "", None, "ie-"])
def test_fuera_de_irlanda_no_se_aplica_nada(pais):
    """El Reino Unido tiene su CIS; compartir isla no comparte retención."""
    f = _f(
        pais_codigo=pais,
        coste_materiales=Decimal("4900"),
        iva_tratamiento="inversion_sujeto_pasivo",
        rct_tipo=Decimal("20"),
    )
    assert f.aplica is False
    assert f.retencion_rct == Decimal("0")
    assert f.iva_invertido == Decimal("0")
    assert f.leyenda_iva == ""
    assert f.con_inversion_sujeto_pasivo is False
    assert f.avisos == ()


def test_irlanda_se_reconoce_aunque_venga_en_minuscula():
    assert _f(pais_codigo=" ie ").aplica is True


# ─────────────────────────────────────────────────────────────────────────────
# IVA
# ─────────────────────────────────────────────────────────────────────────────

def test_documento_normal_no_cambia_de_comportamiento():
    """Sin marcar nada: IVA reducido de construcción, sin retención."""
    f = _f()
    assert f.iva_importe == Decimal("675.00")
    assert f.iva_invertido == Decimal("0")
    assert f.retencion_rct == Decimal("0")
    assert f.total_a_cobrar == Decimal("5675.00")
    assert f.leyenda_iva == ""
    assert f.avisos == ()


def test_tipo_estandar_del_23_por_ciento():
    f = _f(iva_pct=Decimal("23"), iva_tratamiento="estandar")
    assert f.iva_importe == Decimal("1150.00")
    assert f.avisos == ()


def test_tipo_inhabitual_para_irlanda_avisa():
    """Un 20 % huele a tipo británico heredado: Irlanda es 13,5 o 23."""
    f = _f(iva_pct=Decimal("20"), iva_tratamiento="estandar")
    assert any("13,5" in a and "23" in a for a in f.avisos)


def test_inversion_no_cobra_iva_pero_lo_declara_el_contratista_principal():
    f = _f(iva_tratamiento="inversion_sujeto_pasivo", rct_tipo=Decimal("20"))
    assert f.iva_importe == Decimal("0")
    assert f.iva_invertido == Decimal("675.00")
    assert f.con_inversion_sujeto_pasivo is True


def test_la_leyenda_es_la_que_dicta_revenue():
    f = _f(iva_tratamiento="inversion_sujeto_pasivo")
    assert f.leyenda_iva == LEYENDA_INVERSION_IE
    assert f.leyenda_iva == (
        "VAT on this supply to be accounted for by the Principal Contractor"
    )


def test_inversion_sin_tipo_avisa():
    f = _f(iva_pct=Decimal("0"), iva_tratamiento="inversion_sujeto_pasivo")
    assert any("0 %" in a for a in f.avisos)


def test_tratamiento_desconocido_cae_a_la_regla_normal():
    f = _f(iva_tratamiento="inventado")
    assert f.iva_tratamiento == ""
    assert f.iva_importe == Decimal("675.00")
    assert f.avisos


# ─────────────────────────────────────────────────────────────────────────────
# RCT: la retención sobre el importe íntegro
# ─────────────────────────────────────────────────────────────────────────────

def test_el_rct_retiene_sobre_el_importe_integro_materiales_incluidos():
    """La diferencia con el CIS en una cifra: aquí serían 760; aquí, 1 000.

    Con el CIS británico la base sería 5 000 − 1 200 de materiales = 3 800 y
    la retención 760. El RCT no descuenta nada: 20 % de 5 000 = 1 000.
    """
    f = _f(rct_tipo=Decimal("20"))
    assert f.base_rct == Decimal("5000")
    assert f.retencion_rct == Decimal("1000.00")


def test_el_rct_se_calcula_sin_iva_aunque_el_iva_sea_normal():
    f = _f(rct_tipo=Decimal("20"))
    # 5 000 + 675 de IVA − 1 000 de retención.
    assert f.total_a_cobrar == Decimal("4675.00")


def test_rct_con_inversion_ejemplo_completo():
    f = _f(iva_tratamiento="inversion_sujeto_pasivo", rct_tipo=Decimal("20"))
    assert f.total_a_cobrar == Decimal("4000.00")


@pytest.mark.parametrize("tipo,retencion", [
    (Decimal("0"), Decimal("0.00")),
    (Decimal("20"), Decimal("1000.00")),
    (Decimal("35"), Decimal("1750.00")),
])
def test_los_tres_tipos_de_revenue(tipo, retencion):
    f = _f(rct_tipo=tipo)
    assert f.rct_aplica is True
    assert f.rct_tipo == tipo
    assert f.retencion_rct == retencion


def test_rct_al_cero_aplica_aunque_no_retenga():
    """0 % con autorización no es lo mismo que estar fuera del RCT."""
    f = _f(rct_tipo=Decimal("0"))
    assert f.rct_aplica is True
    assert f.retencion_rct == Decimal("0.00")


def test_sin_rct_no_hay_retencion():
    f = _f(rct_tipo=None)
    assert f.rct_aplica is False
    assert f.base_rct == Decimal("0")


def test_un_tipo_que_revenue_no_conoce_no_retiene():
    f = _f(rct_tipo=Decimal("25"))
    assert f.rct_aplica is False
    assert f.retencion_rct == Decimal("0")
    assert any("no existe" in a for a in f.avisos)


def test_el_35_avisa_de_que_es_el_tipo_sin_registro():
    f = _f(rct_tipo=TIPO_RCT_SIN_REGISTRO)
    assert any("35 %" in a and "registrado" in a for a in f.avisos)


def test_con_rct_siempre_se_recuerda_la_autorizacion_previa():
    f = _f(rct_tipo=Decimal("20"))
    assert any("autorización de deducción" in a for a in f.avisos)


def test_rct_con_iva_cargado_avisa_de_la_inversion():
    f = _f(rct_tipo=Decimal("20"))
    assert any("inversión del sujeto pasivo" in a for a in f.avisos)


def test_inversion_sin_rct_avisa():
    f = _f(iva_tratamiento="inversion_sujeto_pasivo")
    assert any("sin RCT marcado" in a for a in f.avisos)


def test_rct_e_inversion_juntos_no_se_contradicen():
    f = _f(iva_tratamiento="inversion_sujeto_pasivo", rct_tipo=Decimal("20"))
    assert not any("sin RCT marcado" in a for a in f.avisos)
    assert not any("Cargar IVA" in a for a in f.avisos)


# ─────────────────────────────────────────────────────────────────────────────
# Regla de los dos tercios
# ─────────────────────────────────────────────────────────────────────────────

def test_materiales_sobre_dos_tercios_al_13_5_avisa_del_23():
    f = _f(coste_materiales=Decimal("3400"))
    assert f.supera_dos_tercios is True
    assert f.pct_materiales == Decimal("68.0")
    assert any("dos tercios" in a and "23 %" in a for a in f.avisos)
    # Y no cambia el tipo por su cuenta: el importe sigue al 13,5 %.
    assert f.iva_importe == Decimal("675.00")


def test_justo_en_dos_tercios_no_supera():
    """La regla muerde al superar dos tercios, no al igualarlos."""
    f = _f(base_imponible=Decimal("6000"), coste_materiales=Decimal("4000"))
    assert f.supera_dos_tercios is False
    assert not any("dos tercios" in a for a in f.avisos)


def test_por_debajo_de_dos_tercios_sin_aviso():
    f = _f(coste_materiales=Decimal("3300"))
    assert f.supera_dos_tercios is False
    assert f.avisos == ()


def test_al_23_la_regla_ya_esta_cumplida_y_no_avisa():
    f = _f(coste_materiales=Decimal("3400"), iva_pct=Decimal("23"),
           iva_tratamiento="estandar")
    assert f.supera_dos_tercios is True
    assert not any("dos tercios" in a for a in f.avisos)


def test_con_inversion_la_regla_no_avisa():
    f = _f(coste_materiales=Decimal("3400"),
           iva_tratamiento="inversion_sujeto_pasivo", rct_tipo=Decimal("20"))
    assert not any("dos tercios" in a for a in f.avisos)


# ─────────────────────────────────────────────────────────────────────────────
# ¿Procede la inversión?
# ─────────────────────────────────────────────────────────────────────────────

def test_procede_con_todas_las_condiciones():
    procede, avisos = inversion_sujeto_pasivo_procede_ie(
        es_servicio_construccion=True,
        cliente_es_contratista_principal=True,
        operacion_sujeta_a_rct=True,
    )
    assert procede is True
    assert avisos == ()


def test_a_un_particular_se_le_carga_iva():
    procede, avisos = inversion_sujeto_pasivo_procede_ie(
        es_servicio_construccion=True,
        cliente_es_contratista_principal=False,
        operacion_sujeta_a_rct=False,
    )
    assert procede is False
    assert any("particular" in a for a in avisos)


def test_sin_operacion_sujeta_a_rct_no_procede():
    procede, _ = inversion_sujeto_pasivo_procede_ie(
        es_servicio_construccion=True,
        cliente_es_contratista_principal=True,
        operacion_sujeta_a_rct=False,
    )
    assert procede is False


def test_fuera_de_la_construccion_no_procede():
    procede, _ = inversion_sujeto_pasivo_procede_ie(
        es_servicio_construccion=False,
        cliente_es_contratista_principal=True,
        operacion_sujeta_a_rct=True,
    )
    assert procede is False


def test_entre_personas_vinculadas_procede_sin_contratista_principal():
    procede, avisos = inversion_sujeto_pasivo_procede_ie(
        es_servicio_construccion=True,
        cliente_es_contratista_principal=False,
        operacion_sujeta_a_rct=False,
        personas_vinculadas=True,
    )
    assert procede is True
    assert any("vinculadas" in a for a in avisos)


# ─────────────────────────────────────────────────────────────────────────────
# Formulario del editor
# ─────────────────────────────────────────────────────────────────────────────

def test_el_formulario_acepta_solo_los_tipos_de_revenue():
    from app.routers.presupuestos import _fiscalidad_ie_desde_form

    assert _fiscalidad_ie_desde_form(
        {"rct_tipo": "20", "iva_tratamiento": "inversion_sujeto_pasivo"}
    ) == (20.0, "inversion_sujeto_pasivo")
    # 0 % no es «vacío»: el documento está bajo RCT reteniendo cero.
    assert _fiscalidad_ie_desde_form({"rct_tipo": "0"}) == (0.0, "")
    assert _fiscalidad_ie_desde_form({"rct_tipo": ""}) == (None, "")
    # Un 25 % inventado se descarta entero, no se redondea a nada.
    assert _fiscalidad_ie_desde_form({"rct_tipo": "25"}) == (None, "")
    assert _fiscalidad_ie_desde_form({"rct_tipo": "abc"}) == (None, "")


def test_la_ruta_de_la_descomposicion_apunta_a_su_funcion():
    """Regresión de la Fase 1 británica: el decorador de esta ruta quedó
    pegado a ``_fiscalidad_gb_desde_form`` al insertar los helpers, y la
    pantalla de la descomposición dejó de estar registrada."""
    from app.routers.presupuestos import router

    get = [
        r.endpoint.__name__
        for r in router.routes
        if getattr(r, "path", "") == "/presupuestos/{presupuesto_id}/partidas/{partida_id}/descomposicion"
        and "GET" in (getattr(r, "methods", None) or set())
    ]
    assert get == ["ver_descomposicion_partida"]


# ─────────────────────────────────────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────────────────────────────────────

def _presupuesto_ie(**kw):
    """Presupuesto irlandés mínimo: 5 000 € de obra, 1 200 € de materiales."""
    from datetime import date

    from app.models import Capitulo, Cliente, Configuracion, Presupuesto, PresupuestoItem

    cliente = Cliente(nombre="Test Client Ltd")
    p = Presupuesto(
        numero="P-IE-1", titulo="Rear extension", fecha=date(2026, 1, 15),
        moneda="EUR", estado="borrador", impuesto_pct=13.5, descuento_pct=0.0,
        cliente=cliente,
        rct_tipo=kw.get("rct_tipo"),
        iva_tratamiento=kw.get("iva_tratamiento", ""),
    )
    cap = Capitulo(nombre="FIRST FIX", orden=1)
    partida = PresupuestoItem(
        nombre="Stud partition", unidad="m2", cantidad=100.0, precio_unitario=50.0,
        coste_materiales=kw.get("coste_materiales", 12.0), coste_mano_obra=20.0,
    )
    cap.partidas = [partida]
    p.capitulos = [cap]
    cfg = Configuracion(empresa_nombre="Test Builders Ltd", empresa_pais="Irlanda",
                        pdf_color="#0F4C81")
    return p, cfg


def _texto(pdf_buf) -> str:
    import io

    from pypdf import PdfReader

    lector = PdfReader(io.BytesIO(pdf_buf.getvalue()))
    return "\n".join((p.extract_text() or "") for p in lector.pages)


def test_costumbre_del_documento_irlandes_es_el_iva_normal():
    p, cfg = _presupuesto_ie()
    t = _texto(generar_pdf(p, cfg, lang="en-IE"))
    assert "RCT" not in t
    assert "Principal Contractor" not in t
    # 5 000 + 13,5 % de IVA = 5 675, con el separador irlandés.
    assert "5,675.00" in t


def test_el_pdf_muestra_la_retencion_rct_sobre_el_importe_integro():
    p, cfg = _presupuesto_ie(rct_tipo=20.0)
    t = _texto(generar_pdf(p, cfg, lang="en-IE"))
    # 20 % de 5 000 (materiales incluidos), no de 3 800 como haría el CIS.
    assert "RCT DEDUCTION (20.0 %)" in t
    assert "1,000.00" in t
    assert "3,800.00" not in t
    assert "4,675.00" in t
    assert "TOTAL PAYABLE (after RCT deduction)" in t or "TOTAL PAYABLE" in t


def test_el_pdf_con_inversion_lleva_la_leyenda_de_revenue():
    p, cfg = _presupuesto_ie(iva_tratamiento="inversion_sujeto_pasivo", rct_tipo=20.0)
    t = _texto(generar_pdf(p, cfg, lang="en-IE"))
    assert "accounted for by the Principal Contractor" in t
    assert "VAT" in t and "not charged" in t and "(13.5 %)" in t
    # 5 000 sin IVA − 1 000 de RCT.
    assert "4,000.00" in t


def test_el_pdf_de_otro_mercado_no_aplica_reglas_irlandesas():
    p, cfg = _presupuesto_ie(rct_tipo=20.0, iva_tratamiento="inversion_sujeto_pasivo")
    t = _texto(generar_pdf(p, cfg, lang="en-US"))
    assert "RCT" not in t
    assert "Principal Contractor" not in t


def test_con_rct_el_pdf_sale_cerrado_no_interactivo():
    """El motor de JavaScript no modela el RCT: mejor estático que incoherente."""
    p, cfg = _presupuesto_ie(rct_tipo=20.0)
    t = _texto(generar_pdf(p, cfg, lang="en-IE"))
    assert "interactive" not in t.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Documento de cobro y detalle
# ─────────────────────────────────────────────────────────────────────────────

def test_la_factura_hereda_la_fiscalidad_del_presupuesto():
    from datetime import date

    from app.models import Factura

    presupuesto, _cfg = _presupuesto_ie(
        rct_tipo=20.0, iva_tratamiento="inversion_sujeto_pasivo")
    factura = Factura(
        numero="F-IE-1", year=2026, fecha=date(2026, 2, 1), moneda="EUR",
        impuesto_pct=presupuesto.impuesto_pct, descuento_pct=0.0,
        iva_tratamiento=presupuesto.iva_tratamiento,
        rct_tipo=presupuesto.rct_tipo,
        coste_materiales=float(presupuesto._totales.coste_materiales),
    )
    assert factura.rct_tipo == 20.0
    # Misma aritmética que el presupuesto: 5 000, inversión, RCT 20 % → 4 000.
    f = _f(iva_tratamiento=factura.iva_tratamiento, rct_tipo=factura.rct_tipo)
    assert f.total_a_cobrar == Decimal("4000.00")


def test_las_columnas_rct_nacen_en_null():
    """Comprobado contra el esquema: los ``default`` solo se ven al insertar."""
    from app.models import Factura, Presupuesto

    for modelo in (Presupuesto, Factura):
        columna = modelo.__table__.columns["rct_tipo"]
        assert columna.nullable is True
        assert columna.default is None


def test_el_pdf_del_documento_de_cobro_lleva_el_rct():
    from datetime import date

    from app.models import Cliente, Configuracion, Factura, FacturaCapitulo, FacturaItem

    factura = Factura(
        numero="F-IE-2", year=2026, fecha=date(2026, 2, 1), moneda="EUR",
        impuesto_pct=13.5, descuento_pct=0.0, rct_tipo=20.0,
        coste_materiales=1200.0, client_id=1,
    )
    cap = FacturaCapitulo(nombre="GROUNDWORKS", orden=1)
    cap.partidas = [FacturaItem(nombre="Excavation", unidad="m3", cantidad=100.0,
                             precio_unitario=50.0)]
    factura.capitulos = [cap]
    factura.cliente = Cliente(nombre="Henderson Construction Ltd")
    cfg = Configuracion(empresa_nombre="Whitfield Builders Ltd",
                        empresa_pais="Irlanda", pdf_color="#0F4C81")
    t = _texto(generar_factura_pdf(factura, cfg, lang="en-IE"))
    assert "RCT DEDUCTION (20.0 %)" in t
    assert "1,000.00" in t
    assert "3,800.00" not in t


def test_el_detalle_devuelve_el_aviso_de_los_dos_tercios_sin_rct():
    """Documento corriente, sin retención, pero mal de tipo: el detalle lo ve."""
    from app.routers.presupuestos import _fiscalidad_ie_documento

    p, cfg = _presupuesto_ie(coste_materiales=34.0)  # 3 400 de 5 000
    f = _fiscalidad_ie_documento(p, cfg)
    assert f is not None
    assert f.rct_aplica is False
    assert any("dos tercios" in a for a in f.avisos)


def test_el_detalle_sin_nada_que_contar_devuelve_none():
    from app.routers.presupuestos import _fiscalidad_ie_documento

    p, cfg = _presupuesto_ie()
    assert _fiscalidad_ie_documento(p, cfg) is None


def test_el_detalle_de_otra_empresa_devuelve_none():
    from app.models import Configuracion
    from app.routers.presupuestos import _fiscalidad_ie_documento

    p, _cfg = _presupuesto_ie(coste_materiales=34.0, rct_tipo=20.0)
    cfg_es = Configuracion(empresa_nombre="Obras SA", empresa_pais="España")
    assert _fiscalidad_ie_documento(p, cfg_es) is None
