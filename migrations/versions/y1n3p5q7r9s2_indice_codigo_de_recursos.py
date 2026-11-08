"""Índice sobre ``recursos.codigo`` en PostgreSQL.

Cada recurso se busca por su código en la mayoría de lecturas del catálogo
(descomposiciones, importaciones, referencias de mercado), pero en PostgreSQL
la tabla solo tenía índice por ``id`` y por ``organizacion_id``: con ~22.000
filas por organización, cualquier consulta por código acababa en un escaneo
secuencial de la tabla completa.

El síntoma apareció al cargar las referencias nacionales de España: el
``NOT EXISTS (SELECT 1 FROM public.recursos WHERE r.codigo = s.codigo_recurso)``
recorría la tabla una vez por cada uno de los 390 códigos y la transacción
quedaba retenida con el bloqueo de la tabla.

SQLite ya creaba ``ix_recursos_codigo`` al migrar bases antiguas
(``app/models.py``); esta revisión lleva el mismo índice al esquema PostgreSQL.
Es idempotente por si el código arranca antes que la migración.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "y1n3p5q7r9s2"
down_revision: Union[str, Sequence[str], None] = "x9m2k4p8v1n6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDICE = "ix_recursos_codigo"


def _es_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _es_postgresql():
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {INDICE} ON public.recursos (codigo)"
        )
        return
    # SQLite (instalación local) ya crea el índice al migrar bases antiguas;
    # aquí solo se iguala el esquema para que las pruebas partan del mismo.
    op.execute(f"CREATE INDEX IF NOT EXISTS {INDICE} ON recursos (codigo)")


def downgrade() -> None:
    if _es_postgresql():
        op.execute(f"DROP INDEX IF EXISTS public.{INDICE}")
        return
    op.execute(f"DROP INDEX IF EXISTS {INDICE}")
