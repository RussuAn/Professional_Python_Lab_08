"""Database entities with one-to-many group / student relationship."""
from __future__ import annotations
from math import isfinite
from sqlalchemy import CheckConstraint, ForeignKey, String, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates

class Base(DeclarativeBase):
    pass

class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    students: Mapped[list[Student]] = relationship(back_populates="group")

    @validates("name")
    def validate_name(self, _key: str, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("Назва групи не може бути порожньою")
        return value

class Student(Base):
    __tablename__ = "students"
    __table_args__ = (CheckConstraint("average_grade >= 0 AND average_grade <= 100", name="valid_grade"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    average_grade: Mapped[float] = mapped_column(Float, nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    group: Mapped[Group] = relationship(back_populates="students")

    @validates("first_name", "last_name")
    def validate_name(self, key: str, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{key} не може бути порожнім")
        return value

    @validates("average_grade")
    def validate_grade(self, _key: str, value: float) -> float:
        value = float(value)
        if not isfinite(value) or not 0 <= value <= 100:
            raise ValueError("Середній бал має бути від 0 до 100")
        return value

    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"
