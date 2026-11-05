"""Datos bancarios propios de un presupuesto (heredar o escribir unos).

Los datos bancarios y métodos de pago viven en ``configuracion`` y son de la
**empresa**: se escriben una vez y salen en todos los presupuestos. Eso funciona
mientras todo se cobre en la misma cuenta, pero hay presupuestos que no encajan:
una obra que se cobra en otra cuenta, un cliente extranjero que paga por Zelle o
USDT, un anticipo que va a nombre de un socio. Hasta ahora la única salida era
cambiar los datos de la empresa —afectando a todos los documentos— o corregir el
PDF a mano.

Esta revisión añade ``presupuestos.datos_bancarios`` con **tres** valores, y la
diferencia entre los dos últimos es la que hace que la función sea útil:

- ``NULL`` → **hereda** los de Configuración. Es el valor de todos los
  presupuestos ya guardados: al añadir la columna sin rellenarla, ningún
  documento cambia y nadie tiene que volver a editar nada.
- ``''`` → este presupuesto **no** muestra datos de pago. Sin este caso no habría
  forma de quitar el bloque en un documento cobrado por otro medio sin borrar los
  datos de la empresa.
- texto → datos **propios**.

No se duplica el texto general en cada fila a propósito: copiarlo al crear el
presupuesto congelaría los datos de hoy y un cambio de cuenta en Configuración
dejaría de llegar a los presupuestos nuevos. La herencia se resuelve al generar
el documento, y las versiones enviadas guardan el texto ya resuelto en su
instantánea (``presupuesto_versiones.datos_snapshot``), que no se toca aquí.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "v2d7f1a6b9c3"
down_revision: Union[str, Sequence[str], None] = "u1c5e8b3d7a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existe(tabla: str, columna: str) -> bool:
    try:
        from sqlalchemy import inspect as _inspect

        return columna in {c["name"] for c in _inspect(op.get_bind()).get_columns(tabla)}
    except Exception:
        return False


def upgrade() -> None:
    # Idempotente por el mismo motivo que las revisiones anteriores: el arranque
    # de la aplicación intenta crear la columna por su cuenta cuando el
    # despliegue llega antes que la migración.
    if _existe("presupuestos", "datos_bancarios"):
        return
    op.add_column(
        "presupuestos",
        sa.Column("datos_bancarios", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    with op.batch_alter_table("presupuestos") as lote:
        lote.drop_column("datos_bancarios")
