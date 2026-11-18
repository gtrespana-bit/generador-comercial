"""Hibernación sin pérdida y siembra bajo demanda del catálogo oficial.

Cada organización con modo ``demo`` clona ~3.000 filas en ``public.partidas``
(~5,6 MB por empresa). Cuando decenas de pruebas gratuitas expiran sin haber
tocado el catálogo, esas copias idénticas ocupan cientos de megabytes en el
plan gratuito de Supabase sin aportar ningún dato propio.

Este módulo resuelve el problema en dos frentes complementarios y reversibles:

1. **Siembra bajo demanda en web** (``COTIZAT_CATALOGO_BAJO_DEMANDA``, activa
   por omisión en PostgreSQL y apagada en SQLite de escritorio): al completar
   ``/bienvenida`` se siembran de inmediato categorías, recursos, productos,
   recetas y el presupuesto de ejemplo del país, y se marca
   ``configuracion.version_catalogo = CATALOGO_HIBERNADO`` (``-1``). Las ~3.000
   partidas oficiales se materializan automáticamente la primera vez que la
   organización entra en ``/partidas``, el editor de presupuestos, ``/recursos``,
   el buscador o la consulta de catálogo del asistente.

2. **Hibernación automática de catálogos inactivos**
   (``COTIZAT_CATALOGO_HIBERNAR_DIAS``, por omisión 7 días): el cron diario
   retira únicamente las partidas oficiales **100 % intactas** de pruebas
   vencidas hace más de N días (o sin licencia y con más de N días de
   antigüedad) que **jamás** hayan tenido una licencia de ``pago``,
   ``cortesia`` o ``compensacion``. Se conservan siempre intactas:

   - todas las organizaciones con licencia vigente o vencida hace menos de N días;
   - todas las organizaciones que alguna vez pagaron o recibieron cortesía/compensación;
   - presupuestos, líneas, clientes, facturas, obras, productos, recetas y recursos;
   - partidas propias (``es_oficial = FALSE``) o reclasificadas (``version_catalogo < 2``);
   - partidas usadas (``usos > 0`` o ``ultimo_uso IS NOT NULL``);
   - partidas ocultas por el usuario (``oculta = TRUE``) o con imagen propia;
   - partidas referenciadas desde ``presupuesto_items.partida_catalogo_id``;
   - partidas con cualquier evento en ``eventos_auditoria``;
   - partidas editadas (``descomposicion_json`` distinto de ``catalogo_propio`` o
     ``fecha_actualizacion_precio`` posterior a la siembra de su versión).

   Al hibernar una organización se anota ``version_catalogo = -1``: si el
   cliente vuelve meses después y contrata un plan, ``asegurar_catalogo_propio``
   repone las partidas oficiales ausentes en la versión vigente respetando todas
   sus partidas propias/editadas/usadas y sus tarifas de recursos revisadas.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta

from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

logger = logging.getLogger("cotizat.hibernacion_catalogo")

#: Marca en ``configuracion.version_catalogo`` que indica que las partidas
#: oficiales no tocadas están diferidas o hibernadas y deben reponerse de forma
#: transparente al abrir el catálogo.
CATALOGO_HIBERNADO = -1

#: Días tras el vencimiento de la prueba antes de hibernar partidas oficiales
#: intactas. ``0`` desactiva el barrido en el cron.
DIAS_HIBERNACION_DEFAULT = 7
DIAS_HIBERNACION_MAX = 3650

#: Máximo de organizaciones procesadas por disparo del cron (mantiene el trabajo
#: muy por debajo del presupuesto de 60 s de Vercel).
LIMITE_ORGS_DEFAULT = 10
LIMITE_ORGS_MAX = 100

#: Orígenes de licencia que nunca se hibernan automáticamente aunque venzan.
ORIGENES_LICENCIA_PROTEGIDOS = ("pago", "cortesia", "compensacion")

#: Prefijo JSON exacto de una descomposición oficial no editada por el usuario
#: (al guardar una ficha en ``/partidas``, ``origen`` cambia a ``"manual"``).
PREFIJO_ORIGEN_OFICIAL = '{"origen": "catalogo_propio"'

#: Margen máximo entre la primera y la última fila oficial de una misma versión
#: sembrada en lote; un ``fecha_actualizacion_precio`` posterior delata un
#: ajuste individual o masivo de precios y protege la fila.
MARGEN_SIEMBRA_SEGUNDOS = 300

APP_ROLE = "cotizat_app"
FUNCTION_SIGNATURE = "hibernar_catalogos_inactivos(integer, integer)"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""

HIBERNAR_CATALOGOS_FUNCTION_SQL = f"""
CREATE OR REPLACE FUNCTION cotizat_security.hibernar_catalogos_inactivos(
  p_dias_inactivo integer DEFAULT {DIAS_HIBERNACION_DEFAULT},
  p_limite_orgs integer DEFAULT {LIMITE_ORGS_DEFAULT}
) RETURNS TABLE(
  organizaciones_hibernadas integer,
  partidas_eliminadas integer
) LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_dias integer := LEAST(GREATEST(COALESCE(p_dias_inactivo, {DIAS_HIBERNACION_DEFAULT}), 1), {DIAS_HIBERNACION_MAX});
  v_limite integer := LEAST(GREATEST(COALESCE(p_limite_orgs, {LIMITE_ORGS_DEFAULT}), 1), {LIMITE_ORGS_MAX});
  v_org_id integer;
  v_borradas integer;
  v_total_orgs integer := 0;
  v_total_partidas integer := 0;
