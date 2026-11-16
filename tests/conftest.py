from pathlib import Path
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from student_manager.models import Base

@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / 'test_students.db'

@pytest.fixture
def session(db_path: Path):
    engine = create_engine(f'sqlite:///{db_path.as_posix()}')
    @event.listens_for(engine, 'connect')
    def fk(conn, _rec): conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as sess:
        yield sess
    engine.dispose()
