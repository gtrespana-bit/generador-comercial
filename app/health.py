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


def _check_sqlite() -> dict[str, object]:
    return {"database": "sqlite-local", "alembic": "no-aplica", "rol_runtime": "no-aplica"}


def _safe_error(exc: Exception) -> str:
    """No incluye la URL de conexión (podría llevar credenciales)."""
    text = str(exc)
    if "://" in text and "@" in text:
        text = text.split("@", 1)[-1]
    return text[:200] or exc.__class__.__name__


def readiness(engine: Engine | None = None) -> HealthStatus:
    """Configuración y dependencias listas para servir tráfico real."""
    checks: dict[str, str] = {}
    errors: list[str] = []

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

    # En SQLite local (escritorio) un contador por proceso es correcto: hay un
    # único proceso. Solo se informa/exige el compartido en despliegue web.
    ratelimit_state, ratelimit_error = estado_configuracion()
    checks["rate_limit"] = ratelimit_state
    if ratelimit_error and not DATABASE_IS_SQLITE:
        errors.append(f"Rate limit: {ratelimit_error}")

    if DATABASE_IS_SQLITE:
        checks.update({k: str(v) for k, v in _check_sqlite().items()})
    else:
        db_results = _check_postgresql(engine or default_engine)
        db_errors = db_results.pop("errors", [])
        checks.update({k: str(v) for k, v in db_results.items()})
        errors.extend(db_errors)  # type: ignore[arg-type]

    return HealthStatus(ok=not errors, checks=checks, errors=errors)


# Permite inyectar un chequeo alternativo en tests sin reabrir conexiones.
_readiness_override: Callable[[], HealthStatus] | None = None


def set_readiness_override(fn: Callable[[], HealthStatus] | None) -> None:
    """Sustituye el readiness (útil para pruebas o mantenimiento)."""
    global _readiness_override
    _readiness_override = fn


def run_readiness() -> HealthStatus:
    if _readiness_override is not None:
        return _readiness_override()
    return readiness()
