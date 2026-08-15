"""invitation recipient keeps visibility after accepting

Revision ID: d7f2a9c41e63
Revises: c93e7a4d20f1
Create Date: 2026-08-15 01:30:00

PostgreSQL aplica el ``USING`` de las políticas SELECT como ``WITH CHECK``
sobre la **fila nueva** de un UPDATE: la fila actualizada debe seguir siendo
visible para quien la modifica. ``cotizat_invitation_select_recipient``
exigía ``accepted_at IS NULL``, exactamente lo que el UPDATE de aceptación
deja de cumplir, así que la reclamación del token moría con
``InsufficientPrivilege: new row violates row-level security policy for
table "invitaciones_organizacion"`` (500 en producción al pulsar «Aceptar
invitación»).

La corrección no amplía privilegios de forma material: el destinatario sigue
viendo únicamente invitaciones dirigidas a su email verificado, no revocadas
y vigentes; una vez aceptadas, solo si fue él mismo quien las aceptó. El
UPDATE de consumo conserva su ``USING`` con ``accepted_at IS NULL``, de modo
que el token de un solo uso sigue sin poder reclamarse dos veces.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d7f2a9c41e63"
down_revision: Union[str, Sequence[str], None] = "c93e7a4d20f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INVITATION_TABLE = "invitaciones_organizacion"
POLICY = "cotizat_invitation_select_recipient"

#: Visibilidad corregida: pendiente O aceptada por el propio destinatario.
RECIPIENT_VISIBLE = """
  email = cotizat_security.current_user_email()
  AND cotizat_security.current_user_is_verified()
  AND revoked_at IS NULL
  AND expires_at > pg_catalog.clock_timestamp()
  AND (
    accepted_at IS NULL
    OR aceptada_por_usuario_id = cotizat_security.current_user_id()
  )
"""

#: Visibilidad original: solo invitaciones pendientes.
RECIPIENT_VISIBLE_ORIGINAL = """
  email = cotizat_security.current_user_email()
  AND cotizat_security.current_user_is_verified()
  AND accepted_at IS NULL
  AND revoked_at IS NULL
  AND expires_at > pg_catalog.clock_timestamp()
"""


def _recreate_policy(visibility: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {POLICY} ON public.{INVITATION_TABLE}")
    op.execute(f"""
        CREATE POLICY {POLICY}
        ON public.{INVITATION_TABLE}
        FOR SELECT TO cotizat_app
        USING ({visibility})
    """)


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    _recreate_policy(RECIPIENT_VISIBLE)


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    _recreate_policy(RECIPIENT_VISIBLE_ORIGINAL)