BEGIN
  IF NOT ({IS_OPERATOR}) THEN
    RAISE EXCEPTION
      'La hibernación de catálogos requiere una sesión de operador.'
      USING ERRCODE = '42501';
  END IF;

  FOR v_org_id IN
    SELECT c.organizacion_id
    FROM public.configuracion c
    JOIN public.organizaciones o ON o.id = c.organizacion_id
    WHERE COALESCE(c.semilla_catalogo_aplicada, FALSE) IS TRUE
      AND COALESCE(c.version_catalogo, 0) >= 2
      AND COALESCE(c.onboarding_modo, '') <> 'limpio'
      AND (
        o.created_at IS NULL
        OR o.created_at < (pg_catalog.now() - pg_catalog.make_interval(days => v_dias))
      )
      AND NOT EXISTS (
        SELECT 1
        FROM public.licencias l
        WHERE l.organizacion_id = c.organizacion_id
          AND (
            (l.estado = 'activa' AND l.vence >= (CURRENT_DATE - v_dias))
            OR l.origen IN ('pago', 'cortesia', 'compensacion')
          )
      )
      AND NOT EXISTS (
        SELECT 1
        FROM public.eventos_auditoria ea_masivo
        WHERE ea_masivo.organizacion_id = c.organizacion_id
          AND ea_masivo.accion = 'catalogo.precios_ajustados'
      )
      AND EXISTS (
        SELECT 1
        FROM public.partidas p0
        WHERE p0.organizacion_id = c.organizacion_id
          AND p0.es_oficial IS TRUE
          AND COALESCE(p0.version_catalogo, 0) >= 2
          AND COALESCE(p0.usos, 0) = 0
          AND p0.ultimo_uso IS NULL
          AND COALESCE(p0.oculta, FALSE) IS FALSE
          AND COALESCE(p0.imagen, '') = ''
          AND COALESCE(p0.descomposicion_json, '') LIKE '{PREFIJO_ORIGEN_OFICIAL}%'
          AND NOT (
            p0.fecha_actualizacion_precio IS NOT NULL
            AND p0.created_at IS NOT NULL
            AND p0.fecha_actualizacion_precio > (
              p0.created_at + pg_catalog.make_interval(secs => {MARGEN_SIEMBRA_SEGUNDOS})
            )
          )
          AND NOT EXISTS (
            SELECT 1
            FROM public.presupuesto_items pi0
            WHERE pi0.organizacion_id = c.organizacion_id
              AND pi0.partida_catalogo_id = p0.id
          )
          AND NOT EXISTS (
            SELECT 1
            FROM public.eventos_auditoria ea0
            WHERE ea0.organizacion_id = c.organizacion_id
              AND ea0.entidad = 'partida'
              AND ea0.entidad_id = p0.id
          )
      )
    ORDER BY c.organizacion_id
    LIMIT v_limite
  LOOP
    WITH refs AS (
      SELECT DISTINCT pi.partida_catalogo_id AS pid
      FROM public.presupuesto_items pi
      WHERE pi.organizacion_id = v_org_id
        AND pi.partida_catalogo_id IS NOT NULL
    ),
    auditadas AS (
      SELECT DISTINCT ea.entidad_id AS pid
      FROM public.eventos_auditoria ea
      WHERE ea.organizacion_id = v_org_id
        AND ea.entidad = 'partida'
        AND ea.entidad_id IS NOT NULL
    ),
    fap_base AS (
      SELECT p2.version_catalogo,
             pg_catalog.min(p2.fecha_actualizacion_precio) AS min_fap
      FROM public.partidas p2
      WHERE p2.organizacion_id = v_org_id
        AND p2.es_oficial IS TRUE
        AND COALESCE(p2.version_catalogo, 0) >= 2
      GROUP BY p2.version_catalogo
    ),
    borrado AS (
      DELETE FROM public.partidas p
      WHERE p.organizacion_id = v_org_id
        AND p.es_oficial IS TRUE
        AND COALESCE(p.version_catalogo, 0) >= 2
        AND COALESCE(p.usos, 0) = 0
        AND p.ultimo_uso IS NULL
        AND COALESCE(p.oculta, FALSE) IS FALSE
        AND COALESCE(p.imagen, '') = ''
        AND COALESCE(p.descomposicion_json, '') LIKE '{PREFIJO_ORIGEN_OFICIAL}%'
        AND NOT (
          p.fecha_actualizacion_precio IS NOT NULL
          AND p.created_at IS NOT NULL
          AND p.fecha_actualizacion_precio > (
            p.created_at + pg_catalog.make_interval(secs => {MARGEN_SIEMBRA_SEGUNDOS})
          )
        )
        AND NOT EXISTS (SELECT 1 FROM refs r WHERE r.pid = p.id)
        AND NOT EXISTS (SELECT 1 FROM auditadas a WHERE a.pid = p.id)
        AND NOT EXISTS (
          SELECT 1
          FROM fap_base fb
          WHERE fb.version_catalogo = p.version_catalogo
            AND p.fecha_actualizacion_precio IS NOT NULL
            AND fb.min_fap IS NOT NULL
            AND p.fecha_actualizacion_precio > (
              fb.min_fap + pg_catalog.make_interval(secs => {MARGEN_SIEMBRA_SEGUNDOS})
            )
        )
      RETURNING 1
    )
    SELECT pg_catalog.count(*)::integer INTO v_borradas FROM borrado;

    IF v_borradas > 0 THEN
      UPDATE public.configuracion
      SET version_catalogo = {CATALOGO_HIBERNADO}
      WHERE organizacion_id = v_org_id;
      v_total_orgs := v_total_orgs + 1;
      v_total_partidas := v_total_partidas + v_borradas;
    END IF;
  END LOOP;

  RETURN QUERY SELECT v_total_orgs, v_total_partidas;
