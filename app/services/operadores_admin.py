"""Gestión del equipo de operadores del producto (A1).

Este servicio vive exclusivamente detrás de ``get_operator_db``: nunca debe
importarse desde una ruta de tenant. Las operaciones de escritura exigen el
rol ``superadmin`` (decidido por el claim de la sesión, no por un parámetro
de formulario).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc

from ..models import OperadorProducto, ROLES_OPERADOR
from ..operadores import operadores_configurados


class GestionEquipoError(RuntimeError):
    """Error de negocio al gestionar operadores."""


#: No se puede suspender ni rebajar al último superadmin: el panel podría
#: quedarse sin nadie capaz de nombrar a un reemplazo.
def exigir_superadmin(db) -> None:
    rol = str(db.info.get("operador_rol") or "").strip().lower()
    if rol != "superadmin":
        raise GestionEquipoError(
            "Solo un superadmin puede gestionar el equipo de operadores."
        )


def listar_operadores(db) -> list[dict]:
    """Lista los operadores de la tabla y fusiona los que solo viven en env.

    La semilla ``COTIZAT_OPERADORES`` aparece siempre (es quien tiene el panel
    abierto), con rol ``superadmin`` salvo que la tabla la haya rebajado.
    """
    filas = db.query(OperadorProducto).order_by(
        desc(OperadorProducto.activo),
        OperadorProducto.email,
    ).all()
    por_email = {f.email: f for f in filas}

    resultado = []
    vistos = set()
    for fila in filas:
        resultado.append({
            "id": fila.id,
            "email": fila.email,
            "rol": fila.rol,
            "rol_label": fila.etiqueta_rol,
            "activo": bool(fila.activo),
            "notas": fila.notas or "",
            "creado_por_email": fila.creado_por_email or "",
            "created_at": fila.created_at,
            "updated_at": fila.updated_at,
            "origen": "tabla",
        })
        vistos.add(fila.email)

    for email in sorted(operadores_configurados()):
        if email in vistos:
            continue
        resultado.append({
            "id": None,
            "email": email,
            "rol": "superadmin",
            "rol_label": "Superadmin",
            "activo": True,
            "notas": "Sembrado desde COTIZAT_OPERADORES.",
            "creado_por_email": "entorno",
            "created_at": None,
            "updated_at": None,
            "origen": "env",
        })
    return resultado


def _rol_valido(rol: str) -> str:
    rol_n = (rol or "").strip().lower()
    if rol_n not in ROLES_OPERADOR:
        raise GestionEquipoError("El rol indicado no es válido.")
    return rol_n


def _email_normalizado(email: str) -> str:
    email_n = (email or "").strip().lower()
    if (
        not email_n
        or "@" not in email_n
        or email_n.split("@")[0] == ""
        or email_n.split("@")[-1] == ""
    ):
        raise GestionEquipoError("Escribe un correo válido.")
    return email_n[:254]


def crear_operador(
    db,
    *,
    email: str,
    rol: str,
    operador_email: str = "",
    notas: str = "",
) -> OperadorProducto:
    """Alta de un operador en ``operadores_producto``.

    El correo puede coincidir con uno ya sembrado por ``COTIZAT_OPERADORES``:
    la fila solo permite rebajarlo/desactivarlo y registrar quién lo hizo.
    """
    email_n = _email_normalizado(email)
    rol_n = _rol_valido(rol)
    existente = db.query(OperadorProducto).filter(
        OperadorProducto.email == email_n
    ).first()
    if existente is not None:
        raise GestionEquipoError("Ese correo ya está en el equipo.")
    operador = OperadorProducto(
        email=email_n,
        rol=rol_n,
        activo=True,
        notas=(notas or "")[:500],
        creado_por_email=(operador_email or "").lower()[:254],
    )
    db.add(operador)
    db.flush()
    return operador


def cambiar_rol_operador(
    db,
    operador_id: int,
    *,
    rol: str,
    operador_email: str = "",
) -> OperadorProducto:
    rol_n = _rol_valido(rol)
    operador = db.get(OperadorProducto, int(operador_id))
    if operador is None:
        raise GestionEquipoError("El operador indicado no existe.")
    # Evitar quedarse sin superadmin activo.
    if (
        operador.rol == "superadmin"
        and operador.activo
        and rol_n != "superadmin"
        and _superadmins_activos(db, excluir_id=operador.id) == 0
    ):
        raise GestionEquipoError(
            "No se puede rebajar al último superadmin activo."
        )
    operador.rol = rol_n
    operador.updated_at = datetime.utcnow()
    if operador_email:
        operador.creado_por_email = operador_email.lower()[:254]
    db.flush()
    return operador


def suspender_operador(db, operador_id: int, *, operador_email: str = "") -> OperadorProducto:
    operador = db.get(OperadorProducto, int(operador_id))
    if operador is None:
        raise GestionEquipoError("El operador indicado no existe.")
    if (
        operador.rol == "superadmin"
        and operador.activo
        and _superadmins_activos(db, excluir_id=operador.id) == 0
    ):
        raise GestionEquipoError(
            "No se puede suspender al último superadmin activo."
        )
    operador.activo = False
    operador.updated_at = datetime.utcnow()
    if operador_email:
        operador.creado_por_email = operador_email.lower()[:254]
    db.flush()
    return operador


def activar_operador(db, operador_id: int, *, operador_email: str = "") -> OperadorProducto:
    operador = db.get(OperadorProducto, int(operador_id))
    if operador is None:
        raise GestionEquipoError("El operador indicado no existe.")
    operador.activo = True
    operador.updated_at = datetime.utcnow()
    if operador_email:
        operador.creado_por_email = operador_email.lower()[:254]
    db.flush()
    return operador


def _superadmins_activos(db, *, excluir_id: int | None = None) -> int:
    consulta = db.query(OperadorProducto).filter(
        OperadorProducto.rol == "superadmin",
        OperadorProducto.activo.is_(True),
    )
    if excluir_id:
        consulta = consulta.filter(OperadorProducto.id != int(excluir_id))
    return consulta.count()
