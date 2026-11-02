"""El catálogo sembrado cotiza al precio de su mercado, no al de Caracas.

El catálogo propio sale de ``basedatos_partidas/datos/recursos.json``
—«MONEDA: USD. ÁMBITO: Venezuela»— y se siembra igual para los 22 mercados.
Medido el 02/11/2026, el precio base se queda corto entre 2 y 3 veces en España
y entre 4 y 5 en Estados Unidos: el contratista pierde dinero en cada
presupuesto y los dos documentos tienen el mismo aspecto de estar bien.

Estas pruebas fijan:

* el precio sale de la matriz del país y coincide con la ficha publicada;
* el desglose suma el precio, para que el PDF no mienta;
* el margen que ve el editor es el real, no el 100 % de un coste en cero;
* cuando no hay dato **no se inventa** un precio;
* las unidades imperiales no multiplican el precio por 10,76.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Partida
from app.services.catalogo_propio import sembrar_catalogo_propio
from app.services.precios_partidas import (
    _complementarios_pct,
    _es_fila_de_recurso,
    _filas_de_la_partida,
    _margen_publicado,
    precio_de_partida,
)

ALICATADO = "12.03.01.010"
INODORO = "09.01.04.010"
DEMOLICION = "02.04.01.010"


@pytest.fixture(scope="module")
def catalogo():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    db = sessionmaker(bind=motor)()
    sembrar_catalogo_propio(db)
    yield db
    db.close()
    motor.dispose()


@pytest.fixture(scope="module")
def alicatado(catalogo):
    return catalogo.query(Partida).filter(Partida.codigo_interno == ALICATADO).one()


# ---------------------------------------------------------------------------
# El precio del mercado
# ---------------------------------------------------------------------------


def test_el_precio_sale_de_la_matriz_del_pais_no_del_catalogo_base(alicatado):
    """El mismo código cuesta distinto en cada mercado, en su moneda."""
    es = precio_de_partida(alicatado, pais="España", moneda_documento="EUR")
    mx = precio_de_partida(alicatado, pais="México", moneda_documento="MXN")
    us = precio_de_partida(alicatado, pais="Estados Unidos", moneda_documento="USD")

    for resultado in (es, mx, us):
        assert resultado.origen == "mercado"
    assert (es.moneda, mx.moneda, us.moneda) == ("EUR", "MXN", "USD")
    assert es.precio != mx.precio
    assert es.precio != us.precio
    # El catálogo base son 10,11 USD: el precio español no puede ser eso.
    assert es.precio > 20


def test_el_precio_coincide_al_centimo_con_la_ficha_publicada(alicatado):
    """No puede haber un precio que se anuncie y otro que se cobre."""
    from app.services import precios_publicos as pp

    indice = pp._indice("ES")
    publicada = indice["partidas"][indice["por_codigo"][ALICATADO]]["pu"]
    resultado = precio_de_partida(alicatado, pais="ES", moneda_documento="EUR")
    assert resultado.precio == pytest.approx(publicada, abs=0.01)


@pytest.mark.parametrize(
    "pais, moneda, minimo",
    [
        ("España", "EUR", 20),
        ("México", "MXN", 250),
        ("Estados Unidos", "USD", 40),
    ],
)
def test_el_precio_nunca_es_el_del_catalogo_base(catalogo, pais, moneda, minimo):
    """El fallo que se corrige: en todos los mercados el base se queda corto."""
    partida = catalogo.query(Partida).filter(Partida.codigo_interno == ALICATADO).one()
    resultado = precio_de_partida(partida, pais=pais, moneda_documento=moneda)
    assert resultado.origen == "mercado"
    assert resultado.precio > minimo


def test_un_mercado_en_dolares_tambien_usa_su_matriz(alicatado):
    """Ecuador, Panamá y El Salvador tienen precios propios aunque usen USD.

    Es la trampa de este módulo: si el disparador fuera «la moneda no es USD»,
    el catálogo base se tomaría por precio local y Ecuador seguiría cotizando
    a 10,11 en vez de a 7,89.
    """
    ecuador = precio_de_partida(alicatado, pais="Ecuador", moneda_documento="USD")
    assert ecuador.origen == "mercado"
    assert ecuador.moneda == "USD"
    assert ecuador.precio != alicatado.precio_unitario


def test_la_moneda_del_documento_manda(alicatado):
    """Un presupuesto en pesos no puede llevar un importe en euros."""
    resultado = precio_de_partida(
        alicatado, pais="España", moneda_documento="MXN", tasa=17.06
    )
    assert resultado.moneda == "MXN"
    # 27,46 EUR = 30,90 USD = 527,20 MXN. Etiquetar 27,46 como pesos es el
    # fallo que esto vigila.
    assert resultado.precio == pytest.approx(527.20, abs=1.0)


def test_sin_tasa_verificada_no_se_cambia_la_etiqueta(alicatado):
    """Sin tasa no se convierte: se dice en qué moneda está el número."""
    resultado = precio_de_partida(
        alicatado, pais="España", moneda_documento="MXN", tasa=None
    )
    # O se queda en EUR con un número real, o en MXN con una tasa real.
    if resultado.moneda == "MXN":
        assert resultado.precio > 100
    else:
        assert resultado.moneda == "EUR"


def test_la_jerga_del_nombre_ya_viene_del_pais(alicatado):
    """El precio y el nombre son del mismo mercado, no uno de cada."""
    from app.services.traduccion import traducir

    es = traducir(alicatado.nombre, "ES").lower()
    mx = traducir(alicatado.nombre, "MX").lower()
    assert es != mx
    assert "alicatado" in es
    assert "alicatado" not in mx


# ---------------------------------------------------------------------------
# Unidades: el error que multiplicaba por 10,76
# ---------------------------------------------------------------------------


def test_estados_unidos_no_multiplica_el_precio_por_la_conversion_de_area(alicatado):
    """La matriz publica en ``sq ft`` y el catálogo guarda ``m2``.

    El precio del recurso hay que convertirlo (``lb`` → ``kg``), pero el
    rendimiento guardado **ya está** por ``m2``. Convertirlo otra vez daba
    508,98 USD el m² en vez de 47,29.
    """
    resultado = precio_de_partida(
        alicatado, pais="Estados Unidos", moneda_documento="USD", con_desglose=True
    )
    assert resultado.precio == pytest.approx(47.29, abs=0.05)


def test_la_ruta_rapida_y_la_completa_dan_el_mismo_precio(alicatado):
    """El editor usa la rápida y el presupuesto la completa: no pueden diferir."""
    for pais, moneda in (("España", "EUR"), ("México", "MXN"), ("Estados Unidos", "USD")):
        rapida = precio_de_partida(
            alicatado, pais=pais, moneda_documento=moneda, con_desglose=False
        )
        completa = precio_de_partida(
            alicatado, pais=pais, moneda_documento=moneda, con_desglose=True
        )
        assert rapida.precio == pytest.approx(completa.precio, abs=0.01), pais


def test_los_precios_de_recurso_respetan_su_unidad(catalogo):
    """El adhesivo se publica en libras y se guarda en kilos.

    La línea va a precio de venta (el coste con su parte de margen), así que
    se comprueba la relación: 0,4173 USD/lb son 0,92 USD/kg de coste y
    0,92 × 1,35 = 1,24 USD/kg en el desglose que ve el cliente.
    """
    partida = catalogo.query(Partida).filter(Partida.codigo_interno == ALICATADO).one()
    resultado = precio_de_partida(
        partida, pais="Estados Unidos", moneda_documento="USD"
    )
    adhesivo = next(f for f in resultado.filas if f["codigo"] == "MT-ADH-C2TE")
    assert adhesivo["unidad"] == "kg"
    assert adhesivo["precio"] == pytest.approx(0.92 * 1.35, abs=0.02)


def test_el_desglose_que_ve_el_cliente_es_el_de_venta(catalogo):
    """El importe de cada línea incluye su parte de margen, como en la ficha."""
    partida = catalogo.query(Partida).filter(Partida.codigo_interno == ALICATADO).one()
    resultado = precio_de_partida(partida, pais="España", moneda_documento="EUR")
    # El coste real es ~20,14 EUR y el precio 27,46: las líneas son de venta.
    assert sum(f["importe"] for f in resultado.filas) == pytest.approx(
        resultado.precio, rel=0.01
    )
    assert resultado.coste_total == pytest.approx(20.14, abs=0.5)
    assert resultado.coste_total < resultado.precio


# ---------------------------------------------------------------------------
# El desglose tiene que cuadrar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("codigo", [ALICATADO, INODORO, DEMOLICION])
@pytest.mark.parametrize("pais, moneda", [("España", "EUR"), ("México", "MXN")])
def test_el_desglose_suma_el_precio_de_venta(catalogo, codigo, pais, moneda):
    """Si las líneas no suman el precio, el PDF miente al cliente."""
    partida = catalogo.query(Partida).filter(Partida.codigo_interno == codigo).one()
    resultado = precio_de_partida(partida, pais=pais, moneda_documento=moneda)
    assert resultado.filas, "sin desglose no hay nada que enseñar"
    assert sum(f["importe"] for f in resultado.filas) == pytest.approx(
        resultado.precio, rel=0.01
    )


def test_el_margen_que_ve_el_editor_es_el_real(catalogo):
    """Coste en cero daría un beneficio del 100 % y el editor lo creería."""
    partida = catalogo.query(Partida).filter(Partida.codigo_interno == ALICATADO).one()
    resultado = precio_de_partida(partida, pais="España", moneda_documento="EUR")
    assert resultado.coste_total and resultado.coste_total > 0
    assert 0.2 < resultado.margen_pct < 0.35, resultado.margen_pct


def test_el_margen_se_deduce_del_precio_publicado(catalogo):
    """El artefacto no guarda el margen; se deduce de sus propias cifras."""
    from app.services import precios_publicos as pp

    indice = pp._indice("ES")
    ficha = indice["partidas"][indice["por_codigo"][ALICATADO]]
    assert _margen_publicado(ficha) == pytest.approx(0.35, abs=0.01)


def test_la_linea_de_cierre_no_se_trata_como_recurso(catalogo):
    """«Costes directos complementarios» no es un recurso y no tiene código."""
    partida = catalogo.query(Partida).filter(Partida.codigo_interno == ALICATADO).one()
    filas = _filas_de_la_partida(partida)
    cierre = [f for f in filas if "complementario" in str(f.get("grupo", "")).lower()]
    assert cierre, "el catálogo trae la fila de cierre"
    for fila in cierre:
        assert not _es_fila_de_recurso(fila)
    assert _complementarios_pct(filas) > 0


# ---------------------------------------------------------------------------
# Cuando no hay dato, no se inventa
# ---------------------------------------------------------------------------


def test_venezuela_se_queda_con_el_catalogo_base(alicatado):
    """Venezuela no tiene matriz: su precio base USD es el bueno, no un error."""
    resultado = precio_de_partida(alicatado, pais="Venezuela", moneda_documento="USD")
    assert resultado.origen == "catalogo"
    assert resultado.precio == alicatado.precio_unitario
    assert resultado.aviso
    assert "Venezuela" in resultado.aviso


def test_un_pais_sin_matriz_no_finge_un_precio(alicatado):
    resultado = precio_de_partida(alicatado, pais="Narnia", moneda_documento="USD")
    assert resultado.origen == "catalogo"
    assert resultado.aviso


def test_una_partida_sin_codigo_de_catalogo_no_hereda_precio(catalogo):
    """Una partida propia del usuario no puede llevar el precio de otra."""
    propia = Partida(nombre="Trabajo mío", precio_unitario=123.0, unidad="ud")
    resultado = precio_de_partida(propia, pais="España", moneda_documento="EUR")
    assert resultado.origen == "catalogo"
    assert resultado.precio == 123.0


def test_una_partida_que_el_mercado_no_publica_conserva_su_precio(catalogo):
    """Las partidas sin descompuesto completo no reciben un precio inventado.

    La matriz descarta las que tienen menos de tres líneas o descripción
    corta. Se quedan con el precio base y con un aviso: mejor eso que un
    número inventado con el mismo aspecto de estar bien.
    """
    sin_matriz = (
        catalogo.query(Partida).filter(Partida.codigo_interno == "01.02.01.040").first()
    )
    assert sin_matriz is not None
    resultado = precio_de_partida(sin_matriz, pais="España", moneda_documento="EUR")
    assert resultado.origen == "catalogo"
    assert resultado.precio == sin_matriz.precio_unitario
    assert "revisa el precio" in resultado.aviso.lower()


# ---------------------------------------------------------------------------
# El editor
# ---------------------------------------------------------------------------


def test_el_indice_del_editor_lleva_el_precio_del_mercado(catalogo):
    from app.models import Configuracion
    from app.routers.common import (
        _indice_catalogo_para_editor,
        limpiar_cache_precios_mercado,
    )

    cfg = catalogo.query(Configuracion).first()
    if cfg is None:
        cfg = Configuracion(empresa_nombre="X")
        catalogo.add(cfg)
    cfg.empresa_pais = "México"
    cfg.moneda_default = "MXN"
    cfg.tasa_cambio = 17.06
    catalogo.commit()
    limpiar_cache_precios_mercado()
    try:
        indice = _indice_catalogo_para_editor(catalogo, "MXN", 17.06)
        fila = next(d for d in indice if d["codigo"] == ALICATADO)
        assert fila["origen_precio"] == "mercado"
        assert fila["moneda"] == "MXN"
        assert fila["precio"] > 250, "10 pesos no son el precio mexicano"
        en_mercado = sum(1 for d in indice if d.get("origen_precio") == "mercado")
        assert en_mercado > len(indice) * 0.6
    finally:
        limpiar_cache_precios_mercado()


def test_el_indice_no_arrastra_el_precio_entre_organizaciones(catalogo):
    """La caché es de módulo: no puede servir el precio de otra empresa."""
    from app.models import Configuracion
    from app.routers.common import (
        _indice_catalogo_para_editor,
        limpiar_cache_precios_mercado,
    )

    cfg = catalogo.query(Configuracion).first()
    cfg.empresa_pais = "España"
    cfg.moneda_default = "EUR"
    cfg.tasa_cambio = 0.8886
    catalogo.commit()
    limpiar_cache_precios_mercado()
    es = next(
        d
        for d in _indice_catalogo_para_editor(catalogo, "EUR", 0.8886)
        if d["codigo"] == ALICATADO
    )
    cfg.empresa_pais = "Estados Unidos"
    cfg.moneda_default = "USD"
    cfg.tasa_cambio = 1.0
    catalogo.commit()
    limpiar_cache_precios_mercado()
    us = next(
        d
        for d in _indice_catalogo_para_editor(catalogo, "USD", 1.0)
        if d["codigo"] == ALICATADO
    )
    assert es["precio"] != us["precio"]
    assert es["moneda"] != us["moneda"]
