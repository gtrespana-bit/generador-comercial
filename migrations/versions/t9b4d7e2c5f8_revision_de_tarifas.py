"""«Revisa tus precios antes de cotizar»: fecha de revisión por tarifa.

El generador no inventa precios: los compone con el catálogo que tenga la
empresa. Si la tarifa de un oficial llega a 15 US$/h y la de otra empresa a
25 US$/h, el mismo presupuesto sale con importes distintos, y eso es correcto
—siempre que cada empresa haya confirmado que esa es *su* tarifa—. El problema
que arregla esta migración es el caso contrario: una cuenta recién creada
cotiza con referencias de mercado que pueden ser de otro país o de hace meses
y nada en el producto le dice que las revise.

Dos columnas, ninguna reescribe datos:

- ``configuracion.onboarding_precios_revisados``: la empresa ya pasó por la
  revisión de tarifas. Es lo que permite pedirlo **una vez** y no en cada
  inicio de sesión.
- ``recursos.precio_revisado_at``: «miré esta tarifa y es la mía», con fecha.
  Es distinto de «tiene precio»: el catálogo llega con precios, pero no con
  la certeza de que sean los de esta empresa. Pasado un tiempo (seis meses) se
  vuelve a pedir, porque una tarifa de mano de obra de hace un año no es un
  dato: es una suposición.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "t9b4d7e2c5f8"
down_revision: Union[str, Sequence[str], None] = "s8a3c6d1f7b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


#: (tabla, columna, tipo, valor por omisión)
COLUMNAS = (
    ("configuracion", "onboarding_precios_revisados", sa.Boolean(), sa.false()),
    ("recursos", "precio_revisado_at", sa.DateTime(), None),
)


def _existe(tabla: str, columna: str) -> bool:
    try:
        from sqlalchemy import inspect as _inspect

        return columna in {c["name"] for c in _inspect(op.get_bind()).get_columns(tabla)}
    except Exception:
        return False


def upgrade() -> None:
    # Idempotente por el mismo motivo que b1c2d3e4f5a6: un hotfix puede haber
    # creado las columnas a mano en producción antes de que corra Alembic, y
    # un «already exists» dejaría la base a medio migrar.
    for tabla, columna, tipo, defecto in COLUMNAS:
        if _existe(tabla, columna):
            continue
        op.add_column(
            tabla,
            sa.Column(
                columna,
                tipo,
                nullable=True,
                # ``sa.false()`` compila a ``false`` en PostgreSQL y a ``0`` en
                # SQLite; ``text("0")`` rompe PostgreSQL con DatatypeMismatch.
                server_default=defecto,
            ),
        )


def downgrade() -> None:
    for tabla, columna, _tipo, _defecto in COLUMNAS:
        if not _existe(tabla, columna):
            continue
        with op.batch_alter_table(tabla) as lote:
            lote.drop_column(columna)
