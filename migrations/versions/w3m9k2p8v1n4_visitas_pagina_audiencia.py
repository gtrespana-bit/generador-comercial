"""Audiencia de la capa pública: ``public.visitas_pagina`` (E5-012 ampliada).

Tabla de agregado para el panel de administración: cuántos visitantes recibe
el sitio cada día, qué páginas los traen y de qué origen. Se usa en
``/admin/analitica`` para que el operador mire el embudo completo (visitas ->
registros -> empresas -> presupuestos -> cobros) con un dato propio y sin
cookies de terceros.

Diseño:

- La IP nunca se guarda, solo su hash con sal del despliegue
  (``app.security.hash_ip``), igual que el registro de pruebas gratuitas.
- Es de lectura/escritura global: no hereda ``TenantMixin`` ni queda bajo RLS
  de inquilino; la analítica del operador la lee desde su propia sesión.
- Idempotente por si el código arranca antes que la migración en un despliegue.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "w3m9k2p8v1n4"
down_revision: Union[str, Sequence[str], None] = "v2d7f1a6b9c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "visitas_pagina"


def _existe() -> bool:
    try:
        from sqlalchemy import inspect as _inspect

        return TABLE in _inspect(op.get_bind()).get_table_names()
    except Exception:
        return False


def upgrade() -> None:
    if _existe():
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ruta", sa.String(length=300), nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=False),
        sa.Column("usuario_agent", sa.String(length=300), nullable=True),
        sa.Column("referente", sa.String(length=300), nullable=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(f"ix_{TABLE}_ruta", TABLE, ["ruta"])
    op.create_index(f"ix_{TABLE}_ip_hash", TABLE, ["ip_hash"])
    op.create_index(f"ix_{TABLE}_created_at", TABLE, ["created_at"])


def downgrade() -> None:
    if not _existe():
        return
    op.drop_index(f"ix_{TABLE}_created_at", table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_ip_hash", table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_ruta", table_name=TABLE)
    op.drop_table(TABLE)
