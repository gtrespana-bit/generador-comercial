"""Analítica operativa: visibilidad de operador, presencia e índices.

La pestaña «Analítica» del panel medía varias cosas a ciegas. Esta migración
corrige la raíz y prepara lo que necesita el panel en vivo:

1. **El operador no podía leer ``usuarios`` ni ``membresias``.** Las políticas
   de ``c93e7a4d20f1`` exigían membresía propia (``own_user``/``can_view_user``)
   y para una sesión de operador ``can_view_user`` siempre da falso, porque no
   hay organización de contexto. Consecuencia real en producción: el KPI
   «Cuentas» contaba 1 —el propio operador— y la serie de «registros por día»
   solo veía sus altas. Se añade la misma rama de operador que ya tiene
   ``cotizat_org_select`` desde ``b7c4a9e2d31f``: una sesión de cliente no gana
   nada con este cambio (``cotizat.es_operador`` solo vale ``on`` cuando el
   correo verificado está en ``COTIZAT_OPERADORES``).

2. **Agregados por organización en una sola consulta.** Llamar a
   ``admin_resumen_cliente(org)`` una vez por empresa es N+1. La nueva función
   ``admin_resumen_organizaciones()`` devuelve una fila por empresa con
   miembros, presupuestos, clientes, facturas y último acceso. Igual que las
   demás funciones de panel: ``SECURITY DEFINER`` y guarda de operador.

3. **Índices** para las consultas nuevas del panel: último acceso por usuario,
   eventos por acción y fecha, eventos por actor, y altas por fecha.

No se toca ningún dato: solo políticas, una función de lectura e índices.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "r7f2b1d4e8a6"
down_revision: Union[str, Sequence[str], None] = "q5e1c8a9d3f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"
IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""

#: ``own_user`` tal como lo definió c93e7a4d20f1 (se reproduce literal para
#: reconstruir la política sin cambiar su semántica de tenant).
OWN_USER = """
  auth_user_id = cotizat_security.context_auth_user_id()
  OR (
    auth_user_id IS NULL
    AND LOWER(email) = cotizat_security.context_email()
  )
"""

USER_SELECT_SQL = f"""
DROP POLICY IF EXISTS cotizat_user_select ON public.usuarios;
CREATE POLICY cotizat_user_select ON public.usuarios
FOR SELECT TO {APP_ROLE}
USING (({OWN_USER}) OR cotizat_security.can_view_user(id) OR ({IS_OPERATOR}))
"""

USER_SELECT_ANTERIOR_SQL = f"""
DROP POLICY IF EXISTS cotizat_user_select ON public.usuarios;
CREATE POLICY cotizat_user_select ON public.usuarios
FOR SELECT TO {APP_ROLE}
USING (({OWN_USER}) OR cotizat_security.can_view_user(id))
"""

MEMBERSHIP_SELECT_SQL = f"""
DROP POLICY IF EXISTS cotizat_membership_select ON public.membresias;
CREATE POLICY cotizat_membership_select ON public.membresias
FOR SELECT TO {APP_ROLE}
USING (
  usuario_id = cotizat_security.current_user_id()
  OR cotizat_security.can_manage_team(organizacion_id)
  OR ({IS_OPERATOR})
)
"""

MEMBERSHIP_SELECT_ANTERIOR_SQL = f"""
DROP POLICY IF EXISTS cotizat_membership_select ON public.membresias;
CREATE POLICY cotizat_membership_select ON public.membresias
FOR SELECT TO {APP_ROLE}
USING (
  usuario_id = cotizat_security.current_user_id()
  OR cotizat_security.can_manage_team(organizacion_id)
)
"""

#: Una fila por organización con lo que el panel necesita para su tabla de
#: clientes. Devuelve cifras y fechas: **nunca** contenido de presupuestos ni
#: datos de los clientes de la empresa.
RESUMEN_ORGANIZACIONES_SQL = f"""
CREATE OR REPLACE FUNCTION cotizat_security.admin_resumen_organizaciones()
RETURNS TABLE(
  organizacion_id integer,
  miembros integer,
  presupuestos integer,
  clientes integer,
  facturas integer,
  total_presupuestado numeric,
  ultimo_acceso timestamp
) LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT
    o.id::integer,
    (SELECT COUNT(*) FROM public.membresias m
      WHERE m.organizacion_id = o.id AND m.activa IS TRUE)::integer,
    (SELECT COUNT(*) FROM public.presupuestos p
      WHERE p.organizacion_id = o.id AND COALESCE(p.es_demo, FALSE) = FALSE)::integer,
    (SELECT COUNT(*) FROM public.clientes c
      WHERE c.organizacion_id = o.id)::integer,
    (SELECT COUNT(*) FROM public.facturas f
      WHERE f.organizacion_id = o.id)::integer,
    COALESCE((SELECT SUM(p.total_calculado) FROM public.presupuestos p
      WHERE p.organizacion_id = o.id AND p.total_calculado > 0), 0)::numeric,
    (SELECT MAX(u.ultimo_acceso_at) FROM public.usuarios u
      JOIN public.membresias m ON m.usuario_id = u.id
      WHERE m.organizacion_id = o.id AND m.activa IS TRUE)
  FROM public.organizaciones o
  WHERE {IS_OPERATOR}
$$
"""

RESUMEN_ORGANIZACIONES_FIRMA = "admin_resumen_organizaciones()"

#: Índices de consulta del panel. Se crean con IF NOT EXISTS porque el
#: arranque best-effort de la aplicación puede haberlos creado ya.
INDICES = (
    ("ix_usuarios_ultimo_acceso", "usuarios", ("ultimo_acceso_at",)),
    (
        "ix_eventos_producto_accion_fecha",
        "eventos_producto",
        ("accion", "created_at"),
    ),
    (
        "ix_eventos_producto_actor_fecha",
        "eventos_producto",
        ("actor_email", "created_at"),
    ),
    ("ix_organizaciones_creada", "organizaciones", ("created_at",)),
)


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    for nombre, tabla, columnas in INDICES:
        op.create_index(nombre, tabla, list(columnas), if_not_exists=True)

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS ni funciones de seguridad.
        return

    op.execute(USER_SELECT_SQL)
    op.execute(MEMBERSHIP_SELECT_SQL)
    op.execute(RESUMEN_ORGANIZACIONES_SQL)
    op.execute(
        f"ALTER FUNCTION cotizat_security.{RESUMEN_ORGANIZACIONES_FIRMA}"
        " OWNER TO CURRENT_USER"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{RESUMEN_ORGANIZACIONES_FIRMA}"
        " FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{RESUMEN_ORGANIZACIONES_FIRMA}"
        f" TO {APP_ROLE}"
    )


def downgrade() -> None:
    if _postgres():
        op.execute(
            f"REVOKE ALL ON FUNCTION "
            f"cotizat_security.{RESUMEN_ORGANIZACIONES_FIRMA} FROM {APP_ROLE}"
        )
        op.execute(
            f"DROP FUNCTION IF EXISTS "
            f"cotizat_security.{RESUMEN_ORGANIZACIONES_FIRMA}"
        )
        op.execute(USER_SELECT_ANTERIOR_SQL)
        op.execute(MEMBERSHIP_SELECT_ANTERIOR_SQL)

    for nombre, tabla, _columnas in INDICES:
        op.drop_index(nombre, table_name=tabla, if_exists=True)
