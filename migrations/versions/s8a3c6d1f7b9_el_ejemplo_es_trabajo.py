"""El ejemplo del alta pasa a ser material de trabajo, no un documento falso.

Medido en la base de producción el 02/11/2026: 36 presupuestos de ejemplo
sembrados, **ninguno** convertido en presupuesto real, y 33 de las 41 cuentas
reales sin haber creado nunca uno (7 de 41, 17 %). La causa no era que el
ejemplo fuera malo: era que el producto le decía al usuario que no valía.

- La guía de inicio decía «el contenido de demostración no completa cliente,
  presupuesto ni PDF».
- El cliente se llamaba «Cliente de demostración» y el documento
  «Remodelación residencial de demostración».
- Al duplicarlo, la copia heredaba ``es_demo = TRUE`` y seguía sin contar.
- Descargar su PDF no marcaba el paso del recorrido.

Esta migración **no cambia qué es un demo** (``es_demo`` sigue siendo la
marca que excluye un documento de los números de negocio). Añade una columna
independiente, ``es_ejemplo``, para poder responder la única pregunta que
importa: *¿esta empresa arrancó desde el ejemplo del alta?* Con eso se mide
si el camino nuevo convierte mejor, sin ensuciar ningún KPI.

Los ejemplos ya sembrados se marcan como ejemplos (``es_ejemplo = TRUE``);
seguirán siendo ``es_demo = TRUE`` hasta que el usuario haga suyo el
documento. Es un ``ALTER TABLE ... ADD COLUMN`` con valor por omisión: no
reescribe la tabla ni bloquea escrituras.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "s8a3c6d1f7b9"
down_revision: Union[str, Sequence[str], None] = "r7f2b1d4e8a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#: (tabla, nombre de la columna)
COLUMNAS = (
    ("presupuestos", "es_ejemplo"),
    ("clientes", "es_ejemplo"),
)


def upgrade() -> None:
    for tabla, columna in COLUMNAS:
        op.add_column(
            tabla,
            sa.Column(
                columna,
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("FALSE"),
            ),
        )

    # Los documentos sembrados por `sembrar_demo` se reconocen por `es_demo`
    # (es la única marca que existía) y por eso mismo se pueden marcar sin
    # ambigüedad: nadie más crea filas con esa bandera.
    for tabla, _columna in COLUMNAS:
        op.execute(
            f"UPDATE {tabla} SET es_ejemplo = TRUE WHERE es_demo IS TRUE"
        )


def downgrade() -> None:
    for tabla, columna in COLUMNAS:
        with op.batch_alter_table(tabla) as lote:
            lote.drop_column(columna)
