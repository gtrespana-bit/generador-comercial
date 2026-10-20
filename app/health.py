"""Chequeos de salud para despliegues web (staging/producción).

No exponen secretos ni datos de tenant:

* ``/healthz`` (liveness): el proceso arrancó y sirve tráfico. No toca la
  base de datos ni servicios externos.
* ``/readyz`` (readiness): el despliegue tiene configuración válida de
  Auth/Storage y, en PostgreSQL, se conecta, está en el head de Alembic
  esperado y el login runtime es un miembro no privilegiado de
  ``cotizat_app`` (sin SUPERUSER/BYPASSRLS, con INHERIT).

Un ``503`` aquí significa que el despliegue no debe recibir tráfico real;
un ``200`` no sustituye la matriz de aceptación manual con dos correos y
dos organizaciones, pero detecta rápido regresiones de infraestructura.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .database import (
    DATABASE_IS_SQLITE,
    DATABASE_URL,
    EXPECTED_ALEMBIC_HEAD,
    engine as default_engine,
)
from .ratelimit import estado_configuracion
from .storage import StorageNotConfigured, StorageSettings


@dataclass(frozen=True)
class HealthStatus:
    ok: bool
    checks: dict[str, str]
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "checks": self.checks, "errors": self.errors}


def liveness() -> HealthStatus:
    """El proceso está vivo. No depende de la base de datos."""
    return HealthStatus(ok=True, checks={"status": "alive"})


def _check_auth_configuration() -> tuple[str, str | None]:
    from .auth import AuthNotConfigured, SupabaseAuthSettings

    try:
        SupabaseAuthSettings.from_environment()
        return "configurado", None
    except AuthNotConfigured as exc:
        return "no-configurado", str(exc)


def _check_storage_configuration() -> tuple[str, str | None]:
    # En SQLite local el backend local no requiere variables de Supabase; no
    # se exige la configuración de Storage para dar por vivo un entorno local.
    if DATABASE_IS_SQLITE:
        return "local", None
    try:
        settings = StorageSettings.from_environment()
    except StorageNotConfigured as exc:
        return "no-configurado", str(exc)
    if settings.backend != "supabase":
        return "local", None
    return f"supabase:{settings.bucket}", None


def _check_public_url() -> tuple[str, str | None]:
    from .auth import AuthNotConfigured, public_app_url

    try:
        public_app_url("/")
        return "configurado", None
    except AuthNotConfigured as exc:
        return "no-configurado", str(exc)


def _check_recovery_redirect() -> tuple[str, str | None]:
    """Publica la Redirect URL exacta que Supabase debe tener autorizada.

    Supabase descarta ``redirect_to`` en silencio cuando la URL no está en su
    lista y usa el Site URL: el enlace del email acaba en la pantalla de login
    y parece roto. No se puede consultar esa lista sin credenciales de
    administración, así que readiness expone el valor esperado para poder
    compararlo de un vistazo con Authentication → URL Configuration.
    """
    from .auth import AuthNotConfigured, password_reset_redirect_url

    try:
        return password_reset_redirect_url(), None
    except AuthNotConfigured as exc:
        return "no-configurado", str(exc)


def _check_email_configuration() -> tuple[str, str | None]:
    """Informativo: las invitaciones degradan a enlace en pantalla.

    Sin `RESEND_API_KEY`/`COTIZAT_EMAIL_FROM` el flujo de equipo sigue
    funcionando (muestra el enlace una sola vez), así que este chequeo nunca
    hace fallar el readiness; solo publica el estado para el panel.
    """
    from .services.email import estado_configuracion_email

    return estado_configuracion_email()


def _check_avisos_destino() -> dict[str, str]:
    """Informativo: adónde van los avisos del negocio y de soporte.

    Sin ``COTIZAT_AVISOS_EMAIL`` van a ``soporte@cotizat.online``, que hoy no
    tiene buzón (sin registros MX): el correo «sale» y rebota en silencio.
    Publicado el 2026-10-20, cuando los mensajes de soporte daban error y
    ningún aviso llegó nunca. No se revela la dirección desviada.
    """
    import os

    desviado = bool((os.environ.get("COTIZAT_AVISOS_EMAIL") or "").strip())
    return {
        "avisos_destino": (
            "desviado (COTIZAT_AVISOS_EMAIL)" if desviado else "buzon de soporte por defecto"
        )
    }


def _check_cron_configuration() -> dict[str, str]:
    """Informativo: el trabajo programado de Vercel y su secreto.

    El cron se declara en ``vercel.json`` → ``crons`` y Vercel solo lo crea
    para despliegues de **producción**; cada invocación lleva
    ``Authorization: Bearer $CRON_SECRET``. Este chequeo publica si el
    despliegue actual tiene el secreto y si las rutas declaradas existen en la
    aplicación, para distinguir de un vistazo «el cron no se creó en Vercel»
    (no aparece en el panel) de «el cron falla al ejecutarse» (aparece pero
    responde 401 o 500). Nunca falla el readiness: sin cron la app funciona
    igual, y no expone el valor del secreto.
    """
    import json
    import os
    from pathlib import Path

    from .routers import admin

    secreto = str(os.environ.get("CRON_SECRET", "")).strip()
    estado = {"cron_secret": "configurado" if secreto else "no-configurado"}

    vercel_json = Path(__file__).resolve().parents[1] / "vercel.json"
    try:
        crons = json.loads(vercel_json.read_text(encoding="utf-8")).get("crons", [])
    except Exception:
        crons = []
    rutas_declaradas = [
        cron["path"] for cron in crons if isinstance(cron, dict) and cron.get("path")
    ]
    if not rutas_declaradas:
        estado["cron"] = "sin-crons-en-vercel.json"
        return estado
    resumen = []
    for ruta in rutas_declaradas:
        registrada = any(
            getattr(r, "path", None) == ruta for r in admin.router.routes
        )
        resumen.append(f"{ruta}:{'registrada' if registrada else 'NO-registrada'}")
    estado["cron"] = "; ".join(resumen)
    return estado


def _check_postgresql(engine: Engine) -> dict[str, object]:
    """Comprueba conexión, head de Alembic y el rol runtime limitado."""
    results: dict[str, object] = {"database": "postgresql"}
    errors: list[str] = []
    require_rls = True
    try:
        from .db_config import resolver_database_settings  # noqa: F401
        import os

        flag = os.environ.get("COTIZAT_REQUIRE_RLS_ROLE", "true").strip().lower()
        require_rls = flag not in {"0", "false", "no", "off"}
    except Exception:
        require_rls = True

    try:
        with engine.connect() as connection:
            version = connection.execute(
                text("SELECT version_num FROM public.alembic_version")
            ).scalar_one_or_none()
        if version == EXPECTED_ALEMBIC_HEAD:
            results["alembic"] = f"head:{EXPECTED_ALEMBIC_HEAD}"
        else:
            results["alembic"] = f"inesperado:{version or 'sin-version'}"
            errors.append(
                f"Esquema en {version or 'sin versión'}; se espera {EXPECTED_ALEMBIC_HEAD}."
            )
    except Exception as exc:  # pragma: no cover - depende de red/infra
        results["alembic"] = "error"
        errors.append(f"No se pudo comprobar Alembic: {_safe_error(exc)}")

    if require_rls:
        try:
            with engine.connect() as connection:
                row = connection.execute(text("""
                    SELECT r.rolname, r.rolsuper, r.rolbypassrls, r.rolinherit,
                           COALESCE(
                             pg_has_role(r.oid, app_role.oid, 'member'), FALSE
                           ) AS app_member
                    FROM pg_catalog.pg_roles AS r
                    LEFT JOIN pg_catalog.pg_roles AS app_role
                      ON app_role.rolname = 'cotizat_app'
                    WHERE r.rolname = current_user
                """)).mappings().one()
            role_bits = (
                f"superuser={row['rolsuper']}, bypassrls={row['rolbypassrls']}, "
                f"inherit={row['rolinherit']}, cotizat_app={row['app_member']}"
            )
            results["rol_runtime"] = role_bits
            if row["rolsuper"] or row["rolbypassrls"] or not row["rolinherit"]:
                errors.append(
                    "El rol runtime es privilegiado: debe ser NOSUPERUSER, "
                    "NOBYPASSRLS y con INHERIT."
                )
            if not row["app_member"]:
                errors.append(
                    "El rol runtime no es miembro de cotizat_app."
                )
        except Exception as exc:  # pragma: no cover - depende de red/infra
            results["rol_runtime"] = "error"
            errors.append(f"No se pudo verificar el rol runtime: {_safe_error(exc)}")
    else:
        results["rol_runtime"] = "verificacion-desactivada"

    results["errors"] = errors
    return results


#: Alarma blanda de frescura de precios: el titular fijó una cadencia
#: mensual de actualización de matrices (Fase 2, 2026-10-20); con el
#: colchón, /readyz avisa cuando la carga más antigua por país supera este
#: umbral. El proceso completo vive en docs/ACTUALIZACION_PRECIOS.md; si la
#: cadencia cambia, se cambia aquí y allí.
_UMBRAL_FRESCURA_PRECIOS_DIAS = 40


def _como_fecha(valor) -> date | None:
    """Normaliza una fecha leída de la BD (datetime, date o texto ISO)."""
    from datetime import date, datetime

    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _texto_frescura_precios(
    ultima_por_pais: dict,
    hoy: date,
    umbral_dias: int = _UMBRAL_FRESCURA_PRECIOS_DIAS,
) -> str:
    """Frase de /readyz sobre cuándo se cargaron los precios nacionales.

    ``guardar_precio`` sella ``fecha_actualizacion`` en cada carga,
    incluidas las filas sin cambios, así que el máximo por país delata la
    última vez que su matriz pasó por el importador: tras una actualización
    completa la frase pasa a «hoy» sin necesitar una tabla de constancias.
    Es una alarma blanda: si el país más atrasado supera la cadencia, la
    frase lo dice, pero el readiness no se tumba por ello.
    """
    try:
        fechas: dict[str, date] = {}
        for pais, valor in ultima_por_pais.items():
            fecha = _como_fecha(valor)
            if fecha is not None:
                fechas[str(pais)] = fecha
        if not fechas:
            return "sin fechas de carga registradas"
        ultima = max(fechas.values())
        dias_ultima = (hoy - ultima).days
        if dias_ultima <= 0:
            texto = f"hoy ({ultima.isoformat()})"
        else:
            texto = (
                f"hace {dias_ultima} {'día' if dias_ultima == 1 else 'días'}"
                f" ({ultima.isoformat()})"
            )
        pais_atrasado, fecha_atrasada = min(fechas.items(), key=lambda par: par[1])
        dias_atrasado = (hoy - fecha_atrasada).days
        if dias_atrasado > umbral_dias:
            texto += (
                f"; REVISAR: {pais_atrasado} hace {dias_atrasado} días"
                f" (cadencia mensual, umbral {umbral_dias})"
            )
        return texto
    except Exception:
        return "no evaluado"


def _check_seo(engine: Engine | None, host: str | None) -> dict[str, str]:
    """Estado SEO del DESPLIEGUE, informativo: nunca tumba el readiness.

    Cubre lo que una revisión externa sin cabeceras no puede certificar:
    que el corpus de artículos y el sitemap del código desplegado estén
    completos, que los artefactos de precios viajen dentro de la función
    (sin el CSV las guías de mano de obra salen con la tabla vacía) y que
    la petición haya llegado por el host canónico. Esto último delata el
    20/10/2026 el conflicto apex↔www: Vercel servía ``www`` mientras
    canónicas, sitemap y robots declaraban el apex.
    """
    checks: dict[str, str] = {}
    try:
        from urllib.parse import urlparse

        from .seo import origen_canonico, urls_sitemap
        from .seo_articulos import lista_articulos
        from .seo_latam import _base_venezuela, _matriz

        canonico = origen_canonico(None)
        checks["dominio_canonico"] = canonico
        host_canonico = urlparse(canonico).hostname or ""
        if host:
            checks["host_recibido"] = host
            checks["host_es_canonico"] = (
                "si"
                if host.lower() == host_canonico.lower()
                else "no: el borde debe redirigir a " + (host_canonico or canonico)
            )
        else:
            checks["host_es_canonico"] = "no evaluado (sin peticion)"
        checks["seo_sitemap_urls"] = str(len(urls_sitemap(None)))
        checks["seo_articulos_es"] = str(len(lista_articulos()))
        matriz = _matriz()
        checks["seo_matriz_latam"] = (
            f"{len(matriz)} paises con filas" if matriz else "CSV ausente o vacio en el despliegue"
        )
        checks["seo_base_venezuela"] = (
            f"{len(_base_venezuela())} oficios" if _base_venezuela() else "recursos.json ausente o vacio"
        )
    except Exception as exc:  # diagnóstico, no condición de salud
        checks["seo"] = f"no evaluado: {_safe_error(exc)}"
        return checks
    # Referencias nacionales cargadas en la base (no los overrides de
    # empresa). Una sola agregación; si la tabla no existe aún, se informa.
    try:
        from datetime import date

        motor = engine or default_engine
        with motor.connect() as conn:
            filas = conn.execute(
                text(
                    "SELECT pais_codigo, COUNT(*), MAX(fecha_actualizacion) "
                    "FROM precios_recursos_mercado "
                    f"WHERE organizacion_id IS NULL AND {_condicion_activo(conn.dialect.name)} "
                    "AND codigo_recurso <> '' GROUP BY pais_codigo ORDER BY pais_codigo"
                )
            ).fetchall()
        total = sum(int(f[1]) for f in filas)
        checks["precios_bd"] = f"{total} referencias nacionales en {len(filas)} paises"
        checks["precios_bd_paises"] = ",".join(str(f[0]) for f in filas) or "ninguno"
        # Frescura (Fase 2): la misma agregación trae la última carga de
        # cada matriz; la frase pasa a «hoy» tras una actualización.
        checks["precios_actualizados"] = _texto_frescura_precios(
            {str(f[0]): f[2] for f in filas}, date.today()
        )
    except Exception as exc:
        checks["precios_bd"] = f"no evaluado: {_safe_error(exc)}"
        checks["precios_actualizados"] = "no evaluado"
    return checks


def _condicion_activo(dialecto: str | None = None) -> str:
    """Condición SQL de «activo» para el motor en uso.

    ``activo`` es 1/0 en SQLite y boolean en PostgreSQL. La condición
    «portable» ``activo = 1 OR activo IS TRUE`` no lo es: Postgres la
    rechaza al analizarla (``boolean = integer`` no existe) y el 20/10/2026
    dejó ``precios_bd`` en «no evaluado» en producción. Hay que elegir.

    Manda el dialecto de la conexión que va a ejecutar la sentencia, no el
    motor global del proceso: la batería PostgreSQL (fase 0.1) demostró que
    decidir por el global miente en cuanto conviven dos motores en el mismo
    proceso. Sin argumento se mantiene el comportamiento histórico.
    """
    if dialecto is not None:
        return "activo = 1" if dialecto == "sqlite" else "activo IS TRUE"
    return "activo = 1" if DATABASE_IS_SQLITE else "activo IS TRUE"


def _check_sqlite() -> dict[str, object]:
    return {"database": "sqlite-local", "alembic": "no-aplica", "rol_runtime": "no-aplica"}


def _safe_error(exc: Exception) -> str:
    """No incluye la URL de conexión (podría llevar credenciales)."""
    text = str(exc)
    if "://" in text and "@" in text:
        text = text.split("@", 1)[-1]
    return text[:200] or exc.__class__.__name__


def readiness(engine: Engine | None = None, host: str | None = None) -> HealthStatus:
    """Configuración y dependencias listas para servir tráfico real.

    ``host`` es el Host de la petición a /readyz cuando lo hay: permite
    contrastarlo con el dominio canónico sin acceder al panel de Vercel.
    """
    checks: dict[str, str] = {}
    errors: list[str] = []

    # Informativo: el entorno detectado (E4-003). No falla por sí mismo; la
    # validación por entorno vive en ``app.config.validar`` y se expone en el
    # panel del operador. Los chequeos de Auth/Storage/URL siguen siendo los
    # que convierten una falta real en un 503.
    from .config import entorno_actual

    checks["entorno"] = entorno_actual().etiqueta

    auth_state, auth_error = _check_auth_configuration()
    checks["auth"] = auth_state
    if auth_error:
        errors.append(f"Auth: {auth_error}")

    storage_state, storage_error = _check_storage_configuration()
    checks["storage"] = storage_state
    if storage_error:
        errors.append(f"Storage: {storage_error}")

    url_state, url_error = _check_public_url()
    checks["public_url"] = url_state
    if url_error:
        errors.append(f"URL pública: {url_error}")

    # Informativo: no falla el readiness, porque la lista de Redirect URLs
    # vive en Supabase y no puede comprobarse desde aquí.
    redirect_state, _redirect_error = _check_recovery_redirect()
    checks["recovery_redirect_url_esperada"] = redirect_state

    # Informativo: sin correo configurado las invitaciones se entregan como
    # enlace en pantalla, así que nunca añade errores al readiness.
    email_state, _email_error = _check_email_configuration()
    checks["email"] = email_state

    # Informativo: sin Stripe el cobro manual sigue funcionando.
    from .services.stripe import estado_configuracion_stripe

    stripe_state, _stripe_error = estado_configuracion_stripe()
    checks["stripe"] = stripe_state

    # Informativo: el cron de Vercel depende de `CRON_SECRET` y de que el
    # despliegue de producción contenga el vercel.json con `crons`. Sin cron
    # la aplicación funciona igual, así que nunca añade errores al readiness.
    checks.update(_check_cron_configuration())

    # En SQLite local (escritorio) un contador por proceso es correcto: hay un
    # único proceso. Solo se informa/exige el compartido en despliegue web.
    ratelimit_state, ratelimit_error = estado_configuracion()
    checks["rate_limit"] = ratelimit_state
    if ratelimit_error and not DATABASE_IS_SQLITE:
        errors.append(f"Rate limit: {ratelimit_error}")

    # Informativo: exigir licencia es una decisión de negocio del despliegue,
    # no una condición de salud; con ella apagada la app funciona igual.
    from .services.licencias import exigencia_licencia_activada

    if DATABASE_IS_SQLITE:
        checks["licencias"] = "no-aplica (escritorio)"
    else:
        checks["licencias"] = (
            "exigida" if exigencia_licencia_activada() else "no-exigida"
        )

    if DATABASE_IS_SQLITE:
        checks.update({k: str(v) for k, v in _check_sqlite().items()})
    else:
        db_results = _check_postgresql(engine or default_engine)
        db_errors = db_results.pop("errors", [])
        checks.update({k: str(v) for k, v in db_results.items()})
        errors.extend(db_errors)  # type: ignore[arg-type]

    # Informativo (nunca añade errores): corpus SEO, artefactos de precios
    # dentro de la función, referencias nacionales en BD y host canónico.
    checks.update(_check_seo(engine, host))

    # Informativo: destino de los avisos internos (sin revelar la dirección).
    checks.update(_check_avisos_destino())

    return HealthStatus(ok=not errors, checks=checks, errors=errors)


# Permite inyectar un chequeo alternativo en tests sin reabrir conexiones.
_readiness_override: Callable[[], HealthStatus] | None = None


def set_readiness_override(fn: Callable[[], HealthStatus] | None) -> None:
    """Sustituye el readiness (útil para pruebas o mantenimiento)."""
    global _readiness_override
    _readiness_override = fn


def run_readiness(host: str | None = None) -> HealthStatus:
    if _readiness_override is not None:
        return _readiness_override()
    return readiness(host=host)
