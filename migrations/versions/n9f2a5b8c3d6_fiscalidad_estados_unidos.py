"""Fiscalidad estadounidense: estado de la obra y modo de base del «sales tax».

Añade a ``presupuestos`` y ``facturas`` tres columnas:

* ``estado_codigo`` — el estado donde se hace la obra («TX», «NY»…). El
  impuesto sigue al lugar de la obra, no a la sede de la empresa, así que
  vive en el documento; la empresa solo guarda su estado habitual como
  valor propuesto.
* ``us_tax_base`` — sobre qué cae el tipo: ``none`` (no se cobra al
  cliente: el contratista es consumidor final de los materiales, el marco
  mayoritario), ``materials``, ``labor``, ``full`` o ``gross_receipts``.
  Vacío = documento sin el motor, con el impuesto genérico de siempre.
* ``us_tax_fraccion`` — fracción de la base que se grava en modo
  «ingresos brutos» (Arizona grava el 65 % del contrato). 1.0 = íntegra.

Y dos instantáneas propias:

* ``facturas.us_base_gravada`` — la base sobre la que se aplicó el tipo al
  emitir. El reparto materiales/mano de obra se estima con los costes del
  presupuesto y ``FacturaItem`` no guarda costes: sin la instantánea, la
  factura recalcularía un impuesto distinto del presupuesto aprobado.
* ``configuracion.empresa_estado_eeuu`` — el estado habitual de la empresa,
  que el editor propone en cada presupuesto nuevo.

No se reutiliza ningún campo existente: ``impuesto_pct`` sigue siendo el
tipo (lo único que el resto de mercados necesita), y meter la base dentro
del porcentaje —«7 % sobre materiales» convertido a un % menor sobre el
total— rompería en cuanto cambiara una partida. Tampoco se toca
``retencion_pct``: esto no es una retención, es el impuesto del documento.

El código que consume estas columnas está en
``app/services/fiscalidad_eeuu.py`` y los defaults investigados en
``docs/INVESTIGACION_FISCALIDAD_ESTADOS_UNIDOS.md``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "n9f2a5b8c3d6"
down_revision: Union[str, Sequence[str], None] = "m8e1f4a7b2c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columnas_existentes(bind, tabla: str) -> set[str]:
    try:
        from sqlalchemy import inspect as _inspect

        return {c["name"] for c in _inspect(bind).get_columns(tabla)}
    except Exception:
        return set()


def upgrade() -> None:
    # Idempotente por la misma razón que k6c9f2d5b8a3/m8e1f4a7b2c5: si un
    # hotfix creó la columna con ``ALTER TABLE ... IF NOT EXISTS``, el
    # upgrade no debe abortar.
    bind = op.get_bind()

    cols = _columnas_existentes(bind, "presupuestos")
    if "estado_codigo" not in cols:
        op.add_column("presupuestos", sa.Column("estado_codigo", sa.String(2), nullable=False, server_default=""))
    if "us_tax_base" not in cols:
        op.add_column("presupuestos", sa.Column("us_tax_base", sa.String(20), nullable=False, server_default=""))
    if "us_tax_fraccion" not in cols:
        op.add_column("presupuestos", sa.Column("us_tax_fraccion", sa.Float(), nullable=False, server_default="1"))

    # El documento de cobro hereda estado, modo y fracción al convertirse el
    # presupuesto, y congela la base gravada: es contra la factura contra
    # lo que el cliente paga y el contratista declara.
    cols = _columnas_existentes(bind, "facturas")
    if "estado_codigo" not in cols:
        op.add_column("facturas", sa.Column("estado_codigo", sa.String(2), nullable=False, server_default=""))
    if "us_tax_base" not in cols:
        op.add_column("facturas", sa.Column("us_tax_base", sa.String(20), nullable=False, server_default=""))
    if "us_tax_fraccion" not in cols:
        op.add_column("facturas", sa.Column("us_tax_fraccion", sa.Float(), nullable=False, server_default="1"))
    if "us_base_gravada" not in cols:
        op.add_column("facturas", sa.Column("us_base_gravada", sa.Float(), nullable=True))

    if "empresa_estado_eeuu" not in _columnas_existentes(bind, "configuracion"):
        op.add_column("configuracion", sa.Column("empresa_estado_eeuu", sa.String(2), nullable=False, server_default=""))


def downgrade() -> None:
    bind = op.get_bind()
    for tabla, columnas in (
        ("presupuestos", ("estado_codigo", "us_tax_base", "us_tax_fraccion")),
        ("facturas", ("estado_codigo", "us_tax_base", "us_tax_fraccion", "us_base_gravada")),
        ("configuracion", ("empresa_estado_eeuu",)),
    ):
        existentes = _columnas_existentes(bind, tabla)
        for columna in columnas:
            if columna in existentes:
                op.drop_column(tabla, columna)
