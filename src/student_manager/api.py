"""HTTP resource layer for the Lab 01 student management domain."""
from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from student_manager.database import make_engine
from student_manager.dependencies import get_session
from student_manager.models import Base, Group, Student
from student_manager.repositories import GroupRepository, StudentRepository
from student_manager.schemas import GroupCreate, GroupResponse, GroupStatistics, StudentCreate, StudentResponse, StudentUpdate
from student_manager.services import StudentService

@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine = make_engine(Path("students.db"))
    Base.metadata.create_all(engine)
    engine.dispose()
    yield

app = FastAPI(title="Student Manager REST API", version="0.8.0", lifespan=lifespan)
DB = Annotated[Session, Depends(get_session)]

def require_group(session: Session, group_id: int) -> Group:
    group = GroupRepository(session).get_by_id(group_id)
    if group is None:
        raise HTTPException(404, "Group not found")
    return group

def require_student(session: Session, student_id: int) -> Student:
    student = StudentRepository(session).get_by_id(student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    return student

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/groups", response_model=GroupResponse, status_code=201)
async def create_group(payload: GroupCreate, session: DB) -> Group:
    if GroupRepository(session).get_by_name(payload.name):
        raise HTTPException(409, "Group already exists")
    try:
        return GroupRepository(session).add(payload.name)
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(409, "Group already exists") from error

@app.get("/groups", response_model=list[GroupResponse])
async def list_groups(session: DB) -> list[Group]:
    return GroupRepository(session).get_all()

@app.get("/students", response_model=list[StudentResponse])
async def list_students(
    session: DB,
    group_id: int | None = Query(default=None, gt=0),
    last_name: str | None = None,
    min_grade: float | None = Query(default=None, ge=0, le=100),
) -> list[Student]:
    students = StudentRepository(session).get_all()
    if group_id is not None:
        students = [student for student in students if student.group_id == group_id]
    if last_name is not None:
        students = [student for student in students if student.last_name.casefold() == last_name.strip().casefold()]
    if min_grade is not None:
        students = [student for student in students if student.average_grade >= min_grade]
    return students

@app.get("/students/best", response_model=StudentResponse | None)
async def best_student(session: DB) -> Student | None:
    return StudentService(session).best_student()

@app.get("/students/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int, session: DB) -> Student:
    return require_student(session, student_id)

@app.post("/students", response_model=StudentResponse, status_code=201)
async def create_student(payload: StudentCreate, session: DB) -> Student:
    require_group(session, payload.group_id)
    student = Student(**payload.model_dump())
    try:
        return StudentRepository(session).add(student)
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(409, "Student violates database constraint") from error

@app.patch("/students/{student_id}", response_model=StudentResponse)
async def patch_student(student_id: int, payload: StudentUpdate, session: DB) -> Student:
    student = require_student(session, student_id)
    updates = payload.model_dump(exclude_unset=True)
    if "group_id" in updates:
        require_group(session, updates["group_id"])
    for key, value in updates.items():
        setattr(student, key, value)
    try:
        session.commit()
        session.refresh(student)
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(409, "Student violates database constraint") from error
    return student

@app.delete("/students/{student_id}", status_code=204)
async def delete_student(student_id: int, session: DB) -> Response:
    student = require_student(session, student_id)
    StudentRepository(session).delete(student.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/groups/{group_id}/students", response_model=list[StudentResponse])
async def group_students(group_id: int, session: DB) -> list[Student]:
    require_group(session, group_id)
    return list(session.scalars(select(Student).where(Student.group_id == group_id).order_by(Student.id)))

@app.get("/groups/{group_id}/statistics", response_model=GroupStatistics)
async def group_statistics(group_id: int, session: DB) -> GroupStatistics:
    require_group(session, group_id)
    statement = select(func.count(Student.id), func.avg(Student.average_grade)).where(Student.group_id == group_id)
    count, avg = session.execute(statement).one()
    best = session.scalar(select(Student).where(Student.group_id == group_id).order_by(Student.average_grade.desc(), Student.id).limit(1))
    return GroupStatistics(group_id=group_id, students_count=count, average_grade=float(avg) if avg is not None else None,
                           best_student=StudentResponse.model_validate(best) if best else None)
