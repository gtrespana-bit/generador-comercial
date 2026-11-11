"""Marca de organización de prueba (no cuenta en métricas del panel).

Las cuentas que el titular crea para probar el producto (QA, demos internas,
capturas de pantalla) contaminaban todos los KPIs del panel admin: MRR,
totales de clientes, embudo, cohortes de retención y ventas. No hay forma
fiable de detectarlas por email o nombre, así que se añade un flag manual
`organizaciones.es_test` que el operador activa desde la ficha de cliente.

Cuando es True la organización sigue visible en el directorio (con etiqueta
gris "TEST") pero se excluye de *todas* las métricas agregadas del panel:
resumen_admin, finanzas, ventas, cobros, renovaciones, analítica, marketing
y uso de presupuestos. En SQLite (tests) la columna nace con default false y
la rama de PostgreSQL la añade con el mismo default; los despliegues sin
migración siguen funcionando porque todos los lectores la tratan como
nullable/False vía getattr.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a8f1c3d9e7b2"
down_revision: Union[str, Sequence[str], None] = "z3m9k2p8v1n7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizaciones",
        sa.Column(
            "es_test",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Índice parcial no necesario con pocas orgs, pero ayuda al panel que filtra
    # constantemente por es_test = false.
    op.create_index(
        "ix_organizaciones_es_test",
        "organizaciones",
        ["es_test"],
    )


def downgrade() -> None:
    op.drop_index("ix_organizaciones_es_test", table_name="organizaciones")
    op.drop_column("organizaciones", "es_test")
