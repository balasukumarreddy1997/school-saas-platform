"""Create teacher profile and assign subjects."""
import asyncio
import uuid
from sqlalchemy import select
from app.database import engine, get_async_session
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.models.school import School
from app.models.academic import Subject, StudentSubject
from sqlmodel import SQLModel

async def seed_teacher_data():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async for session in get_async_session():
        # Get the teacher user
        result = await session.execute(
            select(User).where(User.email == "teacher@stjosephs.edu")
        )
        teacher_user = result.scalar_one_or_none()
        if not teacher_user:
            print("Teacher user not found.")
            return

        print(f"Found teacher user: {teacher_user.email}")

        # Get the school
        result = await session.execute(select(School).limit(1))
        school = result.scalar_one_or_none()
        if not school:
            print("No school found.")
            return

        # Check if teacher profile exists, create if not
        result = await session.execute(
            select(Teacher).where(Teacher.user_id == teacher_user.id)
        )
        teacher = result.scalar_one_or_none()

        if not teacher:
            teacher = Teacher(
                id=uuid.uuid4(),
                user_id=teacher_user.id,
                school_id=school.id,
                employee_id="SJPS-T-001",
                department="Science & Mathematics",
                qualification="M.Sc., B.Ed.",
                is_class_teacher=True,
            )
            session.add(teacher)
            await session.commit()
            await session.refresh(teacher)
            print(f"Created teacher profile: {teacher.employee_id}")
        else:
            print(f"Teacher profile exists: {teacher.employee_id}")

        # Get all subjects
        result = await session.execute(select(Subject))
        subjects = result.scalars().all()

        if not subjects:
            print("No subjects found. Run seed_sample_data.py first.")
            return

        # Get the student
        result = await session.execute(
            select(Student).where(Student.admission_number == "SJPS-2026-001")
        )
        student = result.scalar_one_or_none()
        if not student:
            print("Student not found.")
            return

        # Assign teacher to student's subjects
        count = 0
        for subject in subjects:
            result = await session.execute(
                select(StudentSubject).where(
                    StudentSubject.student_id == student.id,
                    StudentSubject.subject_id == subject.id,
                )
            )
            student_subject = result.scalar_one_or_none()

            if student_subject:
                # Update teacher assignment
                student_subject.teacher_id = teacher.id
                session.add(student_subject)
                count += 1
                print(f"Assigned teacher to {subject.name}")

        await session.commit()
        print(f"\nTeacher data seeded successfully!")
        print(f"Teacher assigned to {count} subjects")
        break

if __name__ == "__main__":
    asyncio.run(seed_teacher_data())
