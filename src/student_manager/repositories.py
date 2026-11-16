"""Data access layer: all SQLAlchemy queries live in repositories."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from student_manager.models import Group, Student

class GroupRepository:
    def __init__(self, session: Session): self.session = session

    def add(self, name: str) -> Group:
        group = Group(name=name)
        self.session.add(group)
        self.session.commit()
        self.session.refresh(group)
        return group

    def get_by_id(self, group_id: int) -> Group | None:
        return self.session.get(Group, group_id)

    def get_by_name(self, name: str) -> Group | None:
        return self.session.scalar(select(Group).where(Group.name == name.strip().upper()))

    def get_all(self) -> list[Group]:
        return list(self.session.scalars(select(Group).order_by(Group.name)))

    def update_name(self, group_id: int, name: str) -> Group | None:
        group = self.get_by_id(group_id)
        if group is None: return None
        group.name = name
        self.session.commit()
        self.session.refresh(group)
        return group

    def delete(self, group_id: int) -> bool:
        group = self.get_by_id(group_id)
        if group is None: return False
        self.session.delete(group)
        self.session.commit()
        return True

class StudentRepository:
    def __init__(self, session: Session): self.session = session

    def add(self, student: Student) -> Student:
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        return student

    def get_by_id(self, student_id: int) -> Student | None:
        return self.session.get(Student, student_id)

    def get_all(self) -> list[Student]:
        return list(self.session.scalars(select(Student).options(selectinload(Student.group)).order_by(Student.id)))

    def find_by_last_name(self, surname: str) -> list[Student]:
        return [student for student in self.session.scalars(select(Student))
                if student.last_name.casefold() == surname.strip().casefold()]

    def find_by_group(self, group_name: str) -> list[Student]:
        statement = select(Student).join(Group).where(Group.name == group_name.strip().upper()).order_by(Student.id)
        return list(self.session.scalars(statement))

    def update_grade(self, student_id: int, grade: float) -> Student | None:
        student = self.get_by_id(student_id)
        if student is None: return None
        student.average_grade = grade
        self.session.commit()
        self.session.refresh(student)
        return student

    def transfer(self, student_id: int, group_id: int) -> Student | None:
        student = self.get_by_id(student_id)
        if student is None: return None
        student.group_id = group_id
        self.session.commit()
        self.session.refresh(student)
        return student

    def delete(self, student_id: int) -> bool:
        student = self.get_by_id(student_id)
        if student is None: return False
        self.session.delete(student)
        self.session.commit()
        return True
