import uuid
from datetime import datetime
from enum import Enum

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class RoleType(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    MANAGEMENT = "management"


class User(SQLAlchemyBaseUserTableUUID, SQLModel, table=True):
    __tablename__ = "users"

    school_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    )
    first_name: str = Field(max_length=100, nullable=False)
    last_name: str = Field(max_length=100, nullable=False)
    phone: str | None = Field(default=None, max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_login_at: datetime | None = Field(default=None)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    role: RoleType = Field(sa_column=Column(String(20), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    class Config:
        use_enum_values = True
