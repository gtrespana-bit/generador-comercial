"""Persist effective resource price provenance on decomposition rows and history."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision='a3b4c5d6e7f8'; down_revision='f2a3b4c5d6e7'; branch_labels=None; depends_on=None

def upgrade():
    for col, typ, default in [('moneda',sa.String(10),'USD'),('origen_precio',sa.String(20),'base'),('confianza_precio',sa.String(20),'provisional'),('fuente_precio',sa.String(200),'')]:
        op.add_column('descomposicion_filas', sa.Column(col,typ,nullable=True,server_default=default))
    op.create_table('historial_precios_recursos',sa.Column('id',sa.Integer,primary_key=True),sa.Column('precio_mercado_id',sa.Integer,sa.ForeignKey('precios_recursos_mercado.id',ondelete='CASCADE'),nullable=False),sa.Column('precio_anterior',sa.Float,nullable=True),sa.Column('precio_nuevo',sa.Float,nullable=False),sa.Column('moneda',sa.String(10),nullable=False,server_default='USD'),sa.Column('fecha',sa.DateTime,nullable=True),sa.Column('motivo',sa.String(250),server_default=''),sa.Column('fuente',sa.String(200),server_default=''))
    op.create_index('ix_historial_precios_recursos_precio_mercado_id','historial_precios_recursos',['precio_mercado_id'])

def downgrade():
    op.drop_index('ix_historial_precios_recursos_precio_mercado_id',table_name='historial_precios_recursos'); op.drop_table('historial_precios_recursos')
    for col in ['fuente_precio','confianza_precio','origen_precio','moneda']: op.drop_column('descomposicion_filas',col)
