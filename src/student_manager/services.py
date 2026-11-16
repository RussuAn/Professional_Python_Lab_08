"""Business operations and atomic student transfers."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from student_manager.models import Group, Student

class StudentService:
    def __init__(self, session: Session): self.session = session

    def group_average(self, group_id: int) -> float | None:
        result = self.session.scalar(select(func.avg(Student.average_grade)).where(Student.group_id == group_id))
        return float(result) if result is not None else None

    def best_student(self) -> Student | None:
        return self.session.scalar(select(Student).order_by(Student.average_grade.desc(), Student.id).limit(1))

    def group_counts(self) -> list[tuple[str, int, float | None]]:
        statement = (select(Group.name, func.count(Student.id), func.avg(Student.average_grade))
                     .outerjoin(Student).group_by(Group.id).order_by(Group.name))
        return [(name, count, float(avg) if avg is not None else None)
                for name, count, avg in self.session.execute(statement)]

def transfer_students(session: Session, student_ids: list[int], new_group_id: int) -> None:
    """All-or-nothing batch transfer; any error rolls back earlier updates."""
    try:
        target = session.get(Group, new_group_id)
        if target is None: raise ValueError("Цільову групу не знайдено")
        for student_id in student_ids:
            student = session.get(Student, student_id)
            if student is None: raise ValueError(f"Студента {student_id} не знайдено")
            student.group_id = target.id
        session.commit()
    except Exception:
        session.rollback()
        raise
