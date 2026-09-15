import uuid
from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class Teacher(SQLModel, table=True):
    __tablename__ = "teachers"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, index=True)
    school_id: uuid.UUID = Field(foreign_key="schools.id", index=True)
    employee_id: str = Field(max_length=50, nullable=False)
    department: Optional[str] = Field(default=None, max_length=100)
    qualification: Optional[str] = Field(default=None, max_length=200)
    date_of_joining: Optional[date] = Field(default=None)
    is_class_teacher: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
