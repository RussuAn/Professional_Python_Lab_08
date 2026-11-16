"""Alembic runtime environment."""
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool, event
from student_manager.models import Base
config = context.config
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction(): context.run_migrations()

def run_migrations_online() -> None:
    engine = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    @event.listens_for(engine, "connect")
    def enable_fk(dbapi_conn, _rec): dbapi_conn.execute("PRAGMA foreign_keys=ON")
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction(): context.run_migrations()
    engine.dispose()

if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
