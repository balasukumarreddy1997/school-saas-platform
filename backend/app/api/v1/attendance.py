import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_active_user
from app.database import get_async_session
from app.models.academic import AttendanceRecord
from app.models.student import Student
from app.models.user import User

router = APIRouter()


class AttendanceRecordResponse(BaseModel):
    id: uuid.UUID
    record_date: date
    status: str
    remarks: Optional[str]

    class Config:
        from_attributes = True


class AttendanceSummary(BaseModel):
    total_days: int
    present: int
    absent: int
    late: int
    excused: int
    percentage: float


class AttendanceResponse(BaseModel):
    summary: AttendanceSummary
    records: List[AttendanceRecordResponse]


async def get_student_profile(session: AsyncSession, user: User) -> Optional[Student]:
    result = await session.execute(select(Student).where(Student.user_id == user.id))
    return result.scalar_one_or_none()


@router.get("/my-attendance", response_model=AttendanceResponse)
async def get_my_attendance(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2030),
) -> AttendanceResponse:
    student = await get_student_profile(session, current_user)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a student",
        )

    query = select(AttendanceRecord).where(AttendanceRecord.student_id == student.id)

    if month and year:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        query = query.where(AttendanceRecord.record_date >= start_date, AttendanceRecord.record_date < end_date)

    query = query.order_by(AttendanceRecord.record_date.desc())
    result = await session.execute(query)
    records = result.scalars().all()

    present = sum(1 for r in records if r.status == "present")
    absent = sum(1 for r in records if r.status == "absent")
    late = sum(1 for r in records if r.status == "late")
    excused = sum(1 for r in records if r.status == "excused")
    total = len(records)
    percentage = (present / total * 100) if total > 0 else 0.0

    return AttendanceResponse(
        summary=AttendanceSummary(
            total_days=total,
            present=present,
            absent=absent,
            late=late,
            excused=excused,
            percentage=round(percentage, 1),
        ),
        records=[
            AttendanceRecordResponse(
                id=r.id,
                record_date=r.record_date,
                status=r.status,
                remarks=r.remarks,
            )
            for r in records
        ],
    )
