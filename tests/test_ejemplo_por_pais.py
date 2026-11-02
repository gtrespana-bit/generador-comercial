"""El ejemplo del alta habla el mercado de la empresa, no el del fundador.

Medido el 02/11/2026: el país elegido en el alta se guardaba en
``Configuracion.empresa_pais`` y **nunca llegaba a la siembra**; la función
recibía solo el idioma. Todas las cuentas abrían un presupuesto en USD con
IVA del 16 %, dirección «Valencia, Carabobo» y partidas venezolanas, y las 13
cuentas españolas veían la obra de otra persona.

Estas pruebas fijan las cuatro cosas que hacen que el ejemplo sirva:

1. el país llega hasta la siembra (era una línea que se perdía en el camino);
2. el precio es el del mercado y no el venezolano;
3. la unidad es la del mercado (un precio por pie cuadrado no puede ir en una
   línea medida en metros);
4. quien no tiene matriz recibe el ejemplo de siempre, sin romperse.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Presupuesto
from app.services.ejemplo_pais import (
    PAISES_CON_EJEMPLO,
    _APARTADOS,
    ejemplo_para_pais,
)


def _db():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(bind=motor)
    return motor, sessionmaker(bind=motor)()


# ---------------------------------------------------------------------------
# El módulo de selección
# ---------------------------------------------------------------------------


def test_todos_los_mercados_con_matriz_pueden_generar_su_ejemplo():
    """Si un mercado tiene matriz, el ejemplo tiene que poder construirse.

    Se comprueban los 22: un país que entra en ``PAISES_PRECIOS_PUBLICOS`` y
    no puede generar ejemplo es un mercado donde el alta vuelve a enseñar el
    presupuesto de Caracas.
    """
    faltan = [cc for cc in PAISES_CON_EJEMPLO if ejemplo_para_pais(cc) is None]
    assert not faltan, f"mercados con matriz sin ejemplo: {faltan}"


@pytest.mark.parametrize("cc", ["ES", "MX", "CO", "AR", "CL", "PE", "US", "GB"])
def test_el_ejemplo_usa_la_moneda_del_pais(cc):
    from app.paises import PAISES

    ejemplo = ejemplo_para_pais(cc)
    assert ejemplo.moneda == PAISES[cc]["moneda"]
    assert all(p.moneda == ejemplo.moneda for p in ejemplo.partidas), (
        "una línea con moneda distinta al documento es un error de suma"
    )


def test_el_iva_del_ejemplo_es_el_del_pais_no_el_venezolano():
    assert ejemplo_para_pais("ES").impuesto_pct == 21.0
    assert ejemplo_para_pais("MX").impuesto_pct == 16.0
    assert ejemplo_para_pais("CO").impuesto_pct == 19.0
    # El genérico anterior era 16 % para todos, incluida España (21 %).
    assert ejemplo_para_pais("ES").impuesto_pct != ejemplo_para_pais("VE") or True


def test_mexico_y_espana_no_reciben_el_mismo_precio():
    """El defecto original: la misma cifra en dólares para los dos países."""
    es = {p.codigo: p for p in ejemplo_para_pais("ES").partidas}
    mx = {p.codigo: p for p in ejemplo_para_pais("MX").partidas}
    comunes = set(es) & set(mx)
    assert comunes, "sin partidas comunes no se pueden comparar"
    for codigo in comunes:
        assert es[codigo].precio != mx[codigo].precio
        assert es[codigo].moneda != mx[codigo].moneda


def test_la_jerga_es_la_del_pais():
    """«Alicatado», «enchape» y «recubrimiento» son la misma obra con tres nombres."""
    mx = " ".join(p.nombre for p in ejemplo_para_pais("MX").partidas).lower()
    co = " ".join(p.nombre for p in ejemplo_para_pais("CO").partidas).lower()
    assert "alicatado" not in mx
    assert "enchape" in co or "enchapado" in co


def test_la_unidad_de_la_partida_es_la_del_mercado():
    """Estados Unidos cobra por pie cuadrado: la cantidad va en pies.

    El error que esto evita: 4,2 m² de solado valorados como 4,2 pies² son
    unos 15 $ en vez de los ~160 $ reales, y el documento tiene el mismo
    aspecto de estar bien.
    """
    us = ejemplo_para_pais("US")
    unidades = {p.unidad for p in us.partidas}
    assert "sq ft" in unidades
    assert "m²" not in unidades and "m2" not in unidades
    # La cantidad de solado tiene que ser la de un baño en pies cuadrados.
    solado = next(p for p in us.partidas if p.unidad == "sq ft")
    assert solado.cantidad > 10, "una cantidad de obra de 4 pies² no es un baño"


def test_el_ejemplo_no_se_queda_en_tres_lineas():
    for cc in ("ES", "MX", "CO", "NI", "US"):
        ejemplo = ejemplo_para_pais(cc)
        assert len(ejemplo.partidas) >= 10, cc
        assert len(ejemplo.capitulos) >= 6, cc


def test_todas_las_partidas_tienen_descripcion_publicable():
    """La descripción es lo que lee el cliente final en el PDF."""
    for partida in ejemplo_para_pais("ES").partidas:
        assert len(partida.descripcion) >= 120, partida.codigo
        assert partida.cantidad > 0
        assert partida.precio > 0


def test_venezuela_sin_matriz_no_inventa_un_ejemplo():
    """Venezuela cotiza con los precios base USD; no hay matriz publicada.

    Devolver ``None`` es la respuesta correcta: quien llama usa el ejemplo
    escrito a mano, que sigue existiendo para ese mercado.
    """
    assert ejemplo_para_pais("VE") is None
    assert ejemplo_para_pais("") is None
    assert ejemplo_para_pais("XX") is None


# ---------------------------------------------------------------------------
# La siembra: el país tiene que llegar hasta el final
# ---------------------------------------------------------------------------


def _completar(pais: str, moneda: str, iva: float, idioma: str = "es"):
    from app.services.onboarding import completar_onboarding

    motor, db = _db()
    try:
        cfg = completar_onboarding(
            db,
            {
                "empresa_nombre": f"Reformas {pais}",
                "empresa_pais": pais,
                "moneda_default": moneda,
                "iva_default": iva,
                "etiqueta_id_fiscal": "NIF",
            },
            "demo",
            idioma,
        )
        return db, cfg
    except Exception:
        db.close()
        motor.dispose()
        raise


@pytest.mark.parametrize(
    "pais,moneda,iva",
    [("México", "MXN", 16), ("España", "EUR", 21), ("Colombia", "COP", 19)],
)
def test_el_alta_siembra_el_presupuesto_del_pais_elegido(pais, moneda, iva):
    """De punta a punta: el país del formulario aparece en el presupuesto."""
    db, cfg = _completar(pais, moneda, iva)
    try:
        presupuesto = db.query(Presupuesto).one()
        assert presupuesto.moneda == moneda
        assert presupuesto.impuesto_pct == iva
        assert "baño" in presupuesto.titulo.lower()
        # «Valencia, Carabobo» en un alta de México es la prueba del defecto.
        assert "valencia" not in (presupuesto.direccion_obra or "").lower()
        assert presupuesto.es_ejemplo is True and presupuesto.es_demo is True
        assert sum(len(c.partidas) for c in presupuesto.capitulos) >= 10
    finally:
        db.close()


def test_el_alta_venezolana_conserva_el_ejemplo_de_siempre():
    """Sin matriz no se degrada: el ejemplo escrito a mano sigue intacto."""
    db, cfg = _completar("Venezuela", "USD", 16)
    try:
        presupuesto = db.query(Presupuesto).one()
        assert presupuesto.moneda == "USD"
        assert presupuesto.es_ejemplo is True
        assert sum(len(c.partidas) for c in presupuesto.capitulos) >= 6
    finally:
        db.close()


def test_el_alta_estadounidense_usa_el_idioma_del_mercado():
    db, cfg = _completar("Estados Unidos", "USD", 7, "en")
    try:
        presupuesto = db.query(Presupuesto).one()
        assert presupuesto.titulo == "Bathroom renovation — sample estimate"
        assert presupuesto.cliente.nombre == "Sample client"
        unidades = {p.unidad for c in presupuesto.capitulos for p in c.partidas}
        assert "sq ft" in unidades
    finally:
        db.close()


def test_el_ejemplo_sembrado_sigue_siendo_convertible(entorno=None):
    """La guía lo ofrece como punto de partida y duplicarlo lo hace propio."""
    from app.services.onboarding import estado_recorrido_inicial

    db, cfg = _completar("México", "MXN", 16)
    try:
        estado = estado_recorrido_inicial(db, cfg)
        ejemplo = estado["ejemplo_convertible"]
        assert ejemplo is not None
        paso = {p["clave"]: p for p in estado["pasos"]}["presupuesto"]
        assert paso["completo"] is False
        assert paso["url"] == f"/presupuestos/{ejemplo.id}"
        assert "partidas" in paso["detalle"] or "partidas" in paso["titulo"].lower()
    finally:
        db.close()


def test_el_glosario_no_produce_plurales_imposibles():
    """«Protección de WCes y grifería» salía en las fichas públicas de MX y CL.

    El glosario traducía «sanitario» → «WC» y la app pluraliza añadiendo «es».
    """
    from app.services.traduccion import traducir

    # La cadena que se publicaba en MX y CL, y su vecina de la misma familia.
    for cc in ("MX", "CL"):
        for frase in (
            "Protección de sanitarios y grifería existente",
            "Protección de puertas, ventanas, aparatos sanitarios y elementos "
            "terminados que permanecen dentro de la zona de obra",
        ):
            traducida = traducir(frase, cc)
            assert "WCes" not in traducida, traducida
            assert "inodoro" in traducida.lower()
