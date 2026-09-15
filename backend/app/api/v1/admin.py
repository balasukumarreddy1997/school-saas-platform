import uuid
from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_active_user, get_password_hash
from app.database import get_async_session
from app.models.user import User, UserRole, RoleType
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.school import School
from app.models.academic import Subject, StudentSubject, AttendanceRecord, Result

router = APIRouter()


# Request/Response Models
class DashboardStats(BaseModel):
    total_students: int
    total_teachers: int
    total_subjects: int
    attendance_today: int
    pending_fees: int


class StudentCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    admission_number: str
    roll_number: Optional[str] = None
    gender: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None


class StudentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    admission_number: str
    roll_number: Optional[str]
    gender: Optional[str]
    parent_name: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class TeacherCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    employee_id: str
    department: Optional[str] = None
    qualification: Optional[str] = None
    is_class_teacher: bool = False


class TeacherResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    employee_id: str
    department: Optional[str]
    qualification: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    credits: int = 1


class SubjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str]
    credits: int
    is_active: bool

    class Config:
        from_attributes = True


async def verify_admin(session: AsyncSession, user: User) -> bool:
    result = await session.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role.in_([RoleType.MANAGEMENT.value, "admin", "management"]),
        )
    )
    return result.scalar_one_or_none() is not None


# Dashboard
@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DashboardStats:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get counts
    students_result = await session.execute(
        select(func.count(Student.id)).where(Student.school_id == current_user.school_id)
    )
    total_students = students_result.scalar() or 0

    teachers_result = await session.execute(
        select(func.count(Teacher.id)).where(Teacher.school_id == current_user.school_id)
    )
    total_teachers = teachers_result.scalar() or 0

    subjects_result = await session.execute(
        select(func.count(Subject.id)).where(Subject.school_id == current_user.school_id)
    )
    total_subjects = subjects_result.scalar() or 0

    # Today's attendance count
    today = DateType.today()
    attendance_result = await session.execute(
        select(func.count(AttendanceRecord.id)).where(AttendanceRecord.record_date == today)
    )
    attendance_today = attendance_result.scalar() or 0

    return DashboardStats(
        total_students=total_students,
        total_teachers=total_teachers,
        total_subjects=total_subjects,
        attendance_today=attendance_today,
        pending_fees=0,  # TODO: Implement fee tracking
    )


# Student Management
@router.get("/students", response_model=List[StudentResponse])
async def list_students(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[StudentResponse]:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(
        select(Student, User)
        .join(User, User.id == Student.user_id)
        .where(Student.school_id == current_user.school_id)
        .order_by(Student.admission_number)
    )
    rows = result.all()

    return [
        StudentResponse(
            id=student.id,
            user_id=student.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            admission_number=student.admission_number,
            roll_number=student.roll_number,
            gender=student.gender,
            parent_name=student.parent_name,
            is_active=user.is_active,
        )
        for student, user in rows
    ]


@router.post("/students", response_model=StudentResponse)
async def create_student(
    data: StudentCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> StudentResponse:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if email exists
    result = await session.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        school_id=current_user.school_id,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        is_active=True,
        is_verified=True,
    )
    session.add(user)

    # Create role
    role = UserRole(id=uuid.uuid4(), user_id=user_id, role=RoleType.STUDENT.value)
    session.add(role)

    # Create student profile
    student = Student(
        id=uuid.uuid4(),
        user_id=user_id,
        school_id=current_user.school_id,
        admission_number=data.admission_number,
        roll_number=data.roll_number,
        gender=data.gender,
        parent_name=data.parent_name,
        parent_phone=data.parent_phone,
    )
    session.add(student)

    await session.commit()
    await session.refresh(student)

    return StudentResponse(
        id=student.id,
        user_id=student.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        admission_number=student.admission_number,
        roll_number=student.roll_number,
        gender=student.gender,
        parent_name=student.parent_name,
        is_active=user.is_active,
    )


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Deactivate user instead of deleting
    result = await session.execute(select(User).where(User.id == student.user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_active = False
        session.add(user)

    await session.commit()
    return {"message": "Student deactivated"}


# Teacher Management
@router.get("/teachers", response_model=List[TeacherResponse])
async def list_teachers(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[TeacherResponse]:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(
        select(Teacher, User)
        .join(User, User.id == Teacher.user_id)
        .where(Teacher.school_id == current_user.school_id)
        .order_by(Teacher.employee_id)
    )
    rows = result.all()

    return [
        TeacherResponse(
            id=teacher.id,
            user_id=teacher.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            employee_id=teacher.employee_id,
            department=teacher.department,
            qualification=teacher.qualification,
            is_active=user.is_active,
        )
        for teacher, user in rows
    ]


@router.post("/teachers", response_model=TeacherResponse)
async def create_teacher(
    data: TeacherCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> TeacherResponse:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if email exists
    result = await session.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        school_id=current_user.school_id,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        is_active=True,
        is_verified=True,
    )
    session.add(user)

    # Create role
    role = UserRole(id=uuid.uuid4(), user_id=user_id, role=RoleType.TEACHER.value)
    session.add(role)

    # Create teacher profile
    teacher = Teacher(
        id=uuid.uuid4(),
        user_id=user_id,
        school_id=current_user.school_id,
        employee_id=data.employee_id,
        department=data.department,
        qualification=data.qualification,
        is_class_teacher=data.is_class_teacher,
    )
    session.add(teacher)

    await session.commit()
    await session.refresh(teacher)

    return TeacherResponse(
        id=teacher.id,
        user_id=teacher.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        employee_id=teacher.employee_id,
        department=teacher.department,
        qualification=teacher.qualification,
        is_active=user.is_active,
    )


@router.delete("/teachers/{teacher_id}")
async def delete_teacher(
    teacher_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    result = await session.execute(select(User).where(User.id == teacher.user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_active = False
        session.add(user)

    await session.commit()
    return {"message": "Teacher deactivated"}


# Subject Management
@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[SubjectResponse]:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(
        select(Subject)
        .where(Subject.school_id == current_user.school_id)
        .order_by(Subject.name)
    )
    subjects = result.scalars().all()

    return [
        SubjectResponse(
            id=s.id,
            name=s.name,
            code=s.code,
            description=s.description,
            credits=s.credits,
            is_active=s.is_active,
        )
        for s in subjects
    ]


@router.post("/subjects", response_model=SubjectResponse)
async def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SubjectResponse:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if code exists
    result = await session.execute(
        select(Subject).where(
            Subject.school_id == current_user.school_id,
            Subject.code == data.code,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subject code already exists")

    subject = Subject(
        id=uuid.uuid4(),
        school_id=current_user.school_id,
        name=data.name,
        code=data.code,
        description=data.description,
        credits=data.credits,
    )
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    return SubjectResponse(
        id=subject.id,
        name=subject.name,
        code=subject.code,
        description=subject.description,
        credits=subject.credits,
        is_active=subject.is_active,
    )


@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    subject.is_active = False
    session.add(subject)
    await session.commit()
    return {"message": "Subject deactivated"}
