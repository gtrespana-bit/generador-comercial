"""Fiscalidad irlandesa de la construcción: tipo de RCT en el documento.

Añade ``rct_tipo`` a ``presupuestos`` y ``facturas``: 0 %, 20 % o 35 %, el
tipo que Revenue asigna al subcontratista según su historial y confirma en
la autorización de deducción de cada pago. ``NULL`` significa «este
documento no está bajo RCT» (cliente particular u operación no relevante),
que no es lo mismo que retener al 0 %: con el 0 % sí hay contrato notificado
y autorización, solo que la retención sale a cero.

Es una columna nueva y no se reutiliza ``cis_tipo`` por la razón de fondo:
el CIS británico retiene sobre el elemento de mano de obra (los materiales
se descuentan de la base) y el RCT irlandés sobre **el importe íntegro sin
IVA, materiales incluidos**. Compartir columna invitaría a aplicar la base
equivocada en uno de los dos países, y un documento irlandés no puede heredar
un tipo británico al copiarse entre mercados.

La inversión del sujeto pasivo irlandesa (VATCA 2010 s. 16(3)) **no** necesita
columna nueva: reutiliza ``iva_tratamiento`` de la migración
``k6c9f2d5b8a3``, porque la pregunta que guarda —«¿el cliente declara el IVA
en vez de cobrarse en factura?»— es la misma en los dos mercados; lo que
cambia es la leyenda que se imprime, y eso lo resuelve el código según el
país. Tampoco hace falta en ``facturas`` ninguna instantánea adicional: la
base del RCT no depende del coste de materiales (la instantánea existente
solo alimenta, en su caso, el aviso de la regla de los dos tercios).

El código que consume esta columna está en
``app/services/fiscalidad_irlanda.py``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "m8e1f4a7b2c5"
down_revision: Union[str, Sequence[str], None] = "l7d0e3f6a9c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columnas_existentes(bind, tabla: str) -> set[str]:
    try:
        from sqlalchemy import inspect as _inspect

        return {c["name"] for c in _inspect(bind).get_columns(tabla)}
    except Exception:
        return set()


def upgrade() -> None:
    # Idempotente por la misma razón que k6c9f2d5b8a3: si un hotfix creó la
    # columna con ``ALTER TABLE ... IF NOT EXISTS``, el upgrade no debe abortar.
    bind = op.get_bind()

    if "rct_tipo" not in _columnas_existentes(bind, "presupuestos"):
        op.add_column(
            "presupuestos",
            sa.Column("rct_tipo", sa.Float(), nullable=True),
        )

    # El documento de cobro hereda la retención al convertirse el presupuesto:
    # es contra el que Revenue autoriza la deducción en ROS.
    if "rct_tipo" not in _columnas_existentes(bind, "facturas"):
        op.add_column("facturas", sa.Column("rct_tipo", sa.Float(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if "rct_tipo" in _columnas_existentes(bind, "presupuestos"):
        op.drop_column("presupuestos", "rct_tipo")
    if "rct_tipo" in _columnas_existentes(bind, "facturas"):
        op.drop_column("facturas", "rct_tipo")
