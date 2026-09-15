"""Announcement models."""
import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Announcement(SQLModel, table=True):
    __tablename__ = "announcements"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    school_id: str = Field(foreign_key="schools.id", index=True)
    title: str = Field(max_length=200)
    content: str = Field(max_length=5000)
    type: str = Field(default="general", max_length=50)  # general, urgent, event, holiday
    target_audience: str = Field(default="all", max_length=50)  # all, students, teachers, parents
    created_by: str = Field(foreign_key="users.id")
    is_pinned: bool = Field(default=False)
    is_active: bool = Field(default=True)
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
