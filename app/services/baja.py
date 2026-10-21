"""Baja de una organización con borrado verificado (E3-023).

Regla de honestidad: una acción irreversible exige la identidad del
propietario escrita a mano y una casilla explícita. La ruta valida ambas antes
de invocar este módulo, y este módulo las vuelve a validar (defensa en
profundidad) antes de borrar nada.

Orden del borrado, para no dejar residuos ni huérfanos:

1. **Suscripción de Stripe.** Si la organización paga con tarjeta, su(s)
   suscripción(es) se cancelan DE INMEDIATO en Stripe antes de tocar nada:
   borrar la organización sin cancelar dejaría el cobro cobrando para
   siempre, sin forma de pararlo desde la app (la compra local que guarda
   el id desaparecería). Si Stripe rechaza la cancelación —o no está
   configurado y hay suscripción— la baja se aborta entera sin borrar
   nada. Cancelar no corta el acceso ya pagado (manda la licencia local),
   así que si un paso posterior aborta, la organización sigue intacta y
   operativa; solo deja de renovar.
2. **Archivos.** Las claves se recogen de ``archivos_almacenados`` y
   cada objeto se elimina del almacenamiento privado (local o Supabase) ANTES
   de tocar la base: una vez borrados los metadatos no habría forma de
   reintentar. Si algún objeto falla, la baja se aborta entera y no se borra
   nada en la base (reintentar es seguro).
3. **Datos y organización.** En PostgreSQL se invoca
   ``cotizat_security.baja_organizacion`` (SECURITY DEFINER, actualizada por
   ``g7c8d9e0f1a2``): borra en una sola transacción todas las tablas de
   negocio, conversaciones del asistente, licencias, membresías y la propia
   organización, con guardias del
   claim de sesión y del rol de propietario. En SQLite el mismo orden se
   ejecuta por ORM dentro de la sesión autenticada.

Lo que NO se borra (y por qué):

- **La cuenta de usuario (Supabase Auth):** la identidad de acceso no depende
  de la organización; sin membresías el usuario queda sin organizaciones y
  puede crear una nueva. El borrado de identidades de Auth es ajeno a la app.
- **La contabilidad externa del titular:** la licencia y su compra
  desaparecen de la base (no hay contrato sin organización) y la
  suscripción de tarjeta se cancela en Stripe (paso 1), pero el operador
  conserva su propia contabilidad externa —facturas ya emitidas y
  registros fiscales—, como corresponde.

Sin período de gracia por decisión de diseño: la baja es inmediata y
verificada; la pantalla ofrece descargar la exportación (E3-022) antes de
confirmar y exige escribir el nombre exacto de la organización.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import DATABASE_IS_SQLITE
from ..datos_pago import METODO_STRIPE
from ..models import (
    AnexoPresupuesto,
    ArchivoAlmacenado,
    BorradorPresupuesto,
    CambioAlcance,
    CambioAlcanceItem,
    Capitulo,
    CategoriaPartida,
    Cliente,
    CompraPlan,
    Configuracion,
    ConversacionIA,
    MensajeIA,
    DescomposicionFila,
    DescomposicionPartida,
    EnlacePropuesta,
    EventoAuditoria,
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
from ..permisos import es_propietario
from ..storage import get_storage_backend
from .stripe import (
    StripeError,
    StripeNotConfigured,
    cancelar_suscripcion,
    stripe_configurado,
)


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
    # Las respuestas del asistente son datos tenant y deben desaparecer junto
    # con la organización, antes de que se elimine su agregado padre.
    MensajeIA,
    ConversacionIA,
    #: Añadida el 19/08/2026: faltaba desde su creación (e5f2a8d31b6c) y su
    #: FK RESTRICT impedía la baja de cualquier organización con compras.
    CompraPlan,
)


def _suscripciones_stripe(db: Session, organizacion_id: int) -> list[str]:
    """Ids de suscripción de Stripe de la organización, sin repetir.

    Cada renovación clona el mismo id de suscripción en una compra nueva:
    hay que cancelarlo una sola vez. No se filtra por estado de la compra:
    cualquier id presente en las compras debe dejar de cobrar, y cancelar
    una suscripción ya cancelada es un no-op en ``cancelar_suscripcion``.
    """
    filas = (
        db.query(CompraPlan.stripe_subscription_id)
        .filter(
            CompraPlan.organizacion_id == organizacion_id,
            CompraPlan.metodo_pago == METODO_STRIPE,
        )
        .all()
    )
    return sorted(
        {str(fila[0]).strip() for fila in filas if str(fila[0] or "").strip()}
    )


def _cancelar_suscripciones_stripe(db: Session, organizacion_id: int) -> None:
    """Cancela en Stripe las suscripciones de la organización, o aborta.

    Es el paso 1 de la baja: si la pasarela rechaza la cancelación (o no
    está configurada y hay suscripción que cancelar), la baja se aborta
    SIN tocar archivos ni base.
    """
    suscripciones = _suscripciones_stripe(db, organizacion_id)
    if not suscripciones:
        return
    if not stripe_configurado():
        raise BajaError(
            "Esta organización paga con tarjeta (Stripe) y el cobro no está "
            "configurado en el servidor: no se puede garantizar que la "
            "suscripción deje de cobrar. No se ha borrado nada; escribe a "
            "soporte para completar la baja."
        )
    for subscription_id in suscripciones:
        try:
            cancelar_suscripcion(subscription_id)
        except (StripeError, StripeNotConfigured) as exc:
            raise BajaError(
                "Stripe no aceptó cancelar la suscripción; no se ha borrado "
                "nada. Inténtalo de nuevo o escribe a soporte."
            ) from exc


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
        # La pantalla avisa de que la suscripción con tarjeta se cancelará
        # de inmediato en Stripe antes de borrar nada.
        "suscripciones_stripe": len(
            _suscripciones_stripe(db, organizacion_id)
        ),
    }


def _borrar_organizacion_sqlite(db: Session, organizacion_id: int) -> None:
    """Mismo borrado que la función PostgreSQL, por ORM con filtro de tenant."""
    for modelo in _ORDEN_BORRADO:
        db.query(modelo).delete(synchronize_session=False)
    # Sin TenantMixin: filtros explícitos para no tocar otras organizaciones.
    db.query(EventoAuditoria).filter(
        EventoAuditoria.organizacion_id == organizacion_id
    ).delete(synchronize_session=False)
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
    if not es_propietario(db):
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

    # 1) Stripe antes que los archivos: si la pasarela rechaza la
    # cancelación, la baja se aborta sin tocar nada.
    _cancelar_suscripciones_stripe(db, organizacion_id)

    # 2) Archivos: sin metadatos no habría reintento después.
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

    # 3) Datos y organización en una sola transacción.
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
