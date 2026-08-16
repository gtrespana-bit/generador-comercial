"""Baja de una organización con borrado verificado (E3-023).

Regla de honestidad: una acción irreversible exige la identidad del
propietario escrita a mano y una casilla explícita. La ruta valida ambas antes
de invocar este módulo, y este módulo las vuelve a validar (defensa en
profundidad) antes de borrar nada.

Orden del borrado, para no dejar residuos ni huérfanos:

1. **Archivos primero.** Las claves se recogen de ``archivos_almacenados`` y
   cada objeto se elimina del almacenamiento privado (local o Supabase) ANTES
   de tocar la base: una vez borrados los metadatos no habría forma de
   reintentar. Si algún objeto falla, la baja se aborta entera y no se borra
   nada en la base (reintentar es seguro).
2. **Datos y organización.** En PostgreSQL se invoca
   ``cotizat_security.baja_organizacion`` (SECURITY DEFINER, revisión
   ``a3d7e9c1b5f2``): borra en una sola transacción todas las tablas de
   negocio, licencias, membresías y la propia organización, con guardias del
   claim de sesión y del rol de propietario. En SQLite el mismo orden se
   ejecuta por ORM dentro de la sesión autenticada.

Lo que NO se borra (y por qué):

- **La cuenta de usuario (Supabase Auth):** la identidad de acceso no depende
  de la organización; sin membresías el usuario queda sin organizaciones y
  puede crear una nueva. El borrado de identidades de Auth es ajeno a la app.
- **Los registros operativos del titular fuera de CotizaT:** la licencia y su
  cobro desaparecen de la base (no hay contrato sin organización), pero el
  operador conserva su propia contabilidad externa, como corresponde.

Sin período de gracia por decisión de diseño: la baja es inmediata y
verificada; la pantalla ofrece descargar la exportación (E3-022) antes de
confirmar y exige escribir el nombre exacto de la organización.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import DATABASE_IS_SQLITE
from ..models import (
    AnexoPresupuesto,
    ArchivoAlmacenado,
    BorradorPresupuesto,
    CambioAlcance,
    CambioAlcanceItem,
    Capitulo,
    CategoriaPartida,
    Cliente,
    Configuracion,
    DescomposicionFila,
    DescomposicionPartida,
    EnlacePropuesta,
    Factura,
    FacturaCapitulo,
    FacturaItem,
    InvitacionOrganizacion,
    Licencia,
    Medicion,
    Membresia,
    NotaSeguimiento,
    Organizacion,
    Pago,
    Partida,
    PermisoOrganizacionError,
    Plantilla,
    Presupuesto,
    PresupuestoItem,
    PresupuestoItemProducto,
    PresupuestoVersion,
    Producto,
    Proyecto,
    RecetaEstancia,
    Recurso,
)
from ..storage import get_storage_backend


class BajaError(ValueError):
    """La baja no se puede ejecutar de forma segura (nada queda borrado)."""


#: Orden hijo → padre para respetar las claves foráneas al borrar por ORM.
#: Solo tablas TenantMixin (el filtro de organización se aplica solo a ellas);
#: licencias y membresías se borran aparte con filtro explícito.
_ORDEN_BORRADO: tuple[Any, ...] = (
    EnlacePropuesta,
    Pago,
    CambioAlcanceItem,
    CambioAlcance,
    Proyecto,
    NotaSeguimiento,
    AnexoPresupuesto,
    BorradorPresupuesto,
    PresupuestoVersion,
    DescomposicionFila,
    DescomposicionPartida,
    Medicion,
    PresupuestoItemProducto,
    PresupuestoItem,
    Capitulo,
    Presupuesto,
    FacturaItem,
    FacturaCapitulo,
    Factura,
    Cliente,
    Partida,
    Producto,
    Recurso,
    Plantilla,
    RecetaEstancia,
    CategoriaPartida,
    ArchivoAlmacenado,
    InvitacionOrganizacion,
    Configuracion,
)


def resumen_baja(db: Session) -> dict[str, Any]:
    """Qué se borraría: nombre de la organización y conteos por tabla."""
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise BajaError("La organización no existe.")
    conteos: dict[str, int] = {}
    for modelo in _ORDEN_BORRADO:
        conteos[modelo.__tablename__] = db.query(modelo).count()
    conteos["licencias"] = (
        db.query(Licencia)
        .filter(Licencia.organizacion_id == organizacion_id)
        .count()
    )
    conteos["membresias"] = (
        db.query(Membresia)
        .filter(Membresia.organizacion_id == organizacion_id)
        .count()
    )
    return {
        "nombre": organizacion.nombre,
        "conteos": conteos,
        "archivos": conteos["archivos_almacenados"],
    }


def _borrar_organizacion_sqlite(db: Session, organizacion_id: int) -> None:
    """Mismo borrado que la función PostgreSQL, por ORM con filtro de tenant."""
    for modelo in _ORDEN_BORRADO:
        db.query(modelo).delete(synchronize_session=False)
    # Sin TenantMixin: filtros explícitos para no tocar otras organizaciones.
    db.query(Licencia).filter(Licencia.organizacion_id == organizacion_id).delete(
        synchronize_session=False
    )
    db.query(Membresia).filter(Membresia.organizacion_id == organizacion_id).delete(
        synchronize_session=False
    )
    db.query(Organizacion).filter(Organizacion.id == organizacion_id).delete(
        synchronize_session=False
    )


def ejecutar_baja(
    db: Session,
    *,
    nombre_confirmado: str,
    confirmar: bool,
) -> str:
    """Ejecuta la baja completa y verificada; devuelve el nombre borrado.

    El ``commit`` lo hace la ruta llamante; ante cualquier error la ruta hace
    ``rollback`` y no queda nada a medias.
    """
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    if organizacion_id <= 0:
        raise BajaError("No hay una organización activa.")
    if db.info.get("rol_membresia") != "propietario":
        raise PermisoOrganizacionError(
            "Solo el propietario puede dar de baja la organización."
        )
    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise BajaError("La organización no existe.")
    nombre = str(organizacion.nombre or "")
    if str(nombre_confirmado or "").strip() != nombre.strip():
        raise BajaError(
            "El nombre escrito no coincide con el de la organización; no se borró nada."
        )
    if not confirmar:
        raise BajaError(
            "Marca la casilla de confirmación para dar de baja la organización."
        )

    # 1) Archivos primero: sin metadatos no habría reintento después.
    claves = [fila.object_key for fila in db.query(ArchivoAlmacenado).all()]
    backend = get_storage_backend()
    fallos: list[str] = []
    for clave in claves:
        try:
            backend.delete(clave)
        except Exception:  # StorageError o red: se declara y se aborta entero
            fallos.append(clave)
    if fallos:
        raise BajaError(
            f"No se pudieron borrar {len(fallos)} archivo(s) del almacenamiento "
            "privado; no se ha borrado nada. Inténtalo de nuevo."
        )

    # 2) Datos y organización en una sola transacción.
    if DATABASE_IS_SQLITE:
        _borrar_organizacion_sqlite(db, organizacion_id)
    else:
        try:
            db.execute(
                text("SELECT cotizat_security.baja_organizacion(:organizacion_id)"),
                {"organizacion_id": organizacion_id},
            )
        except Exception as exc:
            # Incluye las guardias SQL de la función (claim y rol de propietario).
            raise BajaError(
                "La base de datos rechazó la baja; no se borró nada. "
                "Verifica que eres el propietario de esta organización."
            ) from exc
    db.commit()
    return nombre
