"""Mantenimiento automático del despliegue (E4-021 / E4-023).

Un único trabajo programado (Vercel Cron, ``/api/cron/mantenimiento``) ejecuta
cada día las dos tareas de operación que no dependen de una sesión humana:

* **Respaldo automático por organización (E4-021).** Para cada organización se
  genera el mismo paquete verificable de E3-020 (``app/services/respaldo.py``)
  y se guarda en el almacenamiento privado bajo
  ``organizaciones/<id>/respaldo_automatico/…`` con retención de las últimas N
  copias (``COTIZAT_RESPALDO_RETENCION``, 14 por omisión). Es la capa de
  conveniencia —copias portátiles y restaurables desde la propia app—; la capa
  de infraestructura (copias del proyecto en Supabase) es complementaria y se
  documenta aparte en ``docs/RESPALDO_Y_RESTAURACION_WEB.md``.

  Los zips NO se registran como ``ArchivoAlmacenado``: se escriben con el
  backend directamente para que el respaldo no crezca con sus propias copias
  anteriores. Las organizaciones cuyo paquete supere el límite configurable
  (``COTIZAT_RESPALDO_MAX_MB``, 12 MB por omisión, el tope del bucket) se
  reportan como omitidas, nunca rompen la ejecución.

* **Verificación diaria con alerta (E4-023).** Ejecuta los mismos chequeos de
  ``/readyz``; si algo falla, avisa por correo a los operadores
  (``COTIZAT_OPERADORES``) con el detalle de los errores. La disponibilidad en
  tiempo real sigue siendo responsabilidad de un vigilante externo
  (p. ej. UptimeRobot sobre ``/healthz``), documentado en
  ``docs/MONITORIZACION_Y_DIAGNOSTICO.md``.

Ninguna de las dos toca datos de negocio fuera de su organización: la sesión
es de operador del sistema (como el cron de recordatorios) y cada respaldo se
genera con el contexto de su propia organización (``establecer_contexto_organizacion``).
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import date

from ..database import SessionLocal, establecer_contexto_organizacion
from ..models import Organizacion
from ..storage import StorageError, get_storage_backend, validate_tenant_object_key
from .respaldo import ErrorRespaldo, generar_respaldo

logger = logging.getLogger("cotizat.mantenimiento")

#: Carpeta dentro de cada organización donde viven las copias automáticas.
PREFIJO_RESPALDOS = "respaldo_automatico"


# ---------------------------------------------------------------------------
# Respaldo automático (E4-021)
# ---------------------------------------------------------------------------


def _respaldo_automatico_activado() -> bool:
    """Interruptor: `COTIZAT_RESPALDO_AUTOMATICO=false` apaga el barrido."""
    valor = os.environ.get("COTIZAT_RESPALDO_AUTOMATICO", "true").strip().lower()
    return valor not in {"0", "false", "no", "off"}


def _max_bytes() -> int:
    """Límite del paquete por organización (MB → bytes). 0 = sin límite."""
    crudo = os.environ.get("COTIZAT_RESPALDO_MAX_MB", "12") or "12"
    try:
        mb = int(float(crudo))
    except (TypeError, ValueError):
        mb = 12
    return max(0, mb) * 1024 * 1024


def _retencion() -> int:
    """Número de copias que se conservan por organización (mínimo 1)."""
    crudo = os.environ.get("COTIZAT_RESPALDO_RETENCION", "14") or "14"
    try:
        valor = int(crudo)
    except (TypeError, ValueError):
        valor = 14
    return max(1, valor)


def _clave_respaldo(organizacion_id: int, fecha: date) -> str:
    """Clave del zip del día para una organización (bajo el prefijo de tenant)."""
    return validate_tenant_object_key(
        f"organizaciones/{int(organizacion_id)}/{PREFIJO_RESPALDOS}/"
        f"cotizat-respaldo-{fecha.isoformat()}.zip",
        organizacion_id,
    )


def _purgar_antiguos(
    backend, organizacion_id: int, retencion: int, fecha: date
) -> list[str]:
    """Borra las copias más antiguas conservando las `retencion` más nuevas.

    Las claves ordenadas equivalen a orden cronológico (la fecha es ISO), así
    que mantener la cola es ordenar y recortar. Devuelve las claves borradas.
    """
    prefijo = f"organizaciones/{int(organizacion_id)}/{PREFIJO_RESPALDOS}/"
    claves = [
        clave
        for clave in backend.list(prefijo)
        if clave.startswith(prefijo) and clave.endswith(".zip")
    ]
    # La copia del día se acaba de escribir; si por cualquier motivo no está en
    # el listado (consistencia eventual), se añade para no borrarla.
    clave_hoy = _clave_respaldo(organizacion_id, fecha)
    if clave_hoy not in claves:
        claves.append(clave_hoy)
    conservar = set(sorted(claves)[-retencion:])
    borradas = []
    for clave in claves:
        if clave not in conservar:
            try:
                backend.delete(clave)
            except StorageError as exc:  # pragma: no cover - red/infra
                logger.warning("No se pudo borrar la copia antigua %s: %s", clave, exc)
                continue
            borradas.append(clave)
    return borradas


def _respaldo_de_organizacion(db_operador, organizacion: Organizacion) -> dict:
    """Genera y guarda el respaldo del día para una organización (o reporta)."""
    nombre = organizacion.nombre or organizacion.slug
    try:
        with SessionLocal() as sesion:
            sesion.info["es_operador"] = True
            establecer_contexto_organizacion(sesion, organizacion.id)
            paquete = generar_respaldo(sesion)
    except ErrorRespaldo as exc:
        logger.warning("Respaldo automático de %s omitido: %s", nombre, exc)
        return {"organizacion": nombre, "estado": "error", "error": str(exc)}

    limite = _max_bytes()
    if limite and len(paquete) > limite:
        motivo = (
            f"El paquete supera el límite de {limite // (1024 * 1024)} MB "
            f"del respaldo automático; usa el respaldo manual (E3-020)."
        )
        logger.warning("Respaldo automático de %s omitido: %s", nombre, motivo)
        return {"organizacion": nombre, "estado": "omitido", "motivo": motivo}

    fecha = date.today()
    clave = _clave_respaldo(organizacion.id, fecha)
    backend = get_storage_backend()
    try:
        backend.put(clave, paquete, "application/zip", max_size=limite or None)
    except StorageError as exc:
        logger.warning("No se pudo guardar el respaldo de %s: %s", nombre, exc)
        return {"organizacion": nombre, "estado": "error", "error": str(exc)}

    purgadas: list[str] = []
    try:
        purgadas = _purgar_antiguos(backend, organizacion.id, _retencion(), fecha)
    except StorageError as exc:  # pragma: no cover - red/infra
        logger.warning("Retención de respaldos de %s falló: %s", nombre, exc)

    digest = hashlib.sha256(paquete).hexdigest()
    logger.info(
        "Respaldo automático de %s guardado (%d bytes, sha256 %.12s…)",
        nombre, len(paquete), digest,
    )
    return {
        "organizacion": nombre,
        "estado": "ok",
        "clave": clave,
        "bytes": len(paquete),
        "sha256": digest,
        "borradas_retencion": len(purgadas),
    }


def ejecutar_respaldo_automatico(db_operador) -> dict:
    """Genera el respaldo del día para todas las organizaciones.

    `db_operador` debe ser una sesión marcada como operador del sistema
    (get_cron_db): así se listan todas las organizaciones. Cada paquete se
    genera en su propia sesión con el contexto de su organización.
    """
    if not _respaldo_automatico_activado():
        return {"activado": False, "generados": 0, "omitidos": 0, "errores": 0}

    organizaciones = (
        db_operador.query(Organizacion).order_by(Organizacion.id).all()
    )
    resultados = [
        _respaldo_de_organizacion(db_operador, org) for org in organizaciones
    ]
    generados = sum(1 for r in resultados if r["estado"] == "ok")
    omitidos = sum(1 for r in resultados if r["estado"] == "omitido")
    fallidos = [r for r in resultados if r["estado"] == "error"]
    logger.info(
        "Respaldo automático: %d generados, %d omitidos, %d con error "
        "(sobre %d organizaciones).",
        generados, omitidos, len(fallidos), len(resultados),
    )
    return {
        "activado": True,
        "organizaciones": len(resultados),
        "generados": generados,
        "omitidos": omitidos,
        "errores": len(fallidos),
        "detalle": resultados,
    }


# ---------------------------------------------------------------------------
# Verificación diaria con alerta (E4-023)
# ---------------------------------------------------------------------------


def ejecutar_verificacion_diaria() -> dict:
    """Ejecuta /readyz y, si falla, alerta por correo a los operadores.

    Devuelve un resumen JSON seguro (sin secretos): el readiness ya sanea los
    mensajes de error y nunca expone credenciales.
    """
    from ..health import run_readiness
    from ..operadores import operadores_configurados
    from .email import EmailNotConfigured, EmailSendError, enviar_alerta_operador

    estado = run_readiness()
    if estado.ok:
        return {"ok": True, "errores": [], "alertas_enviadas": 0}

    operadores = sorted(operadores_configurados())
    alertas: list[str] = []
    fallos: list[str] = []
    for email in operadores:
        try:
            alertas.append(enviar_alerta_operador(
                email=email, errores=estado.errors, checks=estado.checks
            ))
        except (EmailNotConfigured, EmailSendError) as exc:
            logger.warning("Alerta operativa a %s falló: %s", email, exc)
            fallos.append(email)
    logger.warning(
        "Verificación diaria fallida (%d problema(s)); alertas enviadas: %d%s.",
        len(estado.errors), len(alertas),
        f" (fallaron {len(fallos)})" if fallos else "",
    )
    return {
        "ok": False,
        "errores": list(estado.errors),
        "alertas_enviadas": len(alertas),
        "operadores": len(operadores),
        "alertas_fallidas": len(fallos),
    }