END;
$$
"""


def catalogo_bajo_demanda_activado(*, es_sqlite: bool) -> bool:
    """Indica si el alta en modo ``demo`` difiere la copia de ``partidas``.

    En PostgreSQL (web multi-tenant) está activo por omisión para no clonar
    ~3.000 filas por cada registro que aún no abre el catálogo. En SQLite
    (instalador de escritorio sin servidor y pruebas unitarias locales) está
    desactivado por omisión salvo que se fuerce por variable de entorno.
    """
    raw = os.environ.get("COTIZAT_CATALOGO_BAJO_DEMANDA", "").strip().lower()
    if raw in ("1", "true", "yes", "si", "sí", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return not es_sqlite


def dias_hibernacion_catalogo() -> int:
    """Ventana en días tras el vencimiento antes de hibernar (``0`` apaga)."""
    raw = os.environ.get("COTIZAT_CATALOGO_HIBERNAR_DIAS", "").strip()
    if not raw:
        return DIAS_HIBERNACION_DEFAULT
    try:
        valor = int(raw)
    except ValueError:
        return DIAS_HIBERNACION_DEFAULT
    if valor <= 0:
        return 0
    return min(valor, DIAS_HIBERNACION_MAX)


def limite_orgs_hibernacion() -> int:
    """Tope de organizaciones hibernadas por ejecución del cron."""
    raw = os.environ.get("COTIZAT_CATALOGO_HIBERNAR_LIMITE", "").strip()
    if not raw:
        return LIMITE_ORGS_DEFAULT
    try:
        valor = int(raw)
    except ValueError:
        return LIMITE_ORGS_DEFAULT
    return max(1, min(valor, LIMITE_ORGS_MAX))


def funcion_hibernacion_disponible(conn) -> bool:
    """Comprueba que la función ``SECURITY DEFINER`` exista y sea ejecutable."""
    reg = f"cotizat_security.{FUNCTION_SIGNATURE}"
    return bool(
        conn.execute(
            text(
                """
                SELECT
                  pg_catalog.to_regprocedure(:reg) IS NOT NULL
                  AND EXISTS (
                    SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = :role
                  )
                  AND pg_catalog.has_function_privilege(
                    :role,
                    :reg,
                    'EXECUTE'
                  )
                """
            ),
            {"reg": reg, "role": APP_ROLE},
        ).scalar_one()
    )


def instalar_funcion_hibernacion(conn) -> None:
    """Crea/actualiza la función de hibernación y restringe su ejecución."""
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS cotizat_security"))
    conn.execute(text(HIBERNAR_CATALOGOS_FUNCTION_SQL))
    conn.execute(
        text(
            f"ALTER FUNCTION cotizat_security.{FUNCTION_SIGNATURE} "
            "OWNER TO CURRENT_USER"
        )
    )
    conn.execute(
        text(
            f"REVOKE ALL ON FUNCTION cotizat_security.{FUNCTION_SIGNATURE} "
            "FROM PUBLIC"
        )
    )
    conn.execute(
        text(
            f"GRANT EXECUTE ON FUNCTION cotizat_security.{FUNCTION_SIGNATURE} "
            f"TO {APP_ROLE}"
        )
    )


def _es_postgres(db: Session) -> bool:
    bind = db.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def _hibernar_sqlite(
    db: Session,
    *,
    dias: int,
    limite: int,
    hoy: date,
    ahora: datetime,
) -> tuple[int, int]:
    """Equivalente exacto en ORM para SQLite (pruebas y entorno local)."""
    from ..models import (
        Configuracion,
        EventoAuditoria,
        Licencia,
        Organizacion,
        Partida,
        PresupuestoItem,
    )

    corte_fecha = hoy - timedelta(days=dias)
    corte_ts = ahora - timedelta(days=dias)
    margen_fap = timedelta(seconds=MARGEN_SIEMBRA_SEGUNDOS)

    protegidas: set[int] = set()
    for (org_id,) in (
        db.query(Licencia.organizacion_id)
        .filter(
            or_(
                (Licencia.estado == "activa") & (Licencia.vence >= corte_fecha),
                Licencia.origen.in_(ORIGENES_LICENCIA_PROTEGIDOS),
            )
        )
        .distinct()
        .all()
    ):
        if org_id is not None:
            protegidas.add(int(org_id))
    for (org_id,) in (
        db.query(EventoAuditoria.organizacion_id)
        .filter(EventoAuditoria.accion == "catalogo.precios_ajustados")
        .distinct()
        .all()
    ):
        if org_id is not None:
            protegidas.add(int(org_id))

    configs = (
        db.query(Configuracion)
        .join(Organizacion, Organizacion.id == Configuracion.organizacion_id)
        .filter(
            Configuracion.semilla_catalogo_aplicada.is_(True),
            func.coalesce(Configuracion.version_catalogo, 0) >= 2,
            func.coalesce(Configuracion.onboarding_modo, "") != "limpio",
            or_(
                Organizacion.created_at.is_(None),
                Organizacion.created_at < corte_ts,
            ),
        )
        .order_by(Configuracion.organizacion_id)
        .all()
    )

    total_orgs = 0
    total_partidas = 0
    for cfg in configs:
        if total_orgs >= limite:
            break
        org_id = int(cfg.organizacion_id)
        if org_id in protegidas:
            continue

        refs = {
            int(pid)
            for (pid,) in db.query(PresupuestoItem.partida_catalogo_id)
            .filter(
                PresupuestoItem.organizacion_id == org_id,
                PresupuestoItem.partida_catalogo_id.isnot(None),
            )
            .distinct()
            .all()
        }
        auditadas = {
            int(pid)
            for (pid,) in db.query(EventoAuditoria.entidad_id)
            .filter(
                EventoAuditoria.organizacion_id == org_id,
                EventoAuditoria.entidad == "partida",
                EventoAuditoria.entidad_id.isnot(None),
            )
            .distinct()
            .all()
        }
        min_fap_por_version = {
            int(ver): min_fap
            for ver, min_fap in db.query(
                Partida.version_catalogo,
                func.min(Partida.fecha_actualizacion_precio),
            )
            .filter(
                Partida.organizacion_id == org_id,
                Partida.es_oficial.is_(True),
                func.coalesce(Partida.version_catalogo, 0) >= 2,
            )
            .group_by(Partida.version_catalogo)
            .all()
            if ver is not None
        }

        candidatas = (
            db.query(Partida)
            .filter(
                Partida.organizacion_id == org_id,
                Partida.es_oficial.is_(True),
                func.coalesce(Partida.version_catalogo, 0) >= 2,
                func.coalesce(Partida.usos, 0) == 0,
                Partida.ultimo_uso.is_(None),
                func.coalesce(Partida.oculta, False).is_(False),
                func.coalesce(Partida.imagen, "") == "",
            )
            .all()
        )
        ids_borrar: list[int] = []
        for partida in candidatas:
            if partida.id in refs or partida.id in auditadas:
                continue
            descomp = partida.descomposicion_json or ""
            if not descomp.startswith(PREFIJO_ORIGEN_OFICIAL):
                continue
            if (
                partida.fecha_actualizacion_precio is not None
                and partida.created_at is not None
                and partida.fecha_actualizacion_precio > (partida.created_at + margen_fap)
            ):
                continue
            min_fap = min_fap_por_version.get(int(partida.version_catalogo or 0))
            if (
                min_fap is not None
                and partida.fecha_actualizacion_precio is not None
                and partida.fecha_actualizacion_precio > (min_fap + margen_fap)
            ):
                continue
            ids_borrar.append(int(partida.id))

        if not ids_borrar:
            continue

        # Borrar en bloques para respetar el límite de parámetros de SQLite.
        borradas = 0
        for inicio in range(0, len(ids_borrar), 500):
            bloque = ids_borrar[inicio : inicio + 500]
            borradas += (
                db.query(Partida)
                .filter(
                    Partida.organizacion_id == org_id,
                    Partida.id.in_(bloque),
                )
                .delete(synchronize_session=False)
            )
        if borradas > 0:
            cfg.version_catalogo = CATALOGO_HIBERNADO
            total_orgs += 1
            total_partidas += int(borradas)

    return total_orgs, total_partidas


def hibernar_catalogos_inactivos(
    db_operador: Session,
    *,
    dias: int | None = None,
    limite_orgs: int | None = None,
    hoy: date | None = None,
    ahora: datetime | None = None,
) -> dict:
    """Hiberna partidas oficiales intactas de pruebas vencidas (tarea de cron).

    Nunca toca organizaciones con licencia activa, en ventana de gracia ni con
    historial de pago/cortesía/compensación, ni partidas propias, usadas,
    ocultas, editadas, auditadas o enlazadas desde presupuestos.
    """
    ventana = dias_hibernacion_catalogo() if dias is None else max(0, int(dias))
    if ventana <= 0:
        return {
            "activado": False,
            "organizaciones": 0,
            "partidas": 0,
            "dias": 0,
        }
    limite = (
        limite_orgs_hibernacion()
        if limite_orgs is None
        else max(1, min(int(limite_orgs), LIMITE_ORGS_MAX))
    )

    if _es_postgres(db_operador):
        try:
            fila = db_operador.execute(
                text(
                    "SELECT organizaciones_hibernadas, partidas_eliminadas "
                    "FROM cotizat_security.hibernar_catalogos_inactivos("
                    ":dias, :limite)"
                ),
                {"dias": ventana, "limite": limite},
            ).first()
            db_operador.commit()
            n_orgs = int((fila[0] if fila else 0) or 0)
            n_partidas = int((fila[1] if fila else 0) or 0)
        except Exception as exc:
            db_operador.rollback()
            # Si el despliegue llega antes de instalar la función SECURITY
            # DEFINER, degradamos con gracia sin romper el cron diario.
            codigo = getattr(getattr(exc, "orig", None), "sqlstate", "") or ""
            if codigo in ("42883", "42501"):
                logger.warning(
                    "Función de hibernación de catálogos aún no disponible (%s).",
                    codigo,
                )
                return {
                    "activado": True,
                    "organizaciones": 0,
                    "partidas": 0,
                    "dias": ventana,
                    "omitido": "funcion no disponible",
                }
            raise
    else:
        fecha_ref = hoy or date.today()
        ts_ref = ahora or datetime.utcnow()
        n_orgs, n_partidas = _hibernar_sqlite(
            db_operador,
            dias=ventana,
            limite=limite,
            hoy=fecha_ref,
            ahora=ts_ref,
        )
        db_operador.commit()

    if n_partidas:
        logger.info(
            "Catálogos hibernados: %d organizaciones, %d partidas oficiales "
            "intactas liberadas (ventana >%d días).",
            n_orgs,
            n_partidas,
            ventana,
        )
    return {
        "activado": True,
        "organizaciones": n_orgs,
        "partidas": n_partidas,
        "dias": ventana,
    }
