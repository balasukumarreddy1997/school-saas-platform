import uuid
from datetime import date, datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class Teacher(SQLModel, table=True):
    __tablename__ = "teachers"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True
        )
    )
    school_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    )
    employee_id: str = Field(max_length=50, nullable=False)
    department: str | None = Field(default=None, max_length=100)
    qualification: str | None = Field(default=None, max_length=200)
    date_of_joining: date | None = Field(default=None)
    is_class_teacher: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
