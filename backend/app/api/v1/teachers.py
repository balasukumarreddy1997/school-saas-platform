import uuid
from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_active_user
from app.database import get_async_session
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.user import User, UserRole, RoleType
from app.models.academic import Subject, StudentSubject, AttendanceRecord, Result

router = APIRouter()


class TeacherProfile(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    employee_id: str
    department: Optional[str]
    qualification: Optional[str]
    date_of_joining: Optional[str]
    is_class_teacher: bool

    class Config:
        from_attributes = True


class SubjectWithStudents(BaseModel):
    subject_id: uuid.UUID
    subject_name: str
    subject_code: str
    student_count: int


class TeacherDashboard(BaseModel):
    profile: TeacherProfile
    subjects_teaching: List[SubjectWithStudents]
    total_students: int
    pending_attendance_today: bool


class StudentInfo(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    first_name: str
    last_name: str
    admission_number: str
    roll_number: Optional[str]


class MarkAttendanceRequest(BaseModel):
    student_id: uuid.UUID
    record_date: DateType
    status: str  # present, absent, late, excused
    remarks: Optional[str] = None


class EnterResultRequest(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    exam_name: str
    exam_date: Optional[DateType] = None
    max_marks: float = 100.0
    marks_obtained: float
    grade: Optional[str] = None
    academic_year: str


async def get_teacher_role(session: AsyncSession, user: User) -> Optional[UserRole]:
    result = await session.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role == RoleType.TEACHER,
        )
    )
    return result.scalar_one_or_none()


async def get_teacher_profile(session: AsyncSession, user: User) -> Optional[Teacher]:
    result = await session.execute(select(Teacher).where(Teacher.user_id == user.id))
    return result.scalar_one_or_none()


@router.get("/me", response_model=TeacherProfile)
async def get_current_teacher(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> TeacherProfile:
    role = await get_teacher_role(session, current_user)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a teacher",
        )

    teacher = await get_teacher_profile(session, current_user)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    return TeacherProfile(
        id=teacher.id,
        user_id=teacher.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        employee_id=teacher.employee_id,
        department=teacher.department,
        qualification=teacher.qualification,
        date_of_joining=str(teacher.date_of_joining) if teacher.date_of_joining else None,
        is_class_teacher=teacher.is_class_teacher,
    )


@router.get("/me/dashboard", response_model=TeacherDashboard)
async def get_teacher_dashboard(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> TeacherDashboard:
    role = await get_teacher_role(session, current_user)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a teacher",
        )

    teacher = await get_teacher_profile(session, current_user)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    profile = TeacherProfile(
        id=teacher.id,
        user_id=teacher.user_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        employee_id=teacher.employee_id,
        department=teacher.department,
        qualification=teacher.qualification,
        date_of_joining=str(teacher.date_of_joining) if teacher.date_of_joining else None,
        is_class_teacher=teacher.is_class_teacher,
    )

    # Get subjects this teacher teaches
    result = await session.execute(
        select(Subject, func.count(StudentSubject.student_id).label("student_count"))
        .outerjoin(StudentSubject, StudentSubject.subject_id == Subject.id)
        .where(StudentSubject.teacher_id == teacher.id)
        .group_by(Subject.id)
    )
    subjects_rows = result.all()

    subjects_teaching = []
    total_students = 0
    for subject, count in subjects_rows:
        subjects_teaching.append(SubjectWithStudents(
            subject_id=subject.id,
            subject_name=subject.name,
            subject_code=subject.code,
            student_count=count,
        ))
        total_students += count

    # Check if attendance marked today
    today = DateType.today()
    result = await session.execute(
        select(AttendanceRecord)
        .where(AttendanceRecord.record_date == today)
        .where(AttendanceRecord.recorded_by == current_user.id)
        .limit(1)
    )
    attendance_marked = result.scalar_one_or_none() is not None

    return TeacherDashboard(
        profile=profile,
        subjects_teaching=subjects_teaching,
        total_students=total_students,
        pending_attendance_today=not attendance_marked,
    )


@router.get("/me/students", response_model=List[StudentInfo])
async def get_my_students(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    subject_id: Optional[uuid.UUID] = None,
) -> List[StudentInfo]:
    role = await get_teacher_role(session, current_user)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a teacher",
        )

    teacher = await get_teacher_profile(session, current_user)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    query = (
        select(Student, User)
        .join(StudentSubject, StudentSubject.student_id == Student.id)
        .join(User, User.id == Student.user_id)
        .where(StudentSubject.teacher_id == teacher.id)
    )

    if subject_id:
        query = query.where(StudentSubject.subject_id == subject_id)

    query = query.distinct()
    result = await session.execute(query)
    rows = result.all()

    students = []
    for student, user in rows:
        students.append(StudentInfo(
            id=student.id,
            user_id=student.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            admission_number=student.admission_number,
            roll_number=student.roll_number,
        ))

    return students


@router.post("/attendance/mark")
async def mark_attendance(
    request: MarkAttendanceRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    role = await get_teacher_role(session, current_user)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a teacher",
        )

    # Check if attendance already exists for this student on this date
    result = await session.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.student_id == request.student_id,
            AttendanceRecord.record_date == request.record_date,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.status = request.status
        existing.remarks = request.remarks
        existing.recorded_by = current_user.id
        session.add(existing)
    else:
        # Create new
        attendance = AttendanceRecord(
            student_id=request.student_id,
            record_date=request.record_date,
            status=request.status,
            remarks=request.remarks,
            recorded_by=current_user.id,
        )
        session.add(attendance)

    await session.commit()
    return {"message": "Attendance marked successfully"}


@router.post("/attendance/mark-bulk")
async def mark_attendance_bulk(
    requests: List[MarkAttendanceRequest],
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    role = await get_teacher_role(session, current_user)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a teacher",
        )

    for req in requests:
        result = await session.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.student_id == req.student_id,
                AttendanceRecord.record_date == req.record_date,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = req.status
            existing.remarks = req.remarks
            existing.recorded_by = current_user.id
            session.add(existing)
        else:
            attendance = AttendanceRecord(
                student_id=req.student_id,
                record_date=req.record_date,
                status=req.status,
                remarks=req.remarks,
                recorded_by=current_user.id,
            )
            session.add(attendance)

    await session.commit()
    return {"message": f"Attendance marked for {len(requests)} students"}


@router.post("/results/enter")
async def enter_result(
    request: EnterResultRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    role = await get_teacher_role(session, current_user)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a teacher",
        )

    # Check if result already exists
    result = await session.execute(
        select(Result).where(
            Result.student_id == request.student_id,
            Result.subject_id == request.subject_id,
            Result.exam_name == request.exam_name,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.marks_obtained = request.marks_obtained
        existing.max_marks = request.max_marks
        existing.grade = request.grade
        existing.exam_date = request.exam_date
        session.add(existing)
    else:
        new_result = Result(
            student_id=request.student_id,
            subject_id=request.subject_id,
            exam_name=request.exam_name,
            exam_date=request.exam_date,
            max_marks=request.max_marks,
            marks_obtained=request.marks_obtained,
            grade=request.grade,
            academic_year=request.academic_year,
        )
        session.add(new_result)

    await session.commit()
    return {"message": "Result entered successfully"}
