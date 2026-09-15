"""Timetable models."""
import uuid
from datetime import time, datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class Timetable(SQLModel, table=True):
    __tablename__ = "timetables"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    school_id: str = Field(index=True)
    class_name: str = Field(max_length=50)  # e.g., "10-A", "9-B"
    subject_id: str = Field()
    teacher_id: Optional[str] = Field(default=None)
    day_of_week: int = Field(ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: str = Field(max_length=10)  # "09:00"
    end_time: str = Field(max_length=10)  # "09:45"
    room: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def day_name(self) -> str:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else "Unknown"


class ClassSection(SQLModel, table=True):
    """Defines class sections in the school."""
    __tablename__ = "class_sections"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    school_id: str = Field(index=True)
    name: str = Field(max_length=50)  # e.g., "10-A"
    grade: int = Field(ge=1, le=12)  # Grade 1-12
    section: str = Field(max_length=10)  # A, B, C, etc.
    class_teacher_id: Optional[str] = Field(default=None)
    room: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
