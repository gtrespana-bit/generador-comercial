"""Fiscalidad británica en el presupuesto: CIS e inversión del sujeto pasivo.

Dos columnas en ``presupuestos``, las dos con valor por defecto que no cambia
nada de lo que ya existe:

* ``iva_tratamiento`` (``''``) — cómo se trata el IVA del documento. Vacío es
  la regla normal de cada mercado; ``inversion_sujeto_pasivo`` activa la
  inversión del sujeto pasivo británica (VATA 1994 s. 55A), en la que el
  documento va sin IVA y lo declara el cliente.

* ``cis_tipo`` (``NULL``) — tipo de retención del Construction Industry Scheme:
  0 %, 20 % o 30 %. NULL significa «este documento no está bajo el CIS», que es
  lo correcto para un cliente particular o para un servicio fuera del ámbito
  del CIS. Se elige NULL como neutro en lugar de 0 porque «sin CIS» y «CIS al
  0 % con Gross Payment Status» son situaciones distintas y no deben confundirse.

No se reutiliza ``retencion_pct``: es un porcentaje comercial genérico que solo
se rotula en el PDF, mientras que el CIS es una retención legal que se descuenta
del importe a cobrar y se declara a Hacienda en el CIS300.

En ``facturas`` se añaden las mismas dos columnas más una tercera,
``coste_materiales``. La factura es el documento que se declara en el CIS300,
así que la retención tiene que constar en ella; el coste de materiales viaja
como **instantánea** porque ``FacturaItem`` no guarda costes y la factura no
puede recalcularse contra un presupuesto que puede seguir cambiando.

El código que consume estas columnas está en
``app/services/fiscalidad_reino_unido.py``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "k6c9f2d5b8a3"
down_revision: Union[str, Sequence[str], None] = "j5b8e1c4a9f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columnas_existentes(bind, tabla: str) -> set[str]:
    try:
        from sqlalchemy import inspect as _inspect

        return {c["name"] for c in _inspect(bind).get_columns(tabla)}
    except Exception:
        return set()


def upgrade() -> None:
    # Idempotente por la misma razón que h1c4b7e9a3d2: si un hotfix creó la
    # columna con ``ALTER TABLE ... IF NOT EXISTS``, el upgrade no debe abortar.
    bind = op.get_bind()
    existentes = _columnas_existentes(bind, "presupuestos")

    if "iva_tratamiento" not in existentes:
        op.add_column(
            "presupuestos",
            sa.Column(
                "iva_tratamiento",
                sa.String(30),
                nullable=True,
                # Cadena vacía y no NULL: así los documentos anteriores a esta
                # migración se comportan igual que antes sin CASE WHEN extra.
                server_default=sa.text("''"),
            ),
        )
    if "cis_tipo" not in existentes:
        op.add_column(
            "presupuestos",
            sa.Column("cis_tipo", sa.Float(), nullable=True),
        )

    # El documento de cobro: el que se declara en el CIS300.
    facturas = _columnas_existentes(bind, "facturas")
    if "iva_tratamiento" not in facturas:
        op.add_column(
            "facturas",
            sa.Column(
                "iva_tratamiento",
                sa.String(30),
                nullable=True,
                server_default=sa.text("''"),
            ),
        )
    if "cis_tipo" not in facturas:
        op.add_column("facturas", sa.Column("cis_tipo", sa.Float(), nullable=True))
    if "coste_materiales" not in facturas:
        op.add_column(
            "facturas",
            sa.Column(
                "coste_materiales",
                sa.Float(),
                nullable=True,
                server_default=sa.text("0"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existentes = _columnas_existentes(bind, "presupuestos")
    if "cis_tipo" in existentes:
        op.drop_column("presupuestos", "cis_tipo")
    if "iva_tratamiento" in existentes:
        op.drop_column("presupuestos", "iva_tratamiento")

    facturas = _columnas_existentes(bind, "facturas")
    if "coste_materiales" in facturas:
        op.drop_column("facturas", "coste_materiales")
    if "cis_tipo" in facturas:
        op.drop_column("facturas", "cis_tipo")
    if "iva_tratamiento" in facturas:
        op.drop_column("facturas", "iva_tratamiento")
