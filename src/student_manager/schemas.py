"""Pydantic request/response contracts for student and group endpoints."""
from pydantic import BaseModel, ConfigDict, Field, field_validator

class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def clean_group(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("Порожня назва групи")
        return value

class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class StudentCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    group_id: int = Field(gt=0)
    average_grade: float = Field(ge=0, le=100, allow_inf_nan=False)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("first_name", "last_name")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Ім'я або прізвище має містити щонайменше 2 символи")
        return value

class StudentUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    group_id: int | None = Field(default=None, gt=0)
    average_grade: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("first_name", "last_name")
    @classmethod
    def nonblank(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Ім'я не може бути null")
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Ім'я або прізвище має містити щонайменше 2 символи")
        return value

class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    group_id: int
    average_grade: float
    email: str | None

class GroupStatistics(BaseModel):
    group_id: int
    students_count: int
    average_grade: float | None
    best_student: StudentResponse | None
