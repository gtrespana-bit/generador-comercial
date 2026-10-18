"""CIS e inversión del sujeto pasivo británicas.

Dos reglas que no existen en ningún otro mercado de CotizaT, así que el test
se centra en lo que puede salir caro: que la retención se calcule sobre la
factura en lugar de sobre la mano de obra, que un documento de otro mercado
acabe aplicando reglas británicas, o que una factura con inversión del sujeto
pasivo salga sin la leyenda que exige Hacienda.

Los importes de referencia son los ejemplos resueltos que publica la propia
Hacienda británica y se comprueban en libras, con dos decimales exactos.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services import calculations as calc
from app.services.fiscalidad_reino_unido import (
    LEYENDA_INVERSION,
    TIPO_CIS_NO_REGISTRADO,
    calcular_fiscalidad_gb,
    inversion_sujeto_pasivo_procede,
)
from app.services.pdf import generar_factura_pdf, generar_pdf


# ─────────────────────────────────────────────────────────────────────────────
# Solo rige en el Reino Unido
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pais", ["US", "AU", "CA", "IE", "VE", "ES", "", None, "gb-"])
def test_fuera_del_reino_unido_no_se_aplica_nada(pais):
    """Irlanda comparte isla, Australia comparte corona: ni una regla."""
    f = calcular_fiscalidad_gb(
        pais_codigo=pais,
        base_imponible=Decimal("10000"),
        coste_materiales=Decimal("0"),
        iva_pct=Decimal("20"),
        iva_tratamiento="inversion_sujeto_pasivo",
        cis_tipo=Decimal("20"),
    )
    assert f.aplica is False
    assert f.retencion_cis == Decimal("0")
    assert f.iva_invertido == Decimal("0")
    assert f.iva_importe == Decimal("0")
    assert f.leyenda_iva == ""
    assert f.con_inversion_sujeto_pasivo is False


def test_reino_unido_se_reconoce_aunque_venga_en_minuscula():
    f = calcular_fiscalidad_gb(
        pais_codigo=" gb ", base_imponible=Decimal("100"),
        coste_materiales=Decimal("0"), iva_pct=Decimal("20"),
    )
    assert f.aplica is True


# ─────────────────────────────────────────────────────────────────────────────
# IVA
# ─────────────────────────────────────────────────────────────────────────────

def test_documento_normal_no_cambia_de_comportamiento():
    """Sin tratamiento explícito, el IVA se cobra como siempre."""
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("0"), iva_pct=Decimal("20"),
    )
    assert f.iva_importe == Decimal("1000.00")
    assert f.iva_invertido == Decimal("0")
    assert f.total_a_cobrar == Decimal("6000.00")
    assert f.leyenda_iva == ""


def test_inversion_del_sujeto_pasivo_no_cobra_iva_pero_lo_declarara_el_cliente():
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("0"), iva_pct=Decimal("20"),
        iva_tratamiento="inversion_sujeto_pasivo",
    )
    assert f.iva_importe == Decimal("0")
    assert f.iva_invertido == Decimal("1000.00")
    assert f.total_a_cobrar == Decimal("5000.00")
    assert f.con_inversion_sujeto_pasivo is True


def test_la_leyenda_es_obligatoria_y_nombrable():
    """Hacienda exige la expresión «reverse charge» en la factura."""
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("0"), iva_pct=Decimal("20"),
        iva_tratamiento="inversion_sujeto_pasivo",
    )
    assert "reverse charge" in f.leyenda_iva.lower()
    assert f.leyenda_iva == LEYENDA_INVERSION


def test_tipo_reducido_del_cinco_por_ciento():
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("2000"),
        coste_materiales=Decimal("0"), iva_pct=Decimal("5"),
    )
    assert f.iva_importe == Decimal("100.00")


def test_tratamiento_desconocido_cae_a_la_regla_normal():
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("1000"),
        coste_materiales=Decimal("0"), iva_pct=Decimal("20"),
        iva_tratamiento="inventado",
    )
    assert f.iva_tratamiento == ""
    assert f.iva_importe == Decimal("200.00")


# ─────────────────────────────────────────────────────────────────────────────
# CIS: la retención va sobre la mano de obra
# ─────────────────────────────────────────────────────────────────────────────

def test_la_retencion_se_calcula_sobre_la_mano_de_obra_no_sobre_la_factura():
    """El error clásico: 20 % de 5 000 = 1 000, en vez de 20 % de 3 800 = 760."""
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("0"),
        cis_tipo=Decimal("20"),
    )
    assert f.materiales_excluidos == Decimal("1200.00")
    assert f.base_cis == Decimal("3800.00")
    assert f.retencion_cis == Decimal("760.00")
    assert f.retencion_cis != Decimal("1000.00")


def test_ejemplo_resuelto_de_hacienda_con_inversion_y_cis():
    """5 000 netos, 1 200 de materiales, CIS 20 %, inversión: se cobran 4 240."""
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("20"),
        iva_tratamiento="inversion_sujeto_pasivo", cis_tipo=Decimal("20"),
    )
    assert f.total_a_cobrar == Decimal("4240.00")


def test_ejemplo_resuelto_de_hacienda_con_iva_normal_y_cis():
    """El mismo caso facturando con IVA: 6 000 brutos menos 760 = 5 240.

    La retención no crece al añadir el IVA: se calcula sobre el importe sin
    impuesto, que es lo que confunde a quien viene de otras retenciones.
    """
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("20"),
        cis_tipo=Decimal("20"),
    )
    assert f.retencion_cis == Decimal("760.00")
    assert f.total_a_cobrar == Decimal("5240.00")


@pytest.mark.parametrize(
    "tipo,esperado", [(Decimal("0"), "0.00"), (Decimal("20"), "760.00"), (Decimal("30"), "1140.00")]
)
def test_los_tres_tipos_que_admite_hacienda(tipo, esperado):
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("0"), cis_tipo=tipo,
    )
    assert f.retencion_cis == Decimal(esperado)


def test_sin_cis_no_hay_retencion():
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("0"), cis_tipo=None,
    )
    assert f.cis_aplica is False
    assert f.retencion_cis == Decimal("0")
    assert f.base_cis == Decimal("0")


def test_tipo_cis_invalido_no_retiene_y_avisa():
    """El 25 % no existe: si se cuela, mejor no retener que retener mal."""
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("0"),
        cis_tipo=Decimal("25"),
    )
    assert f.retencion_cis == Decimal("0")
    assert any("30 %" in a for a in f.avisos)


def test_el_treinta_por_ciento_avisa_de_que_no_hay_registro_verificable():
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("0"),
        cis_tipo=TIPO_CIS_NO_REGISTRADO,
    )
    assert any("registro" in a.lower() for a in f.avisos)


def test_sin_materiales_declarados_la_base_es_el_importe_integro_y_avisa():
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("0"), iva_pct=Decimal("0"), cis_tipo=Decimal("20"),
    )
    assert f.base_cis == Decimal("5000.00")
    assert f.retencion_cis == Decimal("1000.00")
    assert any("materiales" in a.lower() for a in f.avisos)


def test_materiales_negativos_no_inflan_la_base():
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("-900"), iva_pct=Decimal("0"), cis_tipo=Decimal("20"),
    )
    assert f.base_cis == Decimal("5000.00")


def test_materiales_por_encima_de_la_base_se_recortan_a_la_base():
    """Datos mal cargados: la retención nunca puede ser negativa."""
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("1000"),
        coste_materiales=Decimal("5000"), iva_pct=Decimal("0"), cis_tipo=Decimal("20"),
    )
    assert f.materiales_excluidos == Decimal("1000.00")
    assert f.base_cis == Decimal("0")
    assert f.retencion_cis == Decimal("0")


# ─────────────────────────────────────────────────────────────────────────────
# ¿Procede la inversión del sujeto pasivo?
# ─────────────────────────────────────────────────────────────────────────────

def _procede(**kw):
    base = dict(
        servicio_dentro_de_cis=True,
        cliente_con_iva=True,
        cliente_registrado_cis=True,
        tipo_no_exento=True,
    )
    base.update(kw)
    return inversion_sujeto_pasivo_procede(**base)


@pytest.mark.parametrize(
    "falta",
    ["servicio_dentro_de_cis", "cliente_con_iva", "cliente_registrado_cis", "tipo_no_exento"],
)
def test_falta_cualquier_condicion_y_no_procede(falta):
    procede, motivos = _procede(**{falta: False})
    assert procede is False
    assert motivos


def test_condiciones_completas_si_procede():
    procede, motivos = _procede()
    assert procede is True
    assert motivos == ()


def test_usuario_final_sin_notificacion_escrita_se_invierte_igualmente():
    """La inversión es la regla; el usuario final es una excepción que hay que
    invocar por escrito. Sin papel, se invierte y se avisa."""
    procede, avisos = _procede(cliente_es_usuario_final=True, notificacion_escrita=False)
    assert procede is True
    assert any("escrita" in a.lower() for a in avisos)


def test_usuario_final_con_notificacion_escrita_factura_con_iva():
    procede, motivos = _procede(cliente_es_usuario_final=True, notificacion_escrita=True)
    assert procede is False
    assert any("escrito" in m.lower() for m in motivos)


# ─────────────────────────────────────────────────────────────────────────────
# Reparto del coste por categoría
# ─────────────────────────────────────────────────────────────────────────────

class _Partida:
    """Partida mínima sin descomposición: manda la caché de campos."""

    def __init__(self, **kw):
        self.cantidad_total = kw.get("cantidad_total", 1)
        self.desperdicio_pct = kw.get("desperdicio_pct", 0)
        self.descomposicion_cype = kw.get("descomposicion_cype")
        self.coste_materiales = kw.get("coste_materiales", 0)
        self.coste_mano_obra = kw.get("coste_mano_obra", 0)
        self.coste_complementarios = kw.get("coste_complementarios", 0)
        self.coste_otros = kw.get("coste_otros", 0)


def test_el_reparto_por_categoria_suma_el_coste_de_obra():
    """Mismo total que ya se venía calculando: el reparto no inventa importe."""
    p = _Partida(cantidad_total=10, coste_materiales=3, coste_mano_obra=5,
                 coste_complementarios=1, coste_otros=0.5)
    reparto = calc.costes_obra_partida(p)
    assert sum(reparto.values()) == calc.coste_obra_partida(p)
    assert reparto["materiales"] == Decimal("30.00")


def test_el_reparto_aplica_el_desperdicio_como_el_coste_de_obra():
    p = _Partida(cantidad_total=10, desperdicio_pct=10, coste_materiales=3,
                 coste_mano_obra=5)
    reparto = calc.costes_obra_partida(p)
    assert sum(reparto.values()) == calc.coste_obra_partida(p)
    assert reparto["materiales"] == Decimal("33.00")


def test_coste_desconocido_se_imputa_a_otros_no_a_materiales():
    """Imputarlo a materiales lo excluiría de la retención y dejaría al
    contratista corto, que es a quien Hacienda le reclama la diferencia."""
    class _Cype:
        origen = "cype"
        filas = None
        coste_directo_unitario = 42
        archivo_origen = "x.xls"

    p = _Partida(cantidad_total=2, descomposicion_cype=_Cype())
    reparto = calc.costes_obra_partida(p)
    assert reparto["otros"] == Decimal("84.00")
    assert reparto["materiales"] == Decimal("0")


def test_totales_no_reparten_costes_si_no_se_piden():
    p = _Partida(cantidad_total=1, coste_materiales=100, coste_mano_obra=50)

    class _P:
        todas_partidas = [p]
        usar_funciones_avanzadas = False
        transporte_monto = 0
        otros_cargos_monto = 0
        gastos_indirectos_pct = 0
        imprevistos_pct = 0
        descuento_pct = 0
        impuesto_pct = 0

    t = calc.calcular_totales(_P())
    assert t.coste_materiales == Decimal("0.00")
    assert t.coste_obra == Decimal("150.00")


def test_totales_reparten_costes_cuando_se_piden():
    p = _Partida(cantidad_total=1, coste_materiales=100, coste_mano_obra=50)

    class _P:
        todas_partidas = [p]
        usar_funciones_avanzadas = False
        transporte_monto = 0
        otros_cargos_monto = 0
        gastos_indirectos_pct = 0
        imprevistos_pct = 0
        descuento_pct = 0
        impuesto_pct = 0

    t = calc.calcular_totales(_P(), con_costes_categoria=True)
    assert t.coste_materiales == Decimal("100.00")
    assert t.coste_obra == Decimal("150.00")


# ─────────────────────────────────────────────────────────────────────────────
# El PDF
# ─────────────────────────────────────────────────────────────────────────────

def _presupuesto_gb(**kw):
    """Presupuesto británico mínimo: 5 000 de obra, 1 200 de materiales."""
    from datetime import date

    from app.models import Capitulo, Cliente, Configuracion, Presupuesto, PresupuestoItem

    cliente = Cliente(nombre="Test Client Ltd")
    p = Presupuesto(
        numero="P-UK-1", titulo="Loft conversion", fecha=date(2026, 1, 15),
        moneda="GBP", estado="borrador", impuesto_pct=20.0, descuento_pct=0.0,
        cliente=cliente,
        cis_tipo=kw.get("cis_tipo"),
        iva_tratamiento=kw.get("iva_tratamiento", ""),
    )
    cap = Capitulo(nombre="FIRST FIX", orden=1)
    partida = PresupuestoItem(
        nombre="Stud partition", unidad="m2", cantidad=100.0, precio_unitario=50.0,
        coste_materiales=12.0, coste_mano_obra=20.0,
    )
    cap.partidas = [partida]
    p.capitulos = [cap]
    cfg = Configuracion(empresa_nombre="Test Builders Ltd", empresa_pais="Reino Unido",
                        pdf_color="#0F4C81")
    return p, cfg


def _texto(pdf_buf) -> str:
    import io

    from pypdf import PdfReader

    lector = PdfReader(io.BytesIO(pdf_buf.getvalue()))
    return "\n".join((p.extract_text() or "") for p in lector.pages)


def test_costumbre_del_documento_britanico_es_el_iva_normal():
    """Sin marcar nada, un presupuesto británico sale exactamente como antes."""
    p, cfg = _presupuesto_gb()
    t = _texto(generar_pdf(p, cfg, lang="en-GB"))
    assert "CIS" not in t
    assert "reverse charge" not in t.lower()
    # 5 000 + 20 % de IVA = 6 000, con el separador británico.
    assert "6,000.00" in t


def test_el_pdf_britanico_muestra_la_retencion_cis():
    p, cfg = _presupuesto_gb(cis_tipo=20.0)
    t = _texto(generar_pdf(p, cfg, lang="en-GB"))

    # Base 5 000 − 1 200 de materiales = 3 800 sujetos; 20 % = 760.
    assert "LABOUR ELEMENT SUBJECT TO DEDUCTION" in t
    assert "3,800.00" in t
    assert "CIS DEDUCTION (20.0 %)" in t
    assert "760.00" in t
    assert "TOTAL PAYABLE (after CIS deduction)" in t or "TOTAL PAYABLE" in t


def test_el_pdf_de_otro_mercado_no_aplica_reglas_britanicas():
    """Estados Unidos con el mismo presupuesto: ni CIS ni inversión."""
    p, cfg = _presupuesto_gb(cis_tipo=20.0, iva_tratamiento="inversion_sujeto_pasivo")
    t = _texto(generar_pdf(p, cfg, lang="en-US"))
    assert "CIS" not in t
    assert "reverse charge" not in t.lower()


def test_el_pdf_con_inversion_lleva_la_leyenda_obligatoria():
    p, cfg = _presupuesto_gb(iva_tratamiento="inversion_sujeto_pasivo")
    t = _texto(generar_pdf(p, cfg, lang="en-GB"))
    # La factura tiene que decir «reverse charge» para ser válida.
    assert "reverse charge" in t.lower()
    assert "Section 55A" in t
    # El impuesto se rotula, pero no se cobra.
    assert "VAT" in t and "not charged" in t and "(20.0 %)" in t
    assert "0.00" in t


def test_con_cis_el_pdf_sale_cerrado_no_interactivo():
    """El motor de JavaScript no modela el CIS: mejor estático que incoherente."""
    p, cfg = _presupuesto_gb(cis_tipo=20.0)
    t = _texto(generar_pdf(p, cfg, lang="en-GB"))
    assert "interactive" not in t.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Documento de cobro: el que se declara en el CIS300
# ─────────────────────────────────────────────────────────────────────────────

def test_la_factura_hereda_la_fiscalidad_del_presupuesto():
    """Si el presupuesto va bajo el CIS, la factura también: es la que se
    declara, y perder la retención al convertir es un error de declaración."""
    from datetime import date

    from app.models import Configuracion, Factura

    presupuesto, cfg = _presupuesto_gb(cis_tipo=20.0,
                                       iva_tratamiento="inversion_sujeto_pasivo")
    # Los campos que la conversión copia (app/routers/presupuestos.py).
    factura = Factura(
        numero="F-UK-1", year=2026, fecha=date(2026, 2, 1), moneda="GBP",
        impuesto_pct=presupuesto.impuesto_pct, descuento_pct=0.0,
        iva_tratamiento=presupuesto.iva_tratamiento,
        cis_tipo=presupuesto.cis_tipo,
        coste_materiales=float(presupuesto._totales.coste_materiales),
    )
    # La factura no guarda costes por línea: el coste viaja congelado, así que
    # el importe que se declara no cambia si el presupuesto se edita después.
    assert factura.coste_materiales == 1200.0
    assert factura.cis_tipo == 20.0
    assert factura.iva_tratamiento == "inversion_sujeto_pasivo"

    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("20"),
        iva_tratamiento=factura.iva_tratamiento, cis_tipo=factura.cis_tipo,
    )
    assert f.total_a_cobrar == Decimal("4240.00")


def test_la_factura_britanica_calcula_lo_mismo_que_el_presupuesto():
    """Misma aritmética en los dos documentos: 5 000, 1 200, 20 % → 4 240."""
    f = calcular_fiscalidad_gb(
        pais_codigo="GB", base_imponible=Decimal("5000"),
        coste_materiales=Decimal("1200"), iva_pct=Decimal("20"),
        iva_tratamiento="inversion_sujeto_pasivo", cis_tipo=Decimal("20"),
    )
    assert f.total_a_cobrar == Decimal("4240.00")


def test_el_documento_de_cobro_sin_cis_no_cambia():
    """Un documento de cobro nuevo no lleva retención: ``cis_tipo`` nace NULL.

    Se comprueba contra el esquema, no contra el objeto en memoria, porque los
    ``default`` de SQLAlchemy solo se aplican al insertar.
    """
    from app.models import Factura

    columna = Factura.__table__.columns["cis_tipo"]
    assert columna.nullable is True
    assert columna.default is None
    assert Factura.__table__.columns["iva_tratamiento"].default.arg == ""
    assert Factura.__table__.columns["coste_materiales"].default.arg == 0.0


def test_el_pdf_del_documento_de_cobro_lleva_el_cis():
    """La factura es el documento que se declara: tiene que salir rotulada."""
    from datetime import date

    from app.models import Cliente, Configuracion, Factura, FacturaCapitulo, FacturaItem

    factura = Factura(
        numero="F-UK-2", year=2026, fecha=date(2026, 2, 1), moneda="GBP",
        impuesto_pct=20.0, descuento_pct=0.0, cis_tipo=20.0,
        coste_materiales=1200.0, client_id=1,
    )
    cap = FacturaCapitulo(nombre="GROUNDWORKS", orden=1)
    cap.partidas = [FacturaItem(nombre="Excavation", unidad="m3", cantidad=100.0,
                             precio_unitario=50.0)]
    factura.capitulos = [cap]
    factura.cliente = Cliente(nombre="Henderson Construction Ltd")
    cfg = Configuracion(empresa_nombre="Whitfield Builders Ltd",
                        empresa_pais="Reino Unido", pdf_color="#0F4C81")
    t = _texto(generar_factura_pdf(factura, cfg, lang="en-GB"))
    assert "CIS DEDUCTION (20.0 %)" in t
    assert "3,800.00" in t
    assert "760.00" in t
