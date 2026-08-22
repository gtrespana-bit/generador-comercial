"""Regresión del 500 «current transaction is aborted» en /inicio (22/08/2026).

Síntoma
-------
``/inicio`` devolvía 500 en el despliegue web::

    psycopg.errors.InFailedSqlTransaction: current transaction is aborted,
    commands ignored until end of transaction block
    [SQL: SELECT count(*) ... FROM clientes WHERE clientes.es_demo IS false ...]

El traceback señalaba ``onboarding.py:151`` (contar clientes reales), una
consulta trivialmente correcta: era la **víctima**, no la causa.

Causa raíz
----------
``BOOLEAN DEFAULT 0``. PostgreSQL es estricto con los tipos y rechaza un
literal entero como valor por defecto de una columna booleana::

    DatatypeMismatch: column "recorrido_inicial_oculto" is of type boolean
    but default expression is of type integer

Ese SQL estaba en cuatro sitios (la migración ``b1c2d3e4f5a6`` y los tres
hotfix de runtime), así que:

1. ``alembic upgrade head`` abortaba → la columna nunca se creaba y la base se
   quedaba clavada en el head anterior (``c3e9a1b7d4f2``).
2. Cada ``SELECT configuracion.*`` fallaba con ``UndefinedColumn``.
3. Los ``except Exception`` defensivos se tragaban ese error **sin hacer
   rollback**, dejando la transacción de psycopg en estado ``aborted``.
4. La siguiente consulta del handler —contar clientes— moría con
   ``InFailedSqlTransaction``.

Estas pruebas cubren las dos mitades del arreglo (el DDL válido y el rollback)
sin necesitar un PostgreSQL: la de tipos compila el SQL con el dialecto real y
la de rollback usa un doble que simula el fallo. ``tests/test_rls_postgres.py``
añade la verificación end-to-end contra una base real.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

#: ``BOOLEAN``/``BOOL`` seguido de ``DEFAULT 0|1`` (el literal entero que
#: PostgreSQL rechaza). Se admite ``DEFAULT true/false``.
BOOLEAN_CON_ENTERO = re.compile(r"BOOL(?:EAN)?\s+DEFAULT\s+[01]\b", re.IGNORECASE)

#: DDL que se ejecuta contra PostgreSQL. ``app/models.py`` tiene además tablas
#: y ALTERs exclusivos de SQLite (``migrar()``), donde ``DEFAULT 0`` es válido;
#: por eso aquí solo se revisan las sentencias que pueden llegar a PG.
FUENTES_DDL_POSTGRES = (
    "app/database.py",
    "app/routers/common.py",
    "app/routers/auth.py",
    "app/models.py",
)


def _sentencias_alter_postgres(texto: str) -> list[str]:
    """ALTERs con ``IF NOT EXISTS``: sintaxis que solo entiende PostgreSQL."""
    return [
        linea.strip()
        for linea in texto.splitlines()
        if "ADD COLUMN IF NOT EXISTS" in linea.upper()
    ]


@pytest.mark.parametrize("ruta", FUENTES_DDL_POSTGRES)
def test_ningun_ddl_de_postgres_usa_boolean_default_entero(ruta):
    """``BOOLEAN DEFAULT 0`` rompe en PostgreSQL con ``DatatypeMismatch``."""
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    ofensivas = [
        sentencia
        for sentencia in _sentencias_alter_postgres(texto)
        if BOOLEAN_CON_ENTERO.search(sentencia)
    ]
    assert not ofensivas, (
        f"{ruta}: PostgreSQL rechaza «BOOLEAN DEFAULT 0» (DatatypeMismatch). "
        "Usa DEFAULT false / DEFAULT true:\n  " + "\n  ".join(ofensivas)
    )


def test_ninguna_migracion_usa_un_entero_como_defecto_booleano():
    """En Alembic el defecto booleano debe ser ``sa.false()``/``sa.true()``.

    ``server_default=sa.text("0")`` sobre ``sa.Boolean()`` compila a
    ``DEFAULT 0`` y aborta ``alembic upgrade head`` en PostgreSQL, que fue lo
    que dejó la base de producción sin la columna.
    """
    sospechosas = []
    for ruta in sorted((RAIZ / "migrations" / "versions").glob("*.py")):
        texto = ruta.read_text(encoding="utf-8")
        # Bloques `sa.Column(...)` que declaren Boolean y un server_default.
        for bloque in re.findall(r"sa\.Column\((?:[^()]|\([^()]*\))*\)", texto, re.S):
            if "sa.Boolean" not in bloque or "server_default" not in bloque:
                continue
            defecto = re.search(r"server_default\s*=\s*([^,\n]+)", bloque)
            if defecto and re.search(r"""sa\.text\(\s*["'][01]["']\s*\)|["'][01]["']""", defecto.group(1)):
                sospechosas.append(f"{ruta.name}: {defecto.group(1).strip()}")

    assert not sospechosas, (
        "Defecto entero sobre columna booleana (PostgreSQL: DatatypeMismatch). "
        "Usa server_default=sa.false():\n  " + "\n  ".join(sospechosas)
    )


def test_la_migracion_de_la_guia_compila_su_defecto_para_postgres():
    """El DDL real de ``b1c2d3e4f5a6`` debe decir ``DEFAULT false`` en PG."""
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql, sqlite
    from sqlalchemy.schema import CreateColumn

    columna = sa.Column(
        "recorrido_inicial_oculto", sa.Boolean(), nullable=True,
        server_default=sa.false(),
    )
    sa.Table("configuracion", sa.MetaData(), columna)

    ddl_pg = str(CreateColumn(columna).compile(dialect=postgresql.dialect()))
    ddl_sqlite = str(CreateColumn(columna).compile(dialect=sqlite.dialect()))

    assert "DEFAULT false" in ddl_pg, ddl_pg
    assert not BOOLEAN_CON_ENTERO.search(ddl_pg), ddl_pg
    # El mismo modelo sigue siendo válido para la instalación de escritorio.
    assert "DEFAULT 0" in ddl_sqlite, ddl_sqlite


def test_precios_anomalos_libera_la_transaccion_si_no_puede_leer_configuracion():
    """El `except` que oculta el error debe hacer rollback.

    Es el eslabón que convertía un fallo ya silenciado en un 500: sin
    ``rollback`` la sesión queda abortada y la siguiente consulta del panel
    (contar clientes, en ``onboarding.py:151``) revienta con
    ``InFailedSqlTransaction`` señalando al lugar equivocado.
    """
    from sqlalchemy.exc import ProgrammingError

    from app.services import precios_anomalos

    class SesionFalsa:
        """Sesión cuyo ``SELECT configuracion.*`` falla, como en producción."""

        def __init__(self):
            self.rollbacks = 0

        def query(self, *_a, **_k):
            raise ProgrammingError(
                "SELECT configuracion.*", {},
                Exception('column "recorrido_inicial_oculto" does not exist'),
            )

        def rollback(self):
            self.rollbacks += 1

    db = SesionFalsa()
    assert precios_anomalos._tasas_candidatas(db), "debe degradar a tasas de referencia"
    assert db.rollbacks >= 1, (
        "_tasas_candidatas se tragó el error sin liberar la transacción: "
        "la siguiente consulta del handler fallaría con InFailedSqlTransaction."
    )

    db = SesionFalsa()
    assert precios_anomalos._indice_precios_oficiales.__doc__  # sanity
    with pytest.raises(ProgrammingError):
        # Sin configuración legible el índice sigue adelante y falla al leer
        # partidas con la MISMA sesión falsa; lo que importa es que antes se
        # haya soltado la transacción.
        precios_anomalos._indice_precios_oficiales(db)
    assert db.rollbacks >= 1, (
        "_indice_precios_oficiales debe hacer rollback antes de continuar."
    )


def test_ids_partidas_anomalas_no_deja_la_sesion_envenenada(monkeypatch):
    """La red de seguridad que devuelve ``[]`` también debe soltar la sesión."""
    from app.services import precios_anomalos

    class SesionFalsa:
        def __init__(self):
            self.rollbacks = 0

        def rollback(self):
            self.rollbacks += 1

    def _explota(*_a, **_k):
        raise RuntimeError("fallo simulado en la detección")

    monkeypatch.setattr(precios_anomalos, "detectar_precios_anomalos", _explota)

    db = SesionFalsa()
    assert precios_anomalos.ids_partidas_anomalas(db) == []
    assert db.rollbacks == 1, (
        "ids_partidas_anomalas devolvió [] sin liberar la transacción abortada."
    )
