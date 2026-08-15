"""make the Alembic version readable by the application role

Revision ID: e1a4b7c9d2f0
Revises: d7f2a9c41e63
Create Date: 2026-08-15 00:00:00

The application connects with ``cotizat_runtime``, a non-superuser member of
``cotizat_app``.  Some Supabase projects have row-level security enabled on
``public.alembic_version``.  Without an explicit exception, the runtime role
can then connect successfully but sees no migration row, so ``/readyz`` and
the startup guard report ``sin-version`` even though the schema is current.

The version table contains migration metadata, not tenant data.  It must not
be protected by tenant RLS; the application only needs to read its current
revision.  DDL and the grant are intentionally kept in this PostgreSQL-only
revision instead of being applied during application startup.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e1a4b7c9d2f0"
down_revision: Union[str, Sequence[str], None] = "d7f2a9c41e63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VERSION_TABLE = "public.alembic_version"
APP_ROLE = "cotizat_app"


def upgrade() -> None:
    """Expose only the migration version metadata to the runtime role."""
    if op.get_bind().dialect.name != "postgresql":
        return

    # Both statements are idempotent.  The migration must run with the
    # administrative URL because disabling RLS is a table-owner operation.
    op.execute(f"ALTER TABLE {VERSION_TABLE} DISABLE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT ON TABLE {VERSION_TABLE} TO {APP_ROLE}")


def downgrade() -> None:
    """Reverse the explicit visibility change made by this revision."""
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(f"REVOKE SELECT ON TABLE {VERSION_TABLE} FROM {APP_ROLE}")
    op.execute(f"ALTER TABLE {VERSION_TABLE} ENABLE ROW LEVEL SECURITY")
