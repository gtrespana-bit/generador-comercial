"""Esquema del editor vectorial de planos (f1b2c3d4e5a6).

El modelo ``PlanoObra`` pasó a tener cuatro columnas más después de
``e4b8c2d6a190``:

* ``origen``: procedencia del plano (subido / dibujado / mixto).
* ``grosor_tabique_cm``: grosor típico del tabique para medir y renderizar.
* ``ancho_lienzo_m`` y ``alto_lienzo_m``: dimensiones del lienzo vectorial.

Además el editor desde cero guarda geometría en ``planos_elementos``
(muros, huecos y líneas auxiliares), tabla que no existía en ninguna
migración anterior. Sin ella, el backend de ``/planos/{id}/elementos``
devuelve ``undefined table planos_elementos`` al guardar el primer muro.

La migración es idempotente en PostgreSQL (``ADD COLUMN IF NOT EXISTS`` y
``CREATE TABLE IF NOT EXISTS``) para que también pueda aplicarse encima de
bases que el arranque ya auto-reparó.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "f1b2c3d4e5a6"
down_revision: Union[str, Sequence[str], None] = "e4b8c2d6a190"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # SQLite crea el esquema por metadatos (Base.metadata.create_all) y el
    # arranque local lo completa con models.migrar(); aquí no hace falta.
    if not _postgres():
        return

    # Columnas nuevas de planos_obra. Idempotente: si una base ya fue
    # auto-reparada en el arranque, el ALTER no hace nada y no falla.
    op.execute(
        "ALTER TABLE public.planos_obra ADD COLUMN IF NOT EXISTS "
        "origen VARCHAR(20) NOT NULL DEFAULT 'subido'"
    )
    op.execute(
        "ALTER TABLE public.planos_obra ADD COLUMN IF NOT EXISTS "
        "grosor_tabique_cm DOUBLE PRECISION NOT NULL DEFAULT 10"
    )
    op.execute(
        "ALTER TABLE public.planos_obra ADD COLUMN IF NOT EXISTS "
        "ancho_lienzo_m DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE public.planos_obra ADD COLUMN IF NOT EXISTS "
        "alto_lienzo_m DOUBLE PRECISION"
    )
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_plano_origen_valido') THEN
            ALTER TABLE public.planos_obra ADD CONSTRAINT ck_plano_origen_valido
              CHECK (origen IN ('subido', 'dibujado', 'mixto'));
          END IF;
        END $$
        """
    )

    # Tabla del editor vectorial.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.planos_elementos (
            id SERIAL PRIMARY KEY,
            plano_id INTEGER NOT NULL REFERENCES public.planos_obra(id) ON DELETE CASCADE,
            organizacion_id INTEGER NOT NULL REFERENCES public.organizaciones(id) ON DELETE RESTRICT,
            tipo VARCHAR(20) NOT NULL DEFAULT 'muro',
            puntos_json TEXT NOT NULL DEFAULT '[]',
            grosor_cm DOUBLE PRECISION DEFAULT 10,
            color VARCHAR(20) DEFAULT '#1f2937',
            muro_id INTEGER REFERENCES public.planos_elementos(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_planos_elementos_plano ON public.planos_elementos (plano_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_planos_elementos_org_plano ON public.planos_elementos (organizacion_id, plano_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_planos_elementos_muro ON public.planos_elementos (muro_id)")
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_plano_elemento_tipo_valido') THEN
            ALTER TABLE public.planos_elementos ADD CONSTRAINT ck_plano_elemento_tipo_valido
              CHECK (tipo IN ('muro', 'hueco', 'linea_auxiliar'));
          END IF;
        END $$
        """
    )

    # Permisos y RLS con el mismo patrón que el resto de tablas planos.
    op.execute("REVOKE ALL ON TABLE public.planos_elementos FROM PUBLIC")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.planos_elementos TO {APP_ROLE}")
    op.execute(
        f"""
        DO $$ DECLARE secuencia text; BEGIN
          secuencia := pg_get_serial_sequence('public.planos_elementos', 'id');
          IF secuencia IS NOT NULL THEN
            EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO {APP_ROLE}', secuencia);
          END IF;
        END $$
        """
    )
    op.execute("ALTER TABLE public.planos_elementos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.planos_elementos FORCE ROW LEVEL SECURITY")

    politicas = (
        ("cotizat_planos_elementos_select", "SELECT", "USING (cotizat_security.tenant_access(organizacion_id, FALSE))"),
        ("cotizat_planos_elementos_insert", "INSERT", "WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE))"),
        (
            "cotizat_planos_elementos_update",
            "UPDATE",
            "USING (cotizat_security.tenant_access(organizacion_id, TRUE)) "
            "WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE))",
        ),
        ("cotizat_planos_elementos_delete", "DELETE", "USING (cotizat_security.tenant_access(organizacion_id, TRUE))"),
    )
    for nombre, accion, clausula in politicas:
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.planos_elementos")
        op.execute(
            f"CREATE POLICY {nombre} ON public.planos_elementos "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )


def downgrade() -> None:
    if not _postgres():
        return

    politicas = (
        "cotizat_planos_elementos_select",
        "cotizat_planos_elementos_insert",
        "cotizat_planos_elementos_update",
        "cotizat_planos_elementos_delete",
    )
    for nombre in politicas:
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.planos_elementos")

    op.execute("ALTER TABLE public.planos_elementos NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.planos_elementos DISABLE ROW LEVEL SECURITY")
    op.execute(f"REVOKE ALL ON TABLE public.planos_elementos FROM {APP_ROLE}")
    op.execute("DROP TABLE IF EXISTS public.planos_elementos")

    op.execute("ALTER TABLE public.planos_obra DROP COLUMN IF EXISTS alto_lienzo_m")
    op.execute("ALTER TABLE public.planos_obra DROP COLUMN IF EXISTS ancho_lienzo_m")
    op.execute("ALTER TABLE public.planos_obra DROP COLUMN IF EXISTS grosor_tabique_cm")
    op.execute("ALTER TABLE public.planos_obra DROP COLUMN IF EXISTS origen")
