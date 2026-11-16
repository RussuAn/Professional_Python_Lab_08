from pathlib import Path
import sqlite3
import pytest
from alembic import command
from alembic.config import Config

def test_alembic_upgrade_and_downgrade(tmp_path: Path):
    config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
    config.set_main_option('script_location', str(Path(__file__).parents[1] / 'migrations'))
    db = tmp_path / 'migrations_test.db'
    config.set_main_option('sqlalchemy.url', f'sqlite:///{db.as_posix()}')
    command.upgrade(config,'head')
    with sqlite3.connect(db) as conn:
        cols=[row[1] for row in conn.execute('PRAGMA table_info(students)')]
        assert 'email' in cols
    command.downgrade(config,'001_initial')
    with sqlite3.connect(db) as conn:
        cols=[row[1] for row in conn.execute('PRAGMA table_info(students)')]
        assert 'email' not in cols
    command.upgrade(config,'head')
    with sqlite3.connect(db) as conn:
        assert 'email' in [row[1] for row in conn.execute('PRAGMA table_info(students)')]
