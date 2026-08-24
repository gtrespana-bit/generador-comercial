"""Permisos/RLS de planos_elementos tras el editor desde cero.

La tabla ``planos_elementos`` se añadió junto al editor vectorial de planos
para guardar muros, huecos (puertas/ventanas) y líneas auxiliares que la
persona dibuja en el lienzo. El GRANT al rol de aplicación y sus políticas
RLS limitadas por tenant viven aquí, igual que ``c0d1e2f3a4b5`` hizo
para ``planos_obra`` y ``planos_mediciones``.

Sin esta migración, las pruebas ``test_rls`` fallan al auditar que cada
tabla del modelo recibe permisos del rol de aplicación; en producción se
manifestaría como ``permission denied for table planos_elementos`` al
guardar el primer muro dibujado por el usuario.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"
TABLA = "planos_elementos"

TENANT_READ = "cotizat_security.tenant_access(organizacion_id, FALSE)"
TENANT_WRITE = "cotizat_security.tenant_access(organizacion_id, TRUE)"

POLITICAS = (
    (TABLA, "cotizat_planos_elementos_select", "SELECT", f"USING ({TENANT_READ})"),
    (TABLA, "cotizat_planos_elementos_insert", "INSERT", f"WITH CHECK ({TENANT_WRITE})"),
    (
        TABLA,
        "cotizat_planos_elementos_update",
        "UPDATE",
        f"USING ({TENANT_WRITE}) WITH CHECK ({TENANT_WRITE})",
    ),
    (TABLA, "cotizat_planos_elementos_delete", "DELETE", f"USING ({TENANT_WRITE})"),
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

    op.execute(f"REVOKE ALL ON TABLE public.{TABLA} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{TABLA} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLA} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.{TABLA} TO {APP_ROLE}"
    )
    op.execute(_conceder_secuencia(TABLA))

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
    op.execute(f"ALTER TABLE public.{TABLA} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLA} DISABLE ROW LEVEL SECURITY")
    op.execute(f"REVOKE ALL ON TABLE public.{TABLA} FROM {APP_ROLE}")
