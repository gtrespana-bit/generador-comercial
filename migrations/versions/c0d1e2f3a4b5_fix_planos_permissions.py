"""Repara permisos/RLS de planos tras auto-reparación de esquema.

La revisión ``b2c3d4e5f6a7`` creó ``planos_obra`` y ``planos_mediciones`` con
sus GRANT, pero algunas bases quedaron marcadas en ese head por la reparación
best-effort de arranque sin haber ejecutado realmente la parte de permisos. En
producción eso se manifiesta como ``permission denied for table planos_obra`` al
abrir el visor de planos.

Esta migración es deliberadamente idempotente: vuelve a conceder permisos al
rol de aplicación, resuelve las secuencias con ``pg_get_serial_sequence`` y
recrea las políticas limitadas a ``cotizat_app``.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c0d1e2f3a4b5"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"
TABLA_PLANOS = "planos_obra"
TABLA_MEDICIONES = "planos_mediciones"

TENANT_READ = "cotizat_security.tenant_access(organizacion_id, FALSE)"
TENANT_WRITE = "cotizat_security.tenant_access(organizacion_id, TRUE)"

POLITICAS = (
    (TABLA_PLANOS, "cotizat_planos_obra_select", "SELECT", f"USING ({TENANT_READ})"),
    (TABLA_PLANOS, "cotizat_planos_obra_insert", "INSERT", f"WITH CHECK ({TENANT_WRITE})"),
    (
        TABLA_PLANOS,
        "cotizat_planos_obra_update",
        "UPDATE",
        f"USING ({TENANT_WRITE}) WITH CHECK ({TENANT_WRITE})",
    ),
    (TABLA_PLANOS, "cotizat_planos_obra_delete", "DELETE", f"USING ({TENANT_WRITE})"),
    (
        TABLA_MEDICIONES,
        "cotizat_planos_mediciones_select",
        "SELECT",
        f"USING ({TENANT_READ})",
    ),
    (
        TABLA_MEDICIONES,
        "cotizat_planos_mediciones_insert",
        "INSERT",
        f"WITH CHECK ({TENANT_WRITE})",
    ),
    (
        TABLA_MEDICIONES,
        "cotizat_planos_mediciones_update",
        "UPDATE",
        f"USING ({TENANT_WRITE}) WITH CHECK ({TENANT_WRITE})",
    ),
    (
        TABLA_MEDICIONES,
        "cotizat_planos_mediciones_delete",
        "DELETE",
        f"USING ({TENANT_WRITE})",
    ),
)


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _conceder_secuencia(tabla: str) -> str:
    return (
        "DO $$ DECLARE secuencia text; BEGIN "
        f"secuencia := pg_get_serial_sequence('public.{tabla}', 'id'); "
        "IF secuencia IS NOT NULL THEN "
        "EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO "
        f"{APP_ROLE}', secuencia); "
        "END IF; END $$"
    )


def upgrade() -> None:
    if not _postgres():
        return

    for tabla in (TABLA_PLANOS, TABLA_MEDICIONES):
        op.execute(f"REVOKE ALL ON TABLE public.{tabla} FROM PUBLIC")
        op.execute(f"ALTER TABLE public.{tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE public.{tabla} FORCE ROW LEVEL SECURITY")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.{tabla} TO {APP_ROLE}")
        op.execute(_conceder_secuencia(tabla))

    for tabla, nombre, accion, clausula in POLITICAS:
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{tabla}")
        op.execute(
            f"CREATE POLICY {nombre} ON public.{tabla} "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )


def downgrade() -> None:
    if not _postgres():
        return

    for tabla, nombre, _accion, _clausula in POLITICAS:
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{tabla}")
    for tabla in (TABLA_PLANOS, TABLA_MEDICIONES):
        op.execute(f"ALTER TABLE public.{tabla} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE public.{tabla} DISABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE public.{tabla} FROM {APP_ROLE}")
