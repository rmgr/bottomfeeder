import sys
from pathlib import Path

# --- Setup project path (must come BEFORE imports) ---
sys.path.append(str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from config.settings import settings  # Your Pydantic config
from sqlmodel import SQLModel
from models import *  # Your models/__init__.py now imports all models

# --- Alembic config ---
config = context.config

# --- Logging setup ---
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- SQLAlchemy metadata ---
target_metadata = SQLModel.metadata

# --- Inject DATABASE_URL from settings ---
escaped_url = settings.DATABASE_URL.replace("%", "%%")
config.set_main_option("sqlalchemy.url", escaped_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

print("✅ Tables found:", SQLModel.metadata.tables.keys())
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
