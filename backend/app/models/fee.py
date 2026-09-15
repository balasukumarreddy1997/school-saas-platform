import uuid
from datetime import date as DateType, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.base import generate_uuid


class FeeStructure(SQLModel, table=True):
    __tablename__ = "fee_structures"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    school_id: uuid.UUID = Field(foreign_key="schools.id", nullable=False)
    name: str = Field(max_length=100, nullable=False)  # e.g., "Tuition Fee", "Transport Fee"
    description: Optional[str] = Field(default=None, max_length=500)
    amount: float = Field(nullable=False)
    frequency: str = Field(max_length=20, nullable=False)  # monthly, quarterly, yearly, one_time
    academic_year: str = Field(max_length=20, nullable=False)
    due_day: int = Field(default=10)  # Day of month/quarter when fee is due
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class StudentFee(SQLModel, table=True):
    __tablename__ = "student_fees"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", nullable=False)
    fee_structure_id: uuid.UUID = Field(foreign_key="fee_structures.id", nullable=False)
    amount: float = Field(nullable=False)
    due_date: DateType = Field(nullable=False)
    status: str = Field(max_length=20, default="pending")  # pending, paid, overdue, partial
    amount_paid: float = Field(default=0.0)
    paid_date: Optional[DateType] = Field(default=None)
    remarks: Optional[str] = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class FeePayment(SQLModel, table=True):
    __tablename__ = "fee_payments"

    id: uuid.UUID = Field(default_factory=generate_uuid, primary_key=True)
    student_fee_id: uuid.UUID = Field(foreign_key="student_fees.id", nullable=False)
    amount: float = Field(nullable=False)
    payment_date: DateType = Field(nullable=False)
    payment_method: str = Field(max_length=50, nullable=False)  # cash, upi, card, bank_transfer
    transaction_id: Optional[str] = Field(default=None, max_length=100)
    receipt_number: str = Field(max_length=50, nullable=False)
    collected_by: Optional[uuid.UUID] = Field(foreign_key="users.id", default=None)
    remarks: Optional[str] = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
