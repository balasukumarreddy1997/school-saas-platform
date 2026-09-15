import uuid
from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, index=True)
    school_id: uuid.UUID = Field(foreign_key="schools.id", index=True)
    admission_number: str = Field(max_length=50, nullable=False)
    roll_number: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = Field(default=None)
    gender: Optional[str] = Field(default=None, max_length=10)
    blood_group: Optional[str] = Field(default=None, max_length=5)
    parent_name: Optional[str] = Field(default=None, max_length=200)
    parent_phone: Optional[str] = Field(default=None, max_length=20)
    parent_email: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
