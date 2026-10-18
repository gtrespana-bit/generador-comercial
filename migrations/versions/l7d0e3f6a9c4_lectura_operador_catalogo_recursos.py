"""Lectura de operador sobre el catálogo de recursos (panel de matrices).

El importador de la matriz nacional de precios resuelve cada fila del CSV
contra ``public.recursos`` por código (``resolver_recursos`` en modo
``nacional`` de ``app/services/importador_precios_mercado.py``). La sesión
del panel de administración (``get_operator_db``) autentica al operador y
marca ``cotizat.es_operador``, pero **no activa ninguna organización**: la
política RLS ``cotizat_tenant_select`` de ``recursos`` (creada en
``c93e7a4d20f1``) exige ``cotizat.organization_id`` con valor y una
membresía activa, así que el ``SELECT`` devolvía cero filas y las 388 filas
de la matriz británica se rechazaron como «recurso no encontrado» aunque el
catálogo estaba sembrado en la base.

El modo ``nacional`` del importador usa ``sin_filtro_organizacion``, pero
esa opción solo levanta el filtro ORM de la aplicación; el RLS de
PostgreSQL se aplica por debajo y la consulta seguía viendo la tabla vacía.
Con SQLite (escritorio y pruebas) no hay RLS y el fallo no se reproduce:
por eso el panel se probó verde y falló en producción.

La solución es una política de SELECT adicional para el rol de aplicación.
Las políticas permisivas se combinan con OR, así que la visibilidad de cada
organización sobre sus propios recursos no cambia. Es **solo lectura**: el
operador no crea, modifica ni borra recursos de ninguna empresa; es lo
único que el importador necesita (id, código, unidad y descripción para
resolver y convertir). La escritura de las referencias nacionales ya la
cubren las políticas de ``precios_recursos_mercado`` (``e7b3c1d5a204``).

La misma marca ``cotizat.es_operador`` que habilita las políticas de
``licencias`` y de los precios nacionales habilita esta: si la comprobación
de operador fallara por un error de código, el RLS seguiría devolviendo
cero filas en vez de filtrar de más.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "l7d0e3f6a9c4"
down_revision: Union[str, Sequence[str], None] = "k6c9f2d5b8a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"
TABLA = "recursos"
POLITICA = "cotizat_operador_select_recursos"

#: Misma expresión que las políticas de ``precios_recursos_mercado``
#: (``e7b3c1d5a204``): la marca la instala ``_aplicar_contexto_postgresql``
#: con ``set_config`` por transacción y vale 'on' solo para operadores.
IS_OPERATOR = (
    "COALESCE("
    "pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)"
)


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS: allí el importador ya
        # ve el catálogo completo con ``sin_filtro_organizacion``.
        return
    op.execute(f"DROP POLICY IF EXISTS {POLITICA} ON public.{TABLA}")
    op.execute(
        f"CREATE POLICY {POLITICA} ON public.{TABLA} "
        f"FOR SELECT TO {APP_ROLE} USING ({IS_OPERATOR})"
    )


def downgrade() -> None:
    if not _postgres():
        return
    op.execute(f"DROP POLICY IF EXISTS {POLITICA} ON public.{TABLA}")
