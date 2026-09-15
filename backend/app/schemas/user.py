import uuid
from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    school_id: uuid.UUID
    first_name: str
    last_name: str
    phone: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    school_id: uuid.UUID
    first_name: str
    last_name: str
    phone: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class UserRoleRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
