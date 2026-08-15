-- CotizaT — actualización de c93e7a4d20f1 a d7f2a9c41e63
-- Corrige el 500 al aceptar invitaciones de equipo.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Solo si tu base YA está en c93e7a4d20f1 (compruébalo antes con:
--   SELECT version_num FROM alembic_version;
-- ). Va dentro de una transacción: si algo falla, no se aplica nada.

BEGIN;

-- El destinatario sigue viendo su invitación después de aceptarla (solo si la
-- aceptó él). PostgreSQL evalúa el USING de las políticas SELECT como WITH
-- CHECK sobre la fila nueva del UPDATE: la versión anterior exigía
-- «accepted_at IS NULL», justo lo que el UPDATE de aceptación elimina, y por
-- eso la reclamación del token devolvía 500.
DROP POLICY IF EXISTS cotizat_invitation_select_recipient ON public.invitaciones_organizacion;

CREATE POLICY cotizat_invitation_select_recipient
        ON public.invitaciones_organizacion
        FOR SELECT TO cotizat_app
        USING (
      email = cotizat_security.current_user_email()
      AND cotizat_security.current_user_is_verified()
      AND revoked_at IS NULL
      AND expires_at > pg_catalog.clock_timestamp()
      AND (
        accepted_at IS NULL
        OR aceptada_por_usuario_id = cotizat_security.current_user_id()
      )
    );

UPDATE alembic_version
SET version_num = 'd7f2a9c41e63'
WHERE version_num = 'c93e7a4d20f1';

COMMIT;

-- Verificación: debe devolver d7f2a9c41e63
SELECT version_num FROM alembic_version;

-- Verificación: la política debe incluir la rama «aceptada_por_usuario_id»
SELECT qual FROM pg_policies
WHERE tablename = 'invitaciones_organizacion'
  AND policyname = 'cotizat_invitation_select_recipient';
