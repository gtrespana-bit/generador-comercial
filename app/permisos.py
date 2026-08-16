"""Autorización centralizada por rol de membresía (E4-002 / E4-009).

Hasta ahora cada ruta repetía su propio conjunto de roles y su propio mensaje.
Este módulo es la **única fuente de verdad** de qué rol puede hacer qué:

- ``ROLES_ESCRITURA`` — propietario, administrador y miembro pueden modificar
  datos de negocio (el rol ``lectura`` queda fuera).
- ``ROLES_GESTION`` — propietario y administrador gestionan configuración,
  equipo, respaldo y operaciones delicadas.
- ``ROL_PROPIETARIO`` — el propietario es el único que decide la baja de la
  organización.

Las rutas siguen escribiendo sus mensajes (para no romper la UX ni las
pruebas), pero **los conjuntos de roles viven aquí** y se usan con los
predicados ``puede_*`` / ``es_*``. La defensa en profundidad se mantiene por
debajo, sin depender de este módulo:

1. Los eventos SQLAlchemy de ``app.models`` bloquean DML de ``lectura`` y
   asignan la tenencia en cada escritura.
2. ``app.storage`` bloquea efectos externos de ``lectura`` antes de tocar el
   almacenamiento (una credencial server-side podría eludir RLS).
3. En PostgreSQL, RLS aplica las políticas por organización y rol
   independientemente de lo que el código compruebe.
"""
from __future__ import annotations

from .models import PermisoOrganizacionError

#: Roles válidos de membresía, en orden de capacidad.
ROLES_VALIDOS = ("lectura", "miembro", "administrador", "propietario")

#: Pueden modificar datos de negocio (todo salvo ``lectura``).
ROLES_ESCRITURA = frozenset(ROLES_VALIDOS[1:])

#: Gestionan configuración, equipo, respaldo y operaciones delicadas.
ROLES_GESTION = frozenset(ROLES_VALIDOS[2:])

#: Único rol que puede dar de baja la organización.
ROL_PROPIETARIO = "propietario"


def rol_actual(db) -> str:
    """Rol de la sesión activa; cadena vacía si no hay contexto."""
    return str(db.info.get("rol_membresia") or "")


def es_lectura(db) -> bool:
    return rol_actual(db) == "lectura"


def puede_escribir(db) -> bool:
    return rol_actual(db) in ROLES_ESCRITURA


def puede_gestionar(db) -> bool:
    return rol_actual(db) in ROLES_GESTION


def es_propietario(db) -> bool:
    return rol_actual(db) == ROL_PROPIETARIO


# ---------------------------------------------------------------------------
# Versiones que lanzan excepción, para los servicios que prefieren abortar
# en lugar de redirigir. La capa de datos (eventos SQLAlchemy) sigue siendo
# la guardia final: estos helpers existen para fallar pronto y con mensajes
# claros, no para sustituirla.
# ---------------------------------------------------------------------------

def exigir_escritura(db, *, mensaje: str | None = None) -> None:
    """Lanza ``PermisoOrganizacionError`` si el rol no puede escribir."""
    if not puede_escribir(db):
        raise PermisoOrganizacionError(
            mensaje or "Tu rol es de solo lectura y no permite modificar datos."
        )


def exigir_gestion(db, *, mensaje: str | None = None) -> None:
    """Lanza si el rol no es propietario ni administrador."""
    if not puede_gestionar(db):
        raise PermisoOrganizacionError(
            mensaje or "Solo propietarios y administradores pueden realizar esta acción."
        )


def exigir_propietario(db, *, mensaje: str | None = None) -> None:
    """Lanza si el rol no es propietario."""
    if not es_propietario(db):
        raise PermisoOrganizacionError(
            mensaje or "Solo el propietario puede realizar esta acción."
        )
