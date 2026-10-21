-- CotizaT — actualización de o2e4a6c8b1d3 a p3f7a1c9d2e4
-- Añade identidad del usuario a los errores internos y amplía la unidad
-- descriptiva del producto presupuestado (20 -> 120 caracteres).
-- Ejecutar una sola vez en Supabase SQL Editor como administrador, solo si
-- public.alembic_version contiene o2e4a6c8b1d3.
BEGIN;

DO $$
BEGIN
  IF (SELECT version_num FROM public.alembic_version LIMIT 1) IS DISTINCT FROM 'o2e4a6c8b1d3' THEN
    RAISE EXCEPTION 'Head inesperado; se esperaba o2e4a6c8b1d3';
  END IF;
END $$;

ALTER TABLE public.errores_internos
  ADD COLUMN usuario_email varchar(254) NOT NULL DEFAULT '',
  ADD COLUMN usuario_nombre varchar(200) NOT NULL DEFAULT '';

ALTER TABLE public.presupuesto_items
  ALTER COLUMN producto_unidad TYPE varchar(120);

DROP FUNCTION cotizat_security.registrar_error_interno(
  text, text, text, text, text, text, timestamp without time zone
);

CREATE OR REPLACE FUNCTION cotizat_security.registrar_error_interno(
  p_huella text,
  p_metodo text,
  p_ruta text,
  p_tipo text,
  p_mensaje text,
  p_traza text,
  p_usuario_email text,
  p_usuario_nombre text,
  p_ahora timestamp without time zone
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_avisar boolean;
BEGIN
  WITH previo AS (
    SELECT resuelto_en IS NOT NULL AS estaba_resuelto
    FROM public.errores_internos WHERE huella = p_huella
  ), upsert AS (
    INSERT INTO public.errores_internos (
      huella, metodo, ruta, tipo, mensaje, traza, usuario_email, usuario_nombre,
      ocurrencias, primera_vez, ultima_vez, resuelto_en
    ) VALUES (
      p_huella,
      left(COALESCE(p_metodo, ''), 10),
      left(COALESCE(NULLIF(p_ruta, ''), '/'), 160),
      left(COALESCE(p_tipo, ''), 120),
      left(COALESCE(p_mensaje, ''), 300),
      COALESCE(p_traza, ''),
      left(COALESCE(p_usuario_email, ''), 254),
      left(COALESCE(p_usuario_nombre, ''), 200),
      1, p_ahora, p_ahora, NULL
    )
    ON CONFLICT (huella) DO UPDATE SET
      ocurrencias = public.errores_internos.ocurrencias + 1,
      ultima_vez = EXCLUDED.ultima_vez,
      traza = EXCLUDED.traza,
      usuario_email = EXCLUDED.usuario_email,
      usuario_nombre = EXCLUDED.usuario_nombre,
      resuelto_en = NULL
    RETURNING (xmax = 0) AS insertado
  )
  SELECT insertado OR COALESCE((SELECT estaba_resuelto FROM previo), FALSE)
  INTO v_avisar FROM upsert;
  RETURN COALESCE(v_avisar, FALSE);
END;
$$;

REVOKE ALL ON FUNCTION cotizat_security.registrar_error_interno(
  text, text, text, text, text, text, text, text, timestamp without time zone
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cotizat_security.registrar_error_interno(
  text, text, text, text, text, text, text, text, timestamp without time zone
) TO cotizat_app;

UPDATE public.alembic_version SET version_num = 'p3f7a1c9d2e4'
WHERE version_num = 'o2e4a6c8b1d3';

COMMIT;

-- Verificar: SELECT version_num FROM public.alembic_version;
-- Debe devolver p3f7a1c9d2e4. /readyz debe indicar head:p3f7a1c9d2e4.
