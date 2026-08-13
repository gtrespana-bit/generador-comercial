"""Entorno Alembic de CotizaT.

La URL nunca se guarda en el repositorio: se resuelve con la misma política
``DATABASE_URL``/SQLite que usa la aplicación.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database import Base, DATABASE_URL
from app import models  # noqa: F401  (registra todas las tablas en metadata)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ConfigParser interpreta '%' como interpolación; escaparlo permite contraseñas
# codificadas en URL sin escribir secretos en alembic.ini.
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))
target_metadata = Base.metadata


def _opciones_comunes() -> dict:
    return {
        "target_metadata": target_metadata,
        "compare_type": True,
        "compare_server_default": True,
    }


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_opciones_comunes(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, **_opciones_comunes())
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
