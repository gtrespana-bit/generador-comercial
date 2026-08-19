"""Add national reference and organization override prices for resources."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "precios_recursos_mercado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recurso_id", sa.Integer(), sa.ForeignKey("recursos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pais_codigo", sa.String(length=2), nullable=False),
        sa.Column("organizacion_id", sa.Integer(), sa.ForeignKey("organizaciones.id", ondelete="CASCADE"), nullable=True),
        sa.Column("precio", sa.Float(), nullable=False, server_default="0"),
        sa.Column("moneda", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("fuente", sa.String(length=200), nullable=True, server_default=""),
        sa.Column("proveedor", sa.String(length=150), nullable=True, server_default=""),
        sa.Column("confianza", sa.String(length=20), nullable=True, server_default="referencia"),
        sa.Column("fecha_vigencia", sa.Date(), nullable=True),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("recurso_id", "pais_codigo", "organizacion_id", name="uq_precio_recurso_mercado_org"),
    )
    op.create_index("ix_precios_recursos_mercado_recurso_id", "precios_recursos_mercado", ["recurso_id"])
    op.create_index("ix_precios_recursos_mercado_pais_codigo", "precios_recursos_mercado", ["pais_codigo"])
    op.create_index("ix_precios_recursos_mercado_organizacion_id", "precios_recursos_mercado", ["organizacion_id"])


def downgrade() -> None:
    op.drop_index("ix_precios_recursos_mercado_organizacion_id", table_name="precios_recursos_mercado")
    op.drop_index("ix_precios_recursos_mercado_pais_codigo", table_name="precios_recursos_mercado")
    op.drop_index("ix_precios_recursos_mercado_recurso_id", table_name="precios_recursos_mercado")
    op.drop_table("precios_recursos_mercado")
