import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_active_user
from app.database import get_async_session
from app.models.academic import Subject, StudentSubject
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User, UserRole, RoleType

router = APIRouter()


class SubjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str]
    credits: int
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True


async def get_student_profile(session: AsyncSession, user: User) -> Optional[Student]:
    result = await session.execute(select(Student).where(Student.user_id == user.id))
    return result.scalar_one_or_none()


@router.get("/my-subjects", response_model=List[SubjectResponse])
async def get_my_subjects(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[SubjectResponse]:
    student = await get_student_profile(session, current_user)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a student",
        )

    result = await session.execute(
        select(Subject, StudentSubject, Teacher)
        .outerjoin(StudentSubject, StudentSubject.subject_id == Subject.id)
        .outerjoin(Teacher, Teacher.id == StudentSubject.teacher_id)
        .where(StudentSubject.student_id == student.id)
        .where(Subject.is_active == True)
    )
    rows = result.all()

    subjects = []
    for subject, student_subject, teacher in rows:
        teacher_name = None
        if teacher:
            teacher_user = await session.execute(
                select(User).where(User.id == teacher.user_id)
            )
            teacher_user = teacher_user.scalar_one_or_none()
            if teacher_user:
                teacher_name = f"{teacher_user.first_name} {teacher_user.last_name}"

        subjects.append(SubjectResponse(
            id=subject.id,
            name=subject.name,
            code=subject.code,
            description=subject.description,
            credits=subject.credits,
            teacher_name=teacher_name,
        ))

    return subjects
