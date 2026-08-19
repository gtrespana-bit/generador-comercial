"""Add labor, equipment and transport metadata to resources."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision='b4c5d6e7f8a9'; down_revision='a3b4c5d6e7f8'; branch_labels=None; depends_on=None

def upgrade():
    cols=[('subtipo',sa.String(40),''),('capacidad',sa.String(80),''),('modalidad_tarifa',sa.String(30),'hora'),('incluye_operador',sa.Boolean(),False),('incluye_combustible',sa.Boolean(),False),('incluye_flete',sa.Boolean(),False),('rendimiento_jornada',sa.Float(),None),('horas_jornada_recurso',sa.Float(),8.0)]
    for name,typ,default in cols: op.add_column('recursos',sa.Column(name,typ,nullable=True,server_default=str(default).lower() if default is not None else None))
def downgrade():
    for name in ['horas_jornada_recurso','rendimiento_jornada','incluye_flete','incluye_combustible','incluye_operador','modalidad_tarifa','capacidad','subtipo']: op.drop_column('recursos',name)
