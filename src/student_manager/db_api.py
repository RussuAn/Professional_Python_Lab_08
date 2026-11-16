"""Parameterized SQL query via Python DB-API instead of ORM."""
import sqlite3
from pathlib import Path

def find_students_by_group(database_path: Path, group_name: str) -> list[tuple[str, str, float]]:
    with sqlite3.connect(database_path) as conn:
        cursor = conn.execute(
            """SELECT s.first_name, s.last_name, s.average_grade
               FROM students AS s JOIN groups AS g ON s.group_id = g.id
               WHERE g.name = ? ORDER BY s.id""",
            (group_name.strip().upper(),),
        )
        return cursor.fetchall()
