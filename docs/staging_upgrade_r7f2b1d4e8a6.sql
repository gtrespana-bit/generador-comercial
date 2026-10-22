-- CotizaT — actualización de q5e1c8a9d3f7 a r7f2b1d4e8a6
-- Analítica operativa: el panel de operador deja de medir a ciegas.
--
-- Contenido:
--   1. Política cotizat_user_select: el operador puede leer todos los
--      usuarios. Antes solo veía el suyo (can_view_user siempre da falso sin
--      organización de contexto), así que «Cuentas» contaba 1 —el propio
--      operador— y la serie de registros por día solo veía sus altas.
--   2. Política cotizat_membership_select: el operador puede leer todas las
--      membresías, para contar miembros por empresa y su último acceso.
--   3. Función cotizat_security.admin_resumen_organizaciones(): una fila por
--      empresa con miembros, presupuestos (sin demos), clientes, facturas,
--      total presupuestado y último acceso. SECURITY DEFINER y cerrada a
--      sesiones de operador; solo devuelve cifras, nunca contenido.
--   4. Índices del panel: último acceso por usuario y eventos por
--      acción/actor con la fecha.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser q5e1c8a9d3f7
--
-- No modifica ni borra ningún dato: solo políticas, una función de lectura e
-- índices. Se puede revertir con el otro sentido de las políticas y
-- DROP FUNCTION (ver migrations/versions/r7f2b1d4e8a6_analitica_operativa.py).
BEGIN;

DO $$
BEGIN
  IF (SELECT version_num FROM public.alembic_version LIMIT 1) IS DISTINCT FROM 'q5e1c8a9d3f7' THEN
    RAISE EXCEPTION 'Head inesperado; se esperaba q5e1c8a9d3f7';
  END IF;
END $$;

-- Running upgrade q5e1c8a9d3f7 -> r7f2b1d4e8a6

-- 1) Índices del panel. IF NOT EXISTS porque el arranque best-effort de la
--    aplicación puede haberlos creado ya en una instalación SQLite.
CREATE INDEX IF NOT EXISTS ix_usuarios_ultimo_acceso
  ON public.usuarios (ultimo_acceso_at);

CREATE INDEX IF NOT EXISTS ix_eventos_producto_accion_fecha
  ON public.eventos_producto (accion, created_at);

CREATE INDEX IF NOT EXISTS ix_eventos_producto_actor_fecha
  ON public.eventos_producto (actor_email, created_at);

CREATE INDEX IF NOT EXISTS ix_organizaciones_creada
  ON public.organizaciones (created_at);

-- 2) El operador ve usuarios. Se reproduce literal la rama «own_user» de
--    c93e7a4d20f1 para no cambiar la semántica de tenant; solo se añade la
--    rama de operador que ya tiene cotizat_org_select desde b7c4a9e2d31f.
DROP POLICY IF EXISTS cotizat_user_select ON public.usuarios;
CREATE POLICY cotizat_user_select ON public.usuarios
FOR SELECT TO cotizat_app
USING (
  (
    auth_user_id = cotizat_security.context_auth_user_id()
    OR (
      auth_user_id IS NULL
      AND LOWER(email) = cotizat_security.context_email()
    )
  )
  OR cotizat_security.can_view_user(id)
  OR COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
);

-- 3) El operador ve membresías (miembros por empresa y último acceso).
DROP POLICY IF EXISTS cotizat_membership_select ON public.membresias;
CREATE POLICY cotizat_membership_select ON public.membresias
FOR SELECT TO cotizat_app
USING (
  usuario_id = cotizat_security.current_user_id()
  OR cotizat_security.can_manage_team(organizacion_id)
  OR COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
);

-- 4) Agregados por empresa en una sola consulta (una fila por organización).
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
  WHERE COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
$$;;

ALTER FUNCTION cotizat_security.admin_resumen_organizaciones() OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.admin_resumen_organizaciones() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.admin_resumen_organizaciones() TO cotizat_app;

UPDATE public.alembic_version SET version_num='r7f2b1d4e8a6' WHERE alembic_version.version_num = 'q5e1c8a9d3f7';

COMMIT;


-- Verificar: SELECT version_num FROM public.alembic_version; debe devolver r7f2b1d4e8a6.
-- Y que la función responde como operador:
--   SET LOCAL cotizat.es_operador = 'on';
--   SELECT * FROM cotizat_security.admin_resumen_organizaciones();
-- Como sesión de cliente debe devolver cero filas (no es un error).
