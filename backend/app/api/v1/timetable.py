"""Timetable API endpoints."""
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_async_session


def str_to_uuid(s: str) -> uuid.UUID:
    """Convert a hex string (with or without dashes) to UUID."""
    if isinstance(s, uuid.UUID):
        return s
    # Remove dashes if present and convert
    clean = s.replace('-', '')
    return uuid.UUID(clean)
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.academic import Subject
from app.models.timetable import Timetable, ClassSection
from app.core.security import get_current_user

router = APIRouter(prefix="/timetable", tags=["timetable"])


class TimetableCreate(BaseModel):
    class_name: str
    subject_id: str
    teacher_id: Optional[str] = None
    day_of_week: int
    start_time: str
    end_time: str
    room: Optional[str] = None


class TimetableResponse(BaseModel):
    id: str
    class_name: str
    subject_id: str
    subject_name: str
    teacher_id: Optional[str]
    teacher_name: Optional[str]
    day_of_week: int
    day_name: str
    start_time: str
    end_time: str
    room: Optional[str]


class ClassSectionCreate(BaseModel):
    name: str
    grade: int
    section: str
    class_teacher_id: Optional[str] = None
    room: Optional[str] = None


@router.get("/my-schedule")
async def get_my_schedule(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get timetable for the current student."""
    # Get student - use UUID directly
    result = await session.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # For now, assume student is in class "10-A" (we'd normally get this from student record)
    class_name = "10-A"

    # Get timetable entries for this class - Timetable uses str type, so convert
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')
    result = await session.execute(
        select(Timetable).where(
            and_(
                Timetable.school_id == school_id_str,
                Timetable.class_name == class_name,
                Timetable.is_active == True,
            )
        ).order_by(Timetable.day_of_week, Timetable.start_time)
    )
    entries = result.scalars().all()

    # Enrich with subject and teacher names
    schedule = []
    for entry in entries:
        # Get subject - convert str to UUID for Subject model
        subject_uuid = str_to_uuid(entry.subject_id)
        sub_result = await session.execute(select(Subject).where(Subject.id == subject_uuid))
        subject = sub_result.scalar_one_or_none()

        # Get teacher - convert str to UUID for Teacher model
        teacher_name = None
        if entry.teacher_id:
            teacher_uuid = str_to_uuid(entry.teacher_id)
            teacher_result = await session.execute(select(Teacher).where(Teacher.id == teacher_uuid))
            teacher = teacher_result.scalar_one_or_none()
            if teacher:
                teacher_result = await session.execute(select(User).where(User.id == teacher.user_id))
                teacher_user = teacher_result.scalar_one_or_none()
                if teacher_user:
                    teacher_name = f"{teacher_user.first_name} {teacher_user.last_name}"

        schedule.append({
            "id": entry.id,
            "class_name": entry.class_name,
            "subject_id": entry.subject_id,
            "subject_name": subject.name if subject else "Unknown",
            "teacher_id": entry.teacher_id,
            "teacher_name": teacher_name,
            "day_of_week": entry.day_of_week,
            "day_name": entry.day_name,
            "start_time": entry.start_time,
            "end_time": entry.end_time,
            "room": entry.room,
        })

    # Group by day
    by_day = {}
    for item in schedule:
        day = item["day_name"]
        if day not in by_day:
            by_day[day] = []
        by_day[day].append(item)

    return {"class_name": class_name, "schedule": schedule, "by_day": by_day}


@router.get("/teacher-schedule")
async def get_teacher_schedule(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get timetable for the current teacher."""
    # Get teacher - use UUID directly
    result = await session.execute(
        select(Teacher).where(Teacher.user_id == current_user.id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")

    # Get timetable entries for this teacher - Timetable uses str type
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')
    teacher_id_str = teacher.id.hex if hasattr(teacher.id, 'hex') else str(teacher.id).replace('-', '')
    result = await session.execute(
        select(Timetable).where(
            and_(
                Timetable.school_id == school_id_str,
                Timetable.teacher_id == teacher_id_str,
                Timetable.is_active == True,
            )
        ).order_by(Timetable.day_of_week, Timetable.start_time)
    )
    entries = result.scalars().all()

    # Enrich with subject names
    schedule = []
    for entry in entries:
        subject_uuid = str_to_uuid(entry.subject_id)
        sub_result = await session.execute(select(Subject).where(Subject.id == subject_uuid))
        subject = sub_result.scalar_one_or_none()

        schedule.append({
            "id": entry.id,
            "class_name": entry.class_name,
            "subject_id": entry.subject_id,
            "subject_name": subject.name if subject else "Unknown",
            "day_of_week": entry.day_of_week,
            "day_name": entry.day_name,
            "start_time": entry.start_time,
            "end_time": entry.end_time,
            "room": entry.room,
        })

    # Group by day
    by_day = {}
    for item in schedule:
        day = item["day_name"]
        if day not in by_day:
            by_day[day] = []
        by_day[day].append(item)

    return {"schedule": schedule, "by_day": by_day}


# Admin endpoints
@router.get("/all")
async def get_all_timetables(
    class_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get all timetable entries (admin)."""
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')
    query = select(Timetable).where(
        Timetable.school_id == school_id_str,
        Timetable.is_active == True,
    )
    if class_name:
        query = query.where(Timetable.class_name == class_name)
    query = query.order_by(Timetable.class_name, Timetable.day_of_week, Timetable.start_time)

    result = await session.execute(query)
    entries = result.scalars().all()

    # Enrich with subject and teacher names
    schedule = []
    for entry in entries:
        subject_uuid = str_to_uuid(entry.subject_id)
        sub_result = await session.execute(select(Subject).where(Subject.id == subject_uuid))
        subject = sub_result.scalar_one_or_none()

        teacher_name = None
        if entry.teacher_id:
            teacher_uuid = str_to_uuid(entry.teacher_id)
            teacher_result = await session.execute(select(Teacher).where(Teacher.id == teacher_uuid))
            teacher = teacher_result.scalar_one_or_none()
            if teacher:
                teacher_result = await session.execute(select(User).where(User.id == teacher.user_id))
                teacher_user = teacher_result.scalar_one_or_none()
                if teacher_user:
                    teacher_name = f"{teacher_user.first_name} {teacher_user.last_name}"

        schedule.append({
            "id": entry.id,
            "class_name": entry.class_name,
            "subject_id": entry.subject_id,
            "subject_name": subject.name if subject else "Unknown",
            "teacher_id": entry.teacher_id,
            "teacher_name": teacher_name,
            "day_of_week": entry.day_of_week,
            "day_name": entry.day_name,
            "start_time": entry.start_time,
            "end_time": entry.end_time,
            "room": entry.room,
        })

    return schedule


@router.post("/")
async def create_timetable_entry(
    data: TimetableCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new timetable entry (admin)."""
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')
    entry = Timetable(
        school_id=school_id_str,
        class_name=data.class_name,
        subject_id=data.subject_id,
        teacher_id=data.teacher_id,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time,
        room=data.room,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return {"id": entry.id, "message": "Timetable entry created"}


@router.delete("/{entry_id}")
async def delete_timetable_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Delete a timetable entry (admin)."""
    result = await session.execute(
        select(Timetable).where(
            Timetable.id == entry_id,
            Timetable.school_id == current_user.school_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry.is_active = False
    await session.commit()
    return {"message": "Entry deleted"}


# Class sections
@router.get("/classes")
async def get_class_sections(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get all class sections."""
    result = await session.execute(
        select(ClassSection).where(
            ClassSection.school_id == current_user.school_id,
            ClassSection.is_active == True,
        ).order_by(ClassSection.grade, ClassSection.section)
    )
    return result.scalars().all()


@router.post("/classes")
async def create_class_section(
    data: ClassSectionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new class section (admin)."""
    section = ClassSection(
        school_id=current_user.school_id,
        name=data.name,
        grade=data.grade,
        section=data.section,
        class_teacher_id=data.class_teacher_id,
        room=data.room,
    )
    session.add(section)
    await session.commit()
    await session.refresh(section)
    return {"id": section.id, "message": "Class section created"}
