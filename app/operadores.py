"""Operadores del producto: quién puede administrar el negocio (E1-060 v2).

Un **operador** es quien explota CotizaT como negocio. No es un rol de
organización: los roles `propietario`, `administrador`, `miembro` y `lectura`
describen permisos *dentro* de la empresa de un cliente, mientras que el
operador actúa *sobre* las cuentas de clientes.

Semilla y escalado
------------------
- ``COTIZAT_OPERADORES`` sigue siendo la **semilla inicial** y la primera
  barrera: sin ella no hay ningún operador y el panel queda cerrado. Un
  despliegue recién creado no tiene administrador hasta que alguien lo declare
  explícitamente en Vercel.
- A partir de esa semilla, el panel puede añadir operadores con rol en
  ``operadores_producto``. La tabla NO es un reemplazo de la variable: es un
  escalado controlado por una sesión que ya es operador.

Defensa en profundidad
----------------------
1. Variable de entorno: independiente del código y de la base.
2. Tabla `operadores_producto`: en PostgreSQL está protegida con RLS que exige
   la marca de operador (``cotizat.es_operador``) y, para escribir, el rol
   ``superadmin`` (``cotizat.operador_rol``). Una sesión de cliente no ve ni
   una fila; un operador no-superadmin tampoco puede nombrar a nadie.
3. RLS de ``licencias``: sigue exigiendo ``cotizat.es_operador``, sin importar
   qué código llame.

La decisión de pertenencia se toma en ``_establecer_contexto_identidad``
(``app/database.py``), nunca a partir de datos de la petición: cualquier
fallo de autorización no puede concederse la marca por su cuenta.
"""
from __future__ import annotations

import os

from .models import OperadorProducto, ROLES_OPERADOR, ROLES_OPERADOR_ETIQUETA

#: Roles disponibles para el equipo de operación.
#: (Re-exportados desde ``app/models.py`` para que el router y las plantillas
#: usen el mismo origen de verdad.)
ROLES_OPERADOR = ROLES_OPERADOR
ROLES_OPERADOR_ETIQUETA = ROLES_OPERADOR_ETIQUETA


#: Rol por omisión para un operador que solo vive en ``COTIZAT_OPERADORES``.
#: Quien gestiona el producto desde el entorno es el dueño: superadmin.
ROL_OPERADOR_ENV = "superadmin"


def _normalizar(email: object) -> str:
    return str(email or "").strip().lower()


def operadores_configurados() -> frozenset[str]:
    """Correos autorizados a administrar el producto desde el entorno.

    Se leen de ``COTIZAT_OPERADORES`` (separados por comas). Vacío significa
    **ningún operador**: el panel queda cerrado para todo el mundo.
    """
    crudo = os.environ.get("COTIZAT_OPERADORES", "")
    return frozenset(
        parte for parte in (_normalizar(p) for p in crudo.split(",")) if parte
    )


def _es_email_valido(email: str) -> bool:
    """Validación ligera de correo para la puerta del panel."""
    email = str(email or "").strip()
    return (
        len(email) <= 254
        and "@" in email
        and email.split("@")[0] != ""
        and email.split("@")[-1] != ""
        and ".." not in email
    )


def _operador_en_db(db, email: str):
    """Consulta la fila activa de `operadores_producto` para un correo.

    Devuelve el objeto o ``None``; nunca lanza. En PostgreSQL la política RLS
    de la tabla permite leer la fila propia aunque todavía no se haya marcado
    la sesión como operador: es la única forma de que un operador añadido por
    el panel pueda autenticar sin volver a tocar la variable de entorno.
    """
    if db is None:
        return None
    try:
        return (
            db.query(OperadorProducto)
            .filter(
                OperadorProducto.email == email,
                OperadorProducto.activo.is_(True),
            )
            .first()
        )
    except Exception:
        # Sin la tabla (SQLite en pruebas, despliegue con migración pendiente)
        # la tabla simplemente no aporta nada nuevo.
        return None


def _fila_operatoria(db, email: str):
    """Fila de operador aunque esté inactiva, o ``None``."""
    if db is None:
        return None
    try:
        return (
            db.query(OperadorProducto)
            .filter(OperadorProducto.email == email)
            .first()
        )
    except Exception:
        return None


def es_operador(
    email: object,
    *,
    email_verificado: bool = True,
    db=None,
) -> bool:
    """Indica si un correo **verificado** es operador del producto.

    Orden de decisión (la base puede rebajar a un correo aún en el entorno):

    1. Si existe una fila **activa** en ``operadores_producto``, sí.
    2. Si la fila existe pero está **inactiva**, no (suspensión manda).
    3. Si no hay fila y aparece en ``COTIZAT_OPERADORES``, sí (semilla).
    """
    if not email_verificado:
        return False
    normalizado = _normalizar(email)
    if not normalizado or not _es_email_valido(normalizado):
        return False
    fila = _fila_operatoria(db, normalizado)
    if fila is not None:
        return bool(fila.activo)
    return normalizado in operadores_configurados()


def rol_operador(
    email: object,
    *,
    email_verificado: bool = True,
    db=None,
) -> str:
    """Rol del operador autorizado, o cadena vacía si no lo es.

    - Si existe fila en ``operadores_producto``, la fila manda (permite
      rebajar a soporte/analista a un correo aún presente en el entorno).
    - Si solo está en ``COTIZAT_OPERADORES``, la semilla es ``superadmin``.
    """
    if not es_operador(email, email_verificado=email_verificado, db=db):
        return ""
    normalizado = _normalizar(email)
    fila = _fila_operatoria(db, normalizado)
    if fila is not None:
        rol = str(fila.rol or "").strip().lower()
        if rol in ROLES_OPERADOR:
            return rol
    return ROL_OPERADOR_ENV
