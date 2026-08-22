"""Permite ocultar la «Guía de inicio» del panel por organización.

Añade `configuracion.recorrido_inicial_oculto` (BOOLEAN, 0 por defecto).
Cuando está activo, el dashboard deja de mostrar la tarjeta del recorrido
inicial sin darlo por completado: es la preferencia de quien ya conoce la
aplicación o crea otra organización y no necesita que le recuerden los cinco
pasos. Cada espacio de trabajo conserva su propia marca.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "c3e9a1b7d4f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotente: el hotfix de producción puede haber creado ya la columna
    # vía ``ALTER TABLE ... IF NOT EXISTS`` antes de que ``alembic upgrade``
    # se ejecute. Sin el chequeo, el upgrade fallaría con "already exists"
    # y dejaría la base a medio migrar.
    bind = op.get_bind()
    try:
        from sqlalchemy import inspect as _inspect

        cols = {c["name"] for c in _inspect(bind).get_columns("configuracion")}
    except Exception:
        cols = set()
    if "recorrido_inicial_oculto" not in cols:
        op.add_column(
            "configuracion",
            sa.Column(
                "recorrido_inicial_oculto",
                sa.Boolean(),
                nullable=True,
                # ``sa.false()`` y NO ``sa.text("0")``: PostgreSQL es estricto
                # con los tipos y rechaza ``BOOLEAN DEFAULT 0`` con
                # ``DatatypeMismatch: column ... is of type boolean but default
                # expression is of type integer``. Con el literal entero esta
                # migración abortaba, ``alembic upgrade head`` nunca terminaba y
                # la base se quedaba en el head anterior sin la columna: de ahí
                # el ``UndefinedColumn`` que acababa en 500 en /inicio.
                # ``sa.false()`` compila a ``false`` en PostgreSQL y a ``0`` en
                # SQLite, así que sirve para los dos backends.
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    op.drop_column("configuracion", "recorrido_inicial_oculto")
