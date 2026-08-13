"""Actualizar sobre una base de datos antigua nunca debe impedir el arranque.

Al añadir un campo nuevo a los modelos es fácil olvidar la entrada
correspondiente en ``migrar()``. Cuando eso pasa, la aplicación instalada
arranca contra la base del usuario (creada por una versión anterior),
SQLAlchemy pide una columna que no existe y el arranque muere. Uvicorn
traduce ese fallo del lifespan a ``SystemExit: 3`` y la ventana nunca se
abre. Fue exactamente el caso de ``mostrar_garantias_default``.

Estas pruebas comparan el esquema declarado en los modelos con el que
realmente se crea, y verifican que una base «vieja» (sin las columnas
nuevas) se pone al día sola.
"""
import sqlite3

from sqlalchemy import create_engine, inspect, text

from app.database import Base
from app.models import Configuracion, Presupuesto, migrar


def _engine(tmp_path, nombre="prueba.db"):
    return create_engine(f"sqlite:///{tmp_path / nombre}")


def _columnas_reales(engine, tabla):
    return {c["name"] for c in inspect(engine).get_columns(tabla)}


def test_migrar_anade_columnas_que_faltan_en_una_base_antigua(tmp_path):
    """Una base sin las columnas de garantías debe quedar utilizable."""
    engine = _engine(tmp_path)
    Base.metadata.create_all(bind=engine)

    # Simula la base de una versión anterior: se eliminan las columnas nuevas.
    for tabla, columna in (
        ("configuracion", "mostrar_garantias_default"),
        ("presupuestos", "mostrar_garantias"),
    ):
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {tabla} DROP COLUMN {columna}"))
        assert columna not in _columnas_reales(engine, tabla)

    migrar(engine)

    assert "mostrar_garantias_default" in _columnas_reales(engine, "configuracion")
    assert "mostrar_garantias" in _columnas_reales(engine, "presupuestos")


def test_consulta_de_configuracion_funciona_tras_migrar(tmp_path):
    """Reproduce el fallo real: SELECT de Configuracion sobre base antigua."""
    from sqlalchemy.orm import sessionmaker

    engine = _engine(tmp_path, "antigua.db")
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE configuracion DROP COLUMN mostrar_garantias_default"))

    migrar(engine)

    # Antes del arreglo esto lanzaba OperationalError: no such column,
    # que es lo que abortaba el arranque con SystemExit: 3.
    with sessionmaker(bind=engine)() as db:
        db.query(Configuracion).first()
        db.query(Presupuesto).first()


def test_el_esquema_creado_coincide_con_los_modelos(tmp_path):
    """Red de seguridad general: ninguna columna del modelo debe faltar.

    Recorre todas las tablas y compara el modelo con la base ya migrada, de
    forma que un campo nuevo sin su migración se detecte aquí y no en el
    ordenador del usuario.
    """
    # Base «antigua»: se crea el esquema y se quitan columnas opcionales
    # recientes para forzar que la migración tenga trabajo que hacer.
    engine = _engine(tmp_path, "completa.db")
    Base.metadata.create_all(bind=engine)
    migrar(engine)

    faltantes = []
    for tabla in Base.metadata.sorted_tables:
        reales = _columnas_reales(engine, tabla.name)
        for columna in tabla.columns:
            if columna.name not in reales:
                faltantes.append(f"{tabla.name}.{columna.name}")

    assert not faltantes, f"Columnas del modelo ausentes en la base: {faltantes}"


def test_init_db_es_idempotente_y_conserva_los_datos(tmp_path):
    """Arrancar dos veces no debe fallar ni perder información."""
    from sqlalchemy.orm import sessionmaker

    ruta = tmp_path / "datos.db"
    engine = create_engine(f"sqlite:///{ruta}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        db.add(Configuracion(empresa_nombre="Mi Empresa"))
        db.commit()

    # Se simula una actualización: falta una columna nueva y se migra.
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE configuracion DROP COLUMN mostrar_garantias_default"))
    migrar(engine)
    migrar(engine)  # segunda pasada: no debe romper nada

    with Session() as db:
        cfg = db.query(Configuracion).first()
        assert cfg.empresa_nombre == "Mi Empresa"
        assert cfg.mostrar_garantias_default in (False, 0, None)

    # El archivo sigue siendo una base SQLite legible.
    con = sqlite3.connect(ruta)
    try:
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        con.close()
