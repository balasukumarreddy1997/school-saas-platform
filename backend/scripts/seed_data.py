"""
Seed script to create initial test data.
Run with: python -m scripts.seed_data
"""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import settings
from app.models.school import School
from app.models.user import User, UserRole, RoleType
from app.models.student import Student

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
PASSWORD_HASH = pwd_context.hash("password123")


async def seed_database():
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if school already exists
        from sqlalchemy import select
        result = await session.execute(select(School).where(School.code == "SJPS"))
        existing_school = result.scalar_one_or_none()

        if existing_school:
            print("Seed data already exists. Skipping...")
            return

        # Create school
        school_id = uuid.uuid4()
        school = School(
            id=school_id,
            name="St Joseph's Public School",
            code="SJPS",
            address="123 Education Lane, Knowledge City",
            contact_email="admin@stjosephs.edu",
            contact_phone="+91-9876543210",
            settings={"academic_year": "2026-2027"},
            is_active=True,
        )
        session.add(school)
        print(f"Created school: {school.name} (ID: {school_id})")

        # Create student user
        student_user_id = uuid.uuid4()
        student_user = User(
            id=student_user_id,
            school_id=school_id,
            email="rahul.sharma@stjosephs.edu",
            hashed_password=PASSWORD_HASH,
            first_name="Rahul",
            last_name="Sharma",
            phone="+91-9876543211",
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        session.add(student_user)
        print(f"Created user: {student_user.email}")

        # Create student role
        student_role = UserRole(
            id=uuid.uuid4(),
            user_id=student_user_id,
            role=RoleType.STUDENT,
        )
        session.add(student_role)

        # Create student profile
        student = Student(
            id=uuid.uuid4(),
            user_id=student_user_id,
            school_id=school_id,
            admission_number="SJPS-2026-001",
            roll_number="15",
            date_of_birth=None,
            gender="Male",
            parent_name="Mr. Sharma",
            parent_phone="+91-9876543212",
            parent_email="parent.sharma@email.com",
            address="456 Student Street, Knowledge City",
        )
        session.add(student)
        print(f"Created student profile: {student.admission_number}")

        # Create management user
        mgmt_user_id = uuid.uuid4()
        mgmt_user = User(
            id=mgmt_user_id,
            school_id=school_id,
            email="admin@stjosephs.edu",
            hashed_password=PASSWORD_HASH,
            first_name="Admin",
            last_name="User",
            phone="+91-9876543213",
            is_active=True,
            is_superuser=True,
            is_verified=True,
        )
        session.add(mgmt_user)

        mgmt_role = UserRole(
            id=uuid.uuid4(),
            user_id=mgmt_user_id,
            role=RoleType.MANAGEMENT,
        )
        session.add(mgmt_role)
        print(f"Created management user: {mgmt_user.email}")

        # Create teacher user
        teacher_user_id = uuid.uuid4()
        teacher_user = User(
            id=teacher_user_id,
            school_id=school_id,
            email="teacher@stjosephs.edu",
            hashed_password=PASSWORD_HASH,
            first_name="Priya",
            last_name="Iyer",
            phone="+91-9876543214",
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        session.add(teacher_user)

        teacher_role = UserRole(
            id=uuid.uuid4(),
            user_id=teacher_user_id,
            role=RoleType.TEACHER,
        )
        session.add(teacher_role)
        print(f"Created teacher user: {teacher_user.email}")

        await session.commit()
        print("\n" + "="*50)
        print("SEED DATA CREATED SUCCESSFULLY!")
        print("="*50)
        print("\nTest Accounts:")
        print("-"*50)
        print("Student:    rahul.sharma@stjosephs.edu / password123")
        print("Teacher:    teacher@stjosephs.edu / password123")
        print("Management: admin@stjosephs.edu / password123")
        print("-"*50)


if __name__ == "__main__":
    asyncio.run(seed_database())
