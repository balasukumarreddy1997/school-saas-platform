"""Seed sample fee data."""
import asyncio
import uuid
from datetime import date, timedelta
from sqlalchemy import select
from app.database import engine, get_async_session
from app.models.student import Student
from app.models.school import School
from app.models.fee import FeeStructure, StudentFee
from sqlmodel import SQLModel

async def seed_fee_data():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async for session in get_async_session():
        # Get the school
        result = await session.execute(select(School).limit(1))
        school = result.scalar_one_or_none()
        if not school:
            print("No school found.")
            return

        print(f"Found school: {school.name}")

        # Create fee structures
        fee_structures = [
            {"name": "Tuition Fee", "amount": 5000, "frequency": "monthly", "description": "Monthly tuition fee"},
            {"name": "Transport Fee", "amount": 2000, "frequency": "monthly", "description": "School bus transport"},
            {"name": "Lab Fee", "amount": 3000, "frequency": "quarterly", "description": "Science lab consumables"},
            {"name": "Annual Fee", "amount": 10000, "frequency": "yearly", "description": "Annual charges"},
        ]

        created_structures = []
        for fs_data in fee_structures:
            # Check if exists
            result = await session.execute(
                select(FeeStructure).where(
                    FeeStructure.school_id == school.id,
                    FeeStructure.name == fs_data["name"],
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                created_structures.append(existing)
                continue

            structure = FeeStructure(
                id=uuid.uuid4(),
                school_id=school.id,
                name=fs_data["name"],
                amount=fs_data["amount"],
                frequency=fs_data["frequency"],
                description=fs_data["description"],
                academic_year="2026-2027",
            )
            session.add(structure)
            created_structures.append(structure)

        await session.commit()

        # Refresh to get IDs
        for s in created_structures:
            await session.refresh(s)

        print(f"Created {len(created_structures)} fee structures")

        # Get the student
        result = await session.execute(
            select(Student).where(Student.admission_number == "SJPS-2026-001")
        )
        student = result.scalar_one_or_none()
        if not student:
            print("Student not found.")
            return

        # Assign fees to student
        today = date.today()
        count = 0

        for structure in created_structures:
            # Create a fee due this month
            due_date = date(today.year, today.month, 10)

            # Check if exists
            result = await session.execute(
                select(StudentFee).where(
                    StudentFee.student_id == student.id,
                    StudentFee.fee_structure_id == structure.id,
                    StudentFee.due_date == due_date,
                )
            )
            if result.scalar_one_or_none():
                continue

            # Set some as paid, some as partial, some as pending
            if structure.name == "Tuition Fee":
                status = "paid"
                amount_paid = structure.amount
            elif structure.name == "Transport Fee":
                status = "partial"
                amount_paid = 1000
            else:
                status = "pending"
                amount_paid = 0

            student_fee = StudentFee(
                id=uuid.uuid4(),
                student_id=student.id,
                fee_structure_id=structure.id,
                amount=structure.amount,
                due_date=due_date,
                status=status,
                amount_paid=amount_paid,
            )
            session.add(student_fee)
            count += 1

        await session.commit()
        print(f"Assigned {count} fees to student")
        print("\nFee data seeded successfully!")
        break

if __name__ == "__main__":
    asyncio.run(seed_fee_data())
