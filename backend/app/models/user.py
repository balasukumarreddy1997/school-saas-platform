import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class RoleType(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    MANAGEMENT = "management"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    school_id: uuid.UUID = Field(foreign_key="schools.id", index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    hashed_password: str = Field(max_length=255)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = Field(default=None)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    role: str = Field(max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
