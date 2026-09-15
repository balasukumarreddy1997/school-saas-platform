import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_active_user
from app.database import get_async_session
from app.models.academic import Result, Subject
from app.models.student import Student
from app.models.user import User

router = APIRouter()


class ResultRecord(BaseModel):
    id: uuid.UUID
    subject_name: str
    subject_code: str
    exam_name: str
    exam_date: Optional[date]
    max_marks: float
    marks_obtained: float
    grade: Optional[str]
    percentage: float
    remarks: Optional[str]

    class Config:
        from_attributes = True


class ResultsSummary(BaseModel):
    total_exams: int
    average_percentage: float
    best_subject: Optional[str]
    subjects_passed: int
    subjects_failed: int


class ResultsResponse(BaseModel):
    summary: ResultsSummary
    results: List[ResultRecord]


async def get_student_profile(session: AsyncSession, user: User) -> Optional[Student]:
    result = await session.execute(select(Student).where(Student.user_id == user.id))
    return result.scalar_one_or_none()


@router.get("/my-results", response_model=ResultsResponse)
async def get_my_results(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    academic_year: Optional[str] = Query(None),
    exam_name: Optional[str] = Query(None),
) -> ResultsResponse:
    student = await get_student_profile(session, current_user)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a student",
        )

    query = (
        select(Result, Subject)
        .join(Subject, Subject.id == Result.subject_id)
        .where(Result.student_id == student.id)
    )

    if academic_year:
        query = query.where(Result.academic_year == academic_year)
    if exam_name:
        query = query.where(Result.exam_name == exam_name)

    query = query.order_by(Result.exam_date.desc())
    db_result = await session.execute(query)
    rows = db_result.all()

    results = []
    percentages = []
    best_pct = 0
    best_subject = None
    passed = 0
    failed = 0

    for result, subject in rows:
        pct = (result.marks_obtained / result.max_marks * 100) if result.max_marks > 0 else 0
        percentages.append(pct)

        if pct > best_pct:
            best_pct = pct
            best_subject = subject.name

        if pct >= 40:
            passed += 1
        else:
            failed += 1

        results.append(ResultRecord(
            id=result.id,
            subject_name=subject.name,
            subject_code=subject.code,
            exam_name=result.exam_name,
            exam_date=result.exam_date,
            max_marks=result.max_marks,
            marks_obtained=result.marks_obtained,
            grade=result.grade,
            percentage=round(pct, 1),
            remarks=result.remarks,
        ))

    avg_pct = sum(percentages) / len(percentages) if percentages else 0.0

    return ResultsResponse(
        summary=ResultsSummary(
            total_exams=len(results),
            average_percentage=round(avg_pct, 1),
            best_subject=best_subject,
            subjects_passed=passed,
            subjects_failed=failed,
        ),
        results=results,
    )
