"""Uso real de presupuestos del cliente en el panel (solo lectura, B7).

El panel ya veía cifras de uso; aquí se fija lo nuevo: la ventana de lectura
del superadmin sobre presupuestos, partidas y precios reales, con detección de
precios modificados frente al catálogo y de partidas que necesitan ajuste.

Se prueba sobre SQLite con el mismo servicio que corre en PostgreSQL (allí las
consultas entran por funciones SECURITY DEFINER, verificadas por separado).
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Capitulo,
    Cliente,
    Organizacion,
    Partida,
    Presupuesto,
    PresupuestoItem,
)
from app.services.panel_contextos import ORDENES, ordenar_filas
from app.services.panel_presupuestos import (
    detalle_presupuesto_cliente,
    resumen_uso_presupuestos,
)


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _org(db, nombre="Constructora Beta", slug="beta-b", alta=None):
    org = Organizacion(nombre=nombre, slug=slug, created_at=alta or datetime(2026, 7, 1))
    db.add(org)
    db.commit()
    return org


def _catalogo(db, org, nombre="Pintura vinílica", precio=5.0):
    partida = Partida(
        nombre=nombre, unidad="m2", precio_unitario=precio,
        organizacion_id=org.id, coste_materiales=2.0,
    )
    db.add(partida)
    db.commit()
    return partida


def _presupuesto(db, org, *, numero="P-2026-001", es_demo=False, moneda="USD",
                 tipo_cambio=None, total=100.0):
    cliente = Cliente(nombre="Cliente Final", organizacion_id=org.id)
    db.add(cliente)
    db.flush()
    p = Presupuesto(
        numero=numero, year=2026, fecha=date(2026, 9, 1), titulo="Obra Centro",
        moneda=moneda, moneda_base="USD", tipo_cambio=tipo_cambio,
        estado="enviado", total_calculado=total, es_demo=es_demo,
        client_id=cliente.id, organizacion_id=org.id,
    )
    db.add(p)
    db.flush()
    cap = Capitulo(nombre="PINTURA", orden=1, presupuesto_id=p.id)
    db.add(cap)
    db.flush()
    return p, cap


def _item(db, cap, *, nombre, precio, partida=None, cantidad=1.0, moneda="USD",
          coste_materiales=0.0, orden=1):
    item = PresupuestoItem(
        capitulo_id=cap.id, nombre=nombre, unidad="m2", cantidad=cantidad,
        precio_unitario=precio, moneda=moneda,
        partida_catalogo_id=partida.id if partida else None,
        coste_materiales=coste_materiales, orden=orden,
        organizacion_id=cap.presupuesto.organizacion_id,
    )
    db.add(item)
    db.commit()
    return item


def _fila(org):
    """Fila mínima del directorio para probar el orden."""
    return {"organizacion": org, "plan_label": "Anual", "ingresos": 89.0, "estado": "activa"}


def test_orden_por_fecha_de_alta_en_el_directorio():
    from types import SimpleNamespace

    engine, db = _db()
    try:
        vieja = _org(db, "Vieja", "vieja", alta=datetime(2025, 1, 5))
        nueva = _org(db, "Nueva", "nueva", alta=datetime(2026, 8, 12))
        assert "alta" in ORDENES

        # Fila sin fecha de alta (histórico): debe quedar al final siempre.
        sin_fecha = SimpleNamespace(nombre="Sin Fecha")
        filas = [_fila(nueva), _fila(sin_fecha), _fila(vieja)]
        ascendente = ordenar_filas(filas, "alta", "asc")
        assert [f["organizacion"].nombre for f in ascendente] == ["Vieja", "Nueva", "Sin Fecha"]
        descendente = ordenar_filas(filas, "alta", "desc")
        assert [f["organizacion"].nombre for f in descendente] == ["Nueva", "Vieja", "Sin Fecha"]
    finally:
        db.close()
        engine.dispose()


def test_resumen_detecta_modificadas_personalizadas_y_ajustes():
    engine, db = _db()
    try:
        org = _org(db)
        partida = _catalogo(db, org)
        p, cap = _presupuesto(db, org)
        # 1) Igual al catálogo: no modificada.
        _item(db, cap, nombre="Pintura igual", precio=5.0, partida=partida)
        # 2) Precio cambiado (+30 %): modificada.
        _item(db, cap, nombre="Pintura cara", precio=6.5, partida=partida, orden=2)
        # 3) Escrita a mano: personalizada, no modificada.
        _item(db, cap, nombre="Pintura propia", precio=8.0, orden=3)
        # 4) Bajo coste y sin margen: modificada + ajuste recomendado.
        _item(db, cap, nombre="Pintura regalada", precio=2.0, partida=partida,
              coste_materiales=3.0, orden=4)
        db.commit()

        datos = resumen_uso_presupuestos(db, org.id)
        totales = datos["totales"]
        assert totales["presupuestos"] == 1
        assert totales["partidas"] == 4
        assert totales["modificadas"] == 2
        assert totales["personalizadas"] == 1
        assert totales["ajustes"] == 1
        assert totales["partidas_unicas"] == 4

        assert datos["por_estado"] == {"enviado": 1}
        assert datos["presupuestos"][0]["numero"] == "P-2026-001"
        assert datos["presupuestos"][0]["modificadas"] == 2

        top = datos["top_modificadas"]
        assert len(top) == 1
        assert top[0]["nombre"] == "Pintura vinílica"
        assert top[0]["veces"] == 2
        # Desviación de mayor magnitud, con signo (−60 % = muy por debajo del catálogo).
        assert top[0]["desviacion_max"] == pytest.approx(-60.0, abs=0.5)

        ajustes = datos["ajustes"]
        assert len(ajustes) == 1
        assert ajustes[0]["nombre"] == "Pintura regalada"
        assert "margen_negativo" in ajustes[0]["motivos_ajuste"]
    finally:
        db.close()
        engine.dispose()


def test_compara_precios_en_la_moneda_del_presupuesto():
    """Catálogo en USD, presupuesto en COP: la comparación usa la tasa."""
    engine, db = _db()
    try:
        org = _org(db)
        partida = _catalogo(db, org, precio=10.0)  # 10 USD/m2
        p, cap = _presupuesto(db, org, numero="P-2026-COP", moneda="COP", tipo_cambio=3900.0)
        # 10 USD × 3900 = 39.000 COP: exactamente el catálogo → no modificada.
        _item(db, cap, nombre="Piso igual", precio=39_000.0, partida=partida,
              moneda="COP")
        # 45.000 COP (≈15,4 % más): modificada.
        _item(db, cap, nombre="Piso caro", precio=45_000.0, partida=partida,
              moneda="COP", orden=2)
        db.commit()

        datos = resumen_uso_presupuestos(db, org.id)
        assert datos["totales"]["modificadas"] == 1
        fila = datos["presupuestos"][0]
        assert fila["moneda"] == "COP"
        # El detalle expone el precio del catálogo convertido a COP.
        detalle = detalle_presupuesto_cliente(db, org.id, p.id)
        piso_igual = next(i for i in detalle["capitulos"][0]["partidas"] if i["nombre"] == "Piso igual")
        piso_caro = next(i for i in detalle["capitulos"][0]["partidas"] if i["nombre"] == "Piso caro")
        assert piso_igual["modificado"] is False
        assert piso_igual["catalogo_precio"] == pytest.approx(39_000.0, abs=0.5)
        assert piso_caro["modificado"] is True
        assert piso_caro["desviacion_pct"] == pytest.approx(
            (45_000 - 39_000) / 39_000 * 100, abs=0.5
        )
    finally:
        db.close()
        engine.dispose()


def test_los_presupuestos_de_demostracion_no_ensucian_el_analisis():
    engine, db = _db()
    try:
        org = _org(db)
        partida = _catalogo(db, org)
        p_real, cap_real = _presupuesto(db, org, numero="P-2026-REAL")
        _item(db, cap_real, nombre="Pintura real", precio=5.0, partida=partida)
        p_demo, cap_demo = _presupuesto(db, org, numero="P-2026-DEMO", es_demo=True)
        _item(db, cap_demo, nombre="Pintura demo", precio=5.0, partida=partida)
        db.commit()

        datos = resumen_uso_presupuestos(db, org.id)
        assert datos["totales"]["presupuestos"] == 1
        assert datos["totales"]["demo"] == 1
        assert datos["totales"]["partidas"] == 1
        demos = [c for c in datos["presupuestos"] if c["es_demo"]]
        assert len(demos) == 1 and demos[0]["numero"] == "P-2026-DEMO"
    finally:
        db.close()
        engine.dispose()


def test_detalle_devuelve_none_si_no_es_del_cliente():
    engine, db = _db()
    try:
        org = _org(db, "Uno", "uno")
        otro = _org(db, "Otro", "otro")
        p, _cap = _presupuesto(db, org)
        assert detalle_presupuesto_cliente(db, otro.id, p.id) is None
        assert detalle_presupuesto_cliente(db, org.id, 9999) is None
    finally:
        db.close()
        engine.dispose()


def test_resumen_es_solo_lectura_no_crea_registros():
    engine, db = _db()
    try:
        from app.models import EventoAdmin

        org = _org(db)
        partida = _catalogo(db, org)
        p, cap = _presupuesto(db, org)
        _item(db, cap, nombre="Pintura", precio=5.0, partida=partida)
        db.commit()

        antes = db.query(EventoAdmin).count()
        resumen_uso_presupuestos(db, org.id)
        detalle_presupuesto_cliente(db, org.id, p.id)
        db.commit()
        assert db.query(EventoAdmin).count() == antes
        # El contenido no se modifica.
        assert db.query(PresupuestoItem).count() == 1
    finally:
        db.close()
        engine.dispose()


def test_migracion_defiende_la_lectura_con_operador():
    from pathlib import Path

    fuente = Path(
        "migrations/versions/f6d1a9c3e8b2_admin_uso_presupuestos_clientes.py"
    ).read_text(encoding="utf-8")
    assert "admin_presupuestos_cliente" in fuente
    assert "admin_presupuesto_items_cliente" in fuente
    assert "SECURITY DEFINER" in fuente
    assert "cotizat.es_operador" in fuente
    assert "GRANT EXECUTE" in fuente
    # Se cuelga de la cabeza vigente del grafo de migraciones.
    assert 'down_revision: Union[str, Sequence[str], None] = "d3e5f7a9c2b4"' in fuente
    # Nunca escribe en tenant: solo SELECT.
    for prohibido in (
        "INSERT INTO public.presupuestos",
        "UPDATE public.presupuestos",
        "DELETE FROM public.presupuestos",
        "INSERT INTO public.presupuesto_items",
    ):
        assert prohibido not in fuente
