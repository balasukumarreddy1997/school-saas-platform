import uuid
from datetime import date, datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True
        )
    )
    school_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    )
    admission_number: str = Field(max_length=50, nullable=False)
    roll_number: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = Field(default=None)
    gender: str | None = Field(default=None, max_length=10)
    blood_group: str | None = Field(default=None, max_length=5)
    parent_name: str | None = Field(default=None, max_length=200)
    parent_phone: str | None = Field(default=None, max_length=20)
    parent_email: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
