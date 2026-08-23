"""Planos con medición manual asistida (b2c3d4e5f6a7).

Crea tablas planos_obra y planos_mediciones con RLS por organización.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "f9d4c2a7e5b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # SQLite se crea via Base.metadata.create_all, no necesita migración
    if not _postgres():
        op.create_table(
            "planos_obra",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organizacion_id", sa.Integer(), sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"), nullable=False, index=True),
            sa.Column("presupuesto_id", sa.Integer(), sa.ForeignKey("presupuestos.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("nombre", sa.String(250), nullable=False, server_default="Plano"),
            sa.Column("archivo", sa.String(500), nullable=False, server_default=""),
            sa.Column("content_type", sa.String(150), nullable=False, server_default="image/png"),
            sa.Column("ancho_px", sa.Integer(), nullable=True),
            sa.Column("alto_px", sa.Integer(), nullable=True),
            sa.Column("escala_px_por_metro", sa.Float(), nullable=True),
            sa.Column("calibracion_px", sa.Float(), nullable=True),
            sa.Column("calibracion_real", sa.Float(), nullable=True),
            sa.Column("unidad_calibracion", sa.String(20), server_default="m"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_table(
            "planos_mediciones",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organizacion_id", sa.Integer(), sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"), nullable=False, index=True),
            sa.Column("plano_id", sa.Integer(), sa.ForeignKey("planos_obra.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("presupuesto_id", sa.Integer(), sa.ForeignKey("presupuestos.id", ondelete="CASCADE"), nullable=True, index=True),
            sa.Column("tipo", sa.String(20), nullable=False, server_default="lineal"),
            sa.Column("etiqueta", sa.String(250), server_default=""),
            sa.Column("valor", sa.Float(), server_default="0"),
            sa.Column("unidad", sa.String(20), server_default="m"),
            sa.Column("puntos_json", sa.Text(), server_default="[]"),
            sa.Column("partida_destino_id", sa.Integer(), sa.ForeignKey("presupuesto_items.id", ondelete="SET NULL"), nullable=True),
            sa.Column("color", sa.String(20), server_default="#ff0000"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        return

    op.create_table(
        "planos_obra",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organizacion_id", sa.Integer(), sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("presupuesto_id", sa.Integer(), sa.ForeignKey("presupuestos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nombre", sa.String(250), nullable=False, server_default="Plano"),
        sa.Column("archivo", sa.String(500), nullable=False, server_default=""),
        sa.Column("content_type", sa.String(150), nullable=False, server_default="image/png"),
        sa.Column("ancho_px", sa.Integer(), nullable=True),
        sa.Column("alto_px", sa.Integer(), nullable=True),
        sa.Column("escala_px_por_metro", sa.Float(), nullable=True),
        sa.Column("calibracion_px", sa.Float(), nullable=True),
        sa.Column("calibracion_real", sa.Float(), nullable=True),
        sa.Column("unidad_calibracion", sa.String(20), server_default="m"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_planos_obra_presupuesto", "planos_obra", ["presupuesto_id"])
    op.create_index("ix_planos_obra_org_presupuesto", "planos_obra", ["organizacion_id", "presupuesto_id"])

    op.create_table(
        "planos_mediciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organizacion_id", sa.Integer(), sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plano_id", sa.Integer(), sa.ForeignKey("planos_obra.id", ondelete="CASCADE"), nullable=False),
        sa.Column("presupuesto_id", sa.Integer(), sa.ForeignKey("presupuestos.id", ondelete="CASCADE"), nullable=True),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="lineal"),
        sa.Column("etiqueta", sa.String(250), server_default=""),
        sa.Column("valor", sa.Float(), server_default="0"),
        sa.Column("unidad", sa.String(20), server_default="m"),
        sa.Column("puntos_json", sa.Text(), server_default="[]"),
        sa.Column("partida_destino_id", sa.Integer(), sa.ForeignKey("presupuesto_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("color", sa.String(20), server_default="#ff0000"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("tipo IN ('lineal', 'area', 'perimetro', 'conteo', 'volumen')", name="ck_plano_medicion_tipo_valido"),
    )
    op.create_index("ix_planos_mediciones_plano", "planos_mediciones", ["plano_id"])
    op.create_index("ix_planos_mediciones_org_plano", "planos_mediciones", ["organizacion_id", "plano_id"])

    op.execute("ALTER TABLE planos_obra ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE planos_obra FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY cotizat_planos_obra_select ON planos_obra
        FOR SELECT USING (organizacion_id = cotizat_security.context_organization_id())
    """)
    op.execute("""
        CREATE POLICY cotizat_planos_obra_insert ON planos_obra
        FOR INSERT WITH CHECK (organizacion_id = cotizat_security.context_organization_id())
    """)
    op.execute("""
        CREATE POLICY cotizat_planos_obra_update ON planos_obra
        FOR UPDATE USING (organizacion_id = cotizat_security.context_organization_id())
        WITH CHECK (organizacion_id = cotizat_security.context_organization_id())
    """)
    op.execute("""
        CREATE POLICY cotizat_planos_obra_delete ON planos_obra
        FOR DELETE USING (organizacion_id = cotizat_security.context_organization_id())
    """)

    op.execute("ALTER TABLE planos_mediciones ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE planos_mediciones FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY cotizat_planos_mediciones_select ON planos_mediciones
        FOR SELECT USING (organizacion_id = cotizat_security.context_organization_id())
    """)
    op.execute("""
        CREATE POLICY cotizat_planos_mediciones_insert ON planos_mediciones
        FOR INSERT WITH CHECK (organizacion_id = cotizat_security.context_organization_id())
    """)
    op.execute("""
        CREATE POLICY cotizat_planos_mediciones_update ON planos_mediciones
        FOR UPDATE USING (organizacion_id = cotizat_security.context_organization_id())
        WITH CHECK (organizacion_id = cotizat_security.context_organization_id())
    """)
    op.execute("""
        CREATE POLICY cotizat_planos_mediciones_delete ON planos_mediciones
        FOR DELETE USING (organizacion_id = cotizat_security.context_organization_id())
    """)


def downgrade() -> None:
    if not _postgres():
        op.drop_table("planos_mediciones")
        op.drop_table("planos_obra")
        return

    op.execute("DROP POLICY IF EXISTS cotizat_planos_mediciones_delete ON planos_mediciones")
    op.execute("DROP POLICY IF EXISTS cotizat_planos_mediciones_update ON planos_mediciones")
    op.execute("DROP POLICY IF EXISTS cotizat_planos_mediciones_insert ON planos_mediciones")
    op.execute("DROP POLICY IF EXISTS cotizat_planos_mediciones_select ON planos_mediciones")
    op.execute("DROP POLICY IF EXISTS cotizat_planos_obra_delete ON planos_obra")
    op.execute("DROP POLICY IF EXISTS cotizat_planos_obra_update ON planos_obra")
    op.execute("DROP POLICY IF EXISTS cotizat_planos_obra_insert ON planos_obra")
    op.execute("DROP POLICY IF EXISTS cotizat_planos_obra_select ON planos_obra")
    op.drop_table("planos_mediciones")
    op.drop_table("planos_obra")
