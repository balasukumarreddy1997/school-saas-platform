import uuid
from datetime import date as DateType, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class Subject(SQLModel, table=True):
    __tablename__ = "subjects"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    school_id: uuid.UUID = Field(foreign_key="schools.id", nullable=False)
    name: str = Field(max_length=100, nullable=False)
    code: str = Field(max_length=20, nullable=False)
    description: Optional[str] = Field(default=None, max_length=500)
    credits: int = Field(default=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class StudentSubject(SQLModel, table=True):
    __tablename__ = "student_subjects"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", nullable=False)
    subject_id: uuid.UUID = Field(foreign_key="subjects.id", nullable=False)
    teacher_id: Optional[uuid.UUID] = Field(foreign_key="teachers.id", default=None)
    academic_year: str = Field(max_length=20, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class AttendanceRecord(SQLModel, table=True):
    __tablename__ = "attendance"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", nullable=False)
    record_date: DateType = Field(nullable=False)
    status: str = Field(max_length=20, nullable=False)  # present, absent, late, excused
    remarks: Optional[str] = Field(default=None, max_length=200)
    recorded_by: Optional[uuid.UUID] = Field(foreign_key="users.id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Result(SQLModel, table=True):
    __tablename__ = "results"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", nullable=False)
    subject_id: uuid.UUID = Field(foreign_key="subjects.id", nullable=False)
    exam_name: str = Field(max_length=100, nullable=False)
    exam_date: Optional[DateType] = Field(default=None)
    max_marks: float = Field(default=100.0)
    marks_obtained: float = Field(nullable=False)
    grade: Optional[str] = Field(default=None, max_length=5)
    remarks: Optional[str] = Field(default=None, max_length=200)
    academic_year: str = Field(max_length=20, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
