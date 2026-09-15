import uuid
from datetime import date as DateType, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_active_user
from app.database import get_async_session
from app.models.user import User, UserRole, RoleType
from app.models.student import Student
from app.models.fee import FeeStructure, StudentFee, FeePayment

router = APIRouter()


# Request/Response Models
class FeeStructureCreate(BaseModel):
    name: str
    description: Optional[str] = None
    amount: float
    frequency: str  # monthly, quarterly, yearly, one_time
    academic_year: str
    due_day: int = 10


class FeeStructureResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    amount: float
    frequency: str
    academic_year: str
    due_day: int
    is_active: bool

    class Config:
        from_attributes = True


class StudentFeeResponse(BaseModel):
    id: uuid.UUID
    fee_name: str
    amount: float
    due_date: DateType
    status: str
    amount_paid: float
    balance: float

    class Config:
        from_attributes = True


class AssignFeeRequest(BaseModel):
    student_id: uuid.UUID
    fee_structure_id: uuid.UUID
    due_date: DateType
    amount: Optional[float] = None  # Override amount if needed


class RecordPaymentRequest(BaseModel):
    student_fee_id: uuid.UUID
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    remarks: Optional[str] = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    amount: float
    payment_date: DateType
    payment_method: str
    receipt_number: str
    transaction_id: Optional[str]

    class Config:
        from_attributes = True


class FeeSummary(BaseModel):
    total_fees: float
    total_paid: float
    total_pending: float
    overdue_count: int


async def verify_admin(session: AsyncSession, user: User) -> bool:
    result = await session.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role.in_([RoleType.MANAGEMENT.value, "admin", "management"]),
        )
    )
    return result.scalar_one_or_none() is not None


async def get_student_profile(session: AsyncSession, user: User) -> Optional[Student]:
    result = await session.execute(select(Student).where(Student.user_id == user.id))
    return result.scalar_one_or_none()


# Admin endpoints
@router.get("/structures", response_model=List[FeeStructureResponse])
async def list_fee_structures(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[FeeStructureResponse]:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(
        select(FeeStructure)
        .where(FeeStructure.school_id == current_user.school_id)
        .order_by(FeeStructure.name)
    )
    structures = result.scalars().all()

    return [
        FeeStructureResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            amount=s.amount,
            frequency=s.frequency,
            academic_year=s.academic_year,
            due_day=s.due_day,
            is_active=s.is_active,
        )
        for s in structures
    ]


