"""Un recordatorio de tarifas que se puede posponer o silenciar.

La revisión de tarifas (``t9b4d7e2c5f8``) pedía confirmar los precios antes de
cotizar, pero solo tenía dos desenlaces: confirmar o no hacer nada. Quien
decidía «lo miro la semana que viene» seguía viendo el mismo aviso al día
siguiente, y quien ya trabajaba con sus precios no tenía forma de decir «no me
lo repitas» sin confirmar tarifas que no había mirado. Un recordatorio que no se
puede posponer acaba siendo un recordatorio que se ignora.

Esta revisión añade las dos decisiones que faltaban, ambas por organización:

- ``configuracion.tarifas_recordatorio_pospuesto_hasta``: «ahora no». Un día
  concreto a partir del cual el aviso vuelve. Se guarda la fecha, no un
  contador, para que el aviso vuelva aunque nadie entre a la aplicación.
- ``configuracion.tarifas_recordatorio_silenciado``: «no me lo vuelvas a
  pedir». El aviso desaparece del panel, del catálogo y de la ficha del
  presupuesto; la pantalla de revisión sigue accesible desde *Recursos*.

Ninguna de las dos confirma precios: silenciar no es revisar. Las tarifas
siguen apareciendo como pendientes en la pantalla de revisión y en la guía de
inicio, y ahí se puede reactivar el recordatorio cuando se quiera.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "u1c5e8b3d7a9"
down_revision: Union[str, Sequence[str], None] = "t9b4d7e2c5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


#: (tabla, columna, tipo)
COLUMNAS = (
    ("configuracion", "tarifas_recordatorio_pospuesto_hasta", sa.Date()),
    ("configuracion", "tarifas_recordatorio_silenciado", sa.Boolean()),
)


def _existe(tabla: str, columna: str) -> bool:
    try:
        from sqlalchemy import inspect as _inspect

        return columna in {c["name"] for c in _inspect(op.get_bind()).get_columns(tabla)}
    except Exception:
        return False


def upgrade() -> None:
    # Idempotente por el mismo motivo que las revisiones anteriores: el arranque
    # de la aplicación intenta crear estas columnas por su cuenta cuando el
    # despliegue llega antes que la migración.
    for tabla, columna, tipo in COLUMNAS:
        if _existe(tabla, columna):
            continue
        op.add_column(
            tabla,
            sa.Column(
                columna,
                tipo,
                nullable=True,
                server_default=sa.false() if isinstance(tipo, sa.Boolean) else None,
            ),
        )


def downgrade() -> None:
    for tabla, columna, _tipo in COLUMNAS:
        with op.batch_alter_table(tabla) as lote:
            lote.drop_column(columna)
