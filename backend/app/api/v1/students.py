import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_active_user
from app.database import get_async_session
from app.models.student import Student
from app.models.user import User, UserRole, RoleType

router = APIRouter()


class StudentProfile(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    admission_number: str
    roll_number: Optional[str]
    date_of_birth: Optional[str]
    gender: Optional[str]
    parent_name: Optional[str]
    parent_phone: Optional[str]

    class Config:
        from_attributes = True


class AttendanceData(BaseModel):
    total_days: int
    present: int
    absent: int
    percentage: float


class DashboardResponse(BaseModel):
    student: StudentProfile
    attendance: AttendanceData
    recent_results: List[dict]
    announcements: List[dict]


async def get_student_role(
    session: AsyncSession,
    user: User,
) -> Optional[UserRole]:
    result = await session.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role == RoleType.STUDENT,
        )
    )
    return result.scalar_one_or_none()


async def get_student_profile(
    session: AsyncSession,
    user: User,
) -> Optional[Student]:
    result = await session.execute(
        select(Student).where(Student.user_id == user.id)
    )
    return result.scalar_one_or_none()


@router.get("/me", response_model=StudentProfile)
async def get_current_student(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> StudentProfile:
    role = await get_student_role(session, current_user)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a student",
        )

    student = await get_student_profile(session, current_user)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    return StudentProfile(
        id=student.id,
        user_id=student.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        admission_number=student.admission_number,
        roll_number=student.roll_number,
        date_of_birth=str(student.date_of_birth) if student.date_of_birth else None,
        gender=student.gender,
        parent_name=student.parent_name,
        parent_phone=student.parent_phone,
    )


@router.get("/me/dashboard", response_model=DashboardResponse)
async def get_student_dashboard(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DashboardResponse:
    role = await get_student_role(session, current_user)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a student",
        )

    student = await get_student_profile(session, current_user)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    profile = StudentProfile(
        id=student.id,
        user_id=student.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        admission_number=student.admission_number,
        roll_number=student.roll_number,
        date_of_birth=str(student.date_of_birth) if student.date_of_birth else None,
        gender=student.gender,
        parent_name=student.parent_name,
        parent_phone=student.parent_phone,
    )

    return DashboardResponse(
        student=profile,
        attendance=AttendanceData(
            total_days=0,
            present=0,
            absent=0,
            percentage=0.0,
        ),
        recent_results=[],
        announcements=[],
    )