@router.post("/structures", response_model=FeeStructureResponse)
async def create_fee_structure(
    data: FeeStructureCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> FeeStructureResponse:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    structure = FeeStructure(
        id=uuid.uuid4(),
        school_id=current_user.school_id,
        name=data.name,
        description=data.description,
        amount=data.amount,
        frequency=data.frequency,
        academic_year=data.academic_year,
        due_day=data.due_day,
    )
    session.add(structure)
    await session.commit()
    await session.refresh(structure)

    return FeeStructureResponse(
        id=structure.id,
        name=structure.name,
        description=structure.description,
        amount=structure.amount,
        frequency=structure.frequency,
        academic_year=structure.academic_year,
        due_day=structure.due_day,
        is_active=structure.is_active,
    )


@router.delete("/structures/{structure_id}")
async def delete_fee_structure(
    structure_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(select(FeeStructure).where(FeeStructure.id == structure_id))
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    structure.is_active = False
    session.add(structure)
    await session.commit()
    return {"message": "Fee structure deactivated"}


@router.post("/assign")
async def assign_fee_to_student(
    data: AssignFeeRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get fee structure
    result = await session.execute(
        select(FeeStructure).where(FeeStructure.id == data.fee_structure_id)
    )
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    # Create student fee
    student_fee = StudentFee(
        id=uuid.uuid4(),
        student_id=data.student_id,
        fee_structure_id=data.fee_structure_id,
        amount=data.amount or structure.amount,
        due_date=data.due_date,
        status="pending",
    )
    session.add(student_fee)
    await session.commit()

    return {"message": "Fee assigned successfully"}


@router.post("/assign-all")
async def assign_fee_to_all_students(
    fee_structure_id: uuid.UUID,
    due_date: DateType,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get fee structure
    result = await session.execute(
        select(FeeStructure).where(FeeStructure.id == fee_structure_id)
    )
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    # Get all students
    result = await session.execute(
        select(Student).where(Student.school_id == current_user.school_id)
    )
    students = result.scalars().all()

    count = 0
    for student in students:
        # Check if already assigned
        existing = await session.execute(
            select(StudentFee).where(
                StudentFee.student_id == student.id,
                StudentFee.fee_structure_id == fee_structure_id,
                StudentFee.due_date == due_date,
            )
        )
        if existing.scalar_one_or_none():
            continue

        student_fee = StudentFee(
            id=uuid.uuid4(),
            student_id=student.id,
            fee_structure_id=fee_structure_id,
            amount=structure.amount,
            due_date=due_date,
            status="pending",
        )
        session.add(student_fee)
        count += 1

    await session.commit()
    return {"message": f"Fee assigned to {count} students"}


@router.get("/all-students", response_model=List[dict])
async def get_all_student_fees(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(
        select(StudentFee, FeeStructure, Student, User)
        .join(FeeStructure, FeeStructure.id == StudentFee.fee_structure_id)
        .join(Student, Student.id == StudentFee.student_id)
        .join(User, User.id == Student.user_id)
        .where(FeeStructure.school_id == current_user.school_id)
        .order_by(StudentFee.due_date.desc())
    )
    rows = result.all()

    return [
        {
            "id": str(sf.id),
            "student_name": f"{user.first_name} {user.last_name}",
            "admission_number": student.admission_number,
            "fee_name": structure.name,
            "amount": sf.amount,
            "due_date": str(sf.due_date),
            "status": sf.status,
            "amount_paid": sf.amount_paid,
            "balance": sf.amount - sf.amount_paid,
        }
        for sf, structure, student, user in rows
    ]


@router.post("/payment")
async def record_payment(
    data: RecordPaymentRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get student fee
    result = await session.execute(
        select(StudentFee).where(StudentFee.id == data.student_fee_id)
    )
    student_fee = result.scalar_one_or_none()
    if not student_fee:
        raise HTTPException(status_code=404, detail="Student fee not found")

    # Generate receipt number
    receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"

    # Create payment record
    payment = FeePayment(
        id=uuid.uuid4(),
        student_fee_id=data.student_fee_id,
        amount=data.amount,
        payment_date=DateType.today(),
        payment_method=data.payment_method,
        transaction_id=data.transaction_id,
        receipt_number=receipt_number,
        collected_by=current_user.id,
        remarks=data.remarks,
    )
    session.add(payment)

    # Update student fee
    student_fee.amount_paid += data.amount
    if student_fee.amount_paid >= student_fee.amount:
        student_fee.status = "paid"
        student_fee.paid_date = DateType.today()
    elif student_fee.amount_paid > 0:
        student_fee.status = "partial"
    student_fee.updated_at = datetime.utcnow()
    session.add(student_fee)

    await session.commit()

    return {"message": "Payment recorded", "receipt_number": receipt_number}


@router.get("/summary", response_model=FeeSummary)
async def get_fee_summary(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> FeeSummary:
    if not await verify_admin(session, current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await session.execute(
        select(
            func.sum(StudentFee.amount).label("total"),
            func.sum(StudentFee.amount_paid).label("paid"),
        )
        .join(FeeStructure, FeeStructure.id == StudentFee.fee_structure_id)
        .where(FeeStructure.school_id == current_user.school_id)
    )
    row = result.one()
    total = row.total or 0
    paid = row.paid or 0

    # Count overdue
    today = DateType.today()
    overdue_result = await session.execute(
        select(func.count(StudentFee.id))
        .join(FeeStructure, FeeStructure.id == StudentFee.fee_structure_id)
        .where(
            FeeStructure.school_id == current_user.school_id,
            StudentFee.due_date < today,
            StudentFee.status.in_(["pending", "partial"]),
        )
    )
    overdue_count = overdue_result.scalar() or 0

    return FeeSummary(
        total_fees=total,
        total_paid=paid,
        total_pending=total - paid,
        overdue_count=overdue_count,
    )


# Student endpoints
@router.get("/my-fees", response_model=List[StudentFeeResponse])
async def get_my_fees(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[StudentFeeResponse]:
    student = await get_student_profile(session, current_user)
    if not student:
        raise HTTPException(status_code=403, detail="Student access required")

    result = await session.execute(
        select(StudentFee, FeeStructure)
        .join(FeeStructure, FeeStructure.id == StudentFee.fee_structure_id)
        .where(StudentFee.student_id == student.id)
        .order_by(StudentFee.due_date.desc())
    )
    rows = result.all()

    return [
        StudentFeeResponse(
            id=sf.id,
            fee_name=structure.name,
            amount=sf.amount,
            due_date=sf.due_date,
            status=sf.status,
            amount_paid=sf.amount_paid,
            balance=sf.amount - sf.amount_paid,
        )
        for sf, structure in rows
    ]


@router.get("/my-payments", response_model=List[PaymentResponse])
async def get_my_payments(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[PaymentResponse]:
    student = await get_student_profile(session, current_user)
    if not student:
        raise HTTPException(status_code=403, detail="Student access required")

    result = await session.execute(
        select(FeePayment)
        .join(StudentFee, StudentFee.id == FeePayment.student_fee_id)
        .where(StudentFee.student_id == student.id)
        .order_by(FeePayment.payment_date.desc())
    )
    payments = result.scalars().all()

    return [
        PaymentResponse(
            id=p.id,
            amount=p.amount,
            payment_date=p.payment_date,
            payment_method=p.payment_method,
            receipt_number=p.receipt_number,
            transaction_id=p.transaction_id,
        )
        for p in payments
    ]
