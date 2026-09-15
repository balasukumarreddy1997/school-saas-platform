import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class School(SQLModel, table=True):
    __tablename__ = "schools"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(max_length=200, nullable=False)
    code: str = Field(max_length=20, unique=True, index=True, nullable=False)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    address: Optional[str] = Field(default=None, max_length=500)
    contact_email: Optional[str] = Field(default=None, max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    settings: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
