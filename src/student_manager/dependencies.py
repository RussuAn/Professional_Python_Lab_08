"""Database dependency: one Session per incoming API request."""
from collections.abc import Generator
from pathlib import Path
from sqlalchemy.orm import Session
from student_manager.database import make_engine, make_session_factory

_engine = make_engine(Path('students.db'))
SessionLocal = make_session_factory(_engine)

def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
