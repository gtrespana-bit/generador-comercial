"""Operadores del producto: quién puede administrar licencias (E1-060).

Un **operador** es quien explota CotizaT como negocio (hoy, el titular). No es
un rol de organización: los roles `propietario`, `administrador`, `miembro` y
`lectura` describen permisos *dentro* de la empresa de un cliente, mientras que
el operador actúa *sobre* las cuentas de clientes para conceder licencias,
regalar meses o compensar una incidencia.

Por qué la lista vive en una variable de entorno
------------------------------------------------
La tentación evidente sería una columna `es_operador` en `usuarios`. Se ha
descartado a propósito: esa columna sería escribible desde la propia
aplicación, así que **cualquier fallo de autorización o inyección se
convertiría en una escalada a superadministrador**. Una variable de entorno
solo se cambia en el panel de Vercel, fuera del alcance del código en ejecución
y de la base de datos.

Consecuencia deliberada: **no existe ninguna pantalla para nombrar operadores**.
Se añaden en Vercel y se redespliega. Es incómodo a propósito; debería serlo.

Defensa en profundidad
----------------------
Esta lista es la primera barrera. La segunda es RLS: la tabla `licencias`
declara políticas que exigen la marca de operador en la sesión de PostgreSQL,
de modo que una sesión normal de cliente no ve ni una fila aunque el código
llegara a consultarla por error.
"""
from __future__ import annotations

import os


def _normalizar(email: object) -> str:
    return str(email or "").strip().lower()


def operadores_configurados() -> frozenset[str]:
    """Correos autorizados a administrar licencias.

    Se leen de ``COTIZAT_OPERADORES`` (separados por comas). Vacío significa
    **ningún operador**: el panel queda cerrado para todo el mundo, que es el
    valor seguro por omisión. Es intencional que un despliegue recién creado no
    tenga administrador hasta que alguien lo declare explícitamente.
    """
    crudo = os.environ.get("COTIZAT_OPERADORES", "")
    return frozenset(
        parte for parte in (_normalizar(p) for p in crudo.split(",")) if parte
    )


def es_operador(email: object, *, email_verificado: bool = True) -> bool:
    """Indica si un correo **verificado** pertenece a la lista de operadores.

    Se exige la verificación del email porque la pertenencia se decide por
    dirección: sin confirmar, cualquiera que registrase una cuenta con el correo
    del titular obtendría el panel sin controlar el buzón.
    """
    if not email_verificado:
        return False
    normalizado = _normalizar(email)
    return bool(normalizado) and normalizado in operadores_configurados()
