"""Seed sample data for subjects, attendance, and results."""
import asyncio
import uuid
from datetime import date, timedelta
from sqlalchemy import select
from app.database import engine, get_async_session
from app.models.student import Student
from app.models.school import School
from app.models.academic import Subject, StudentSubject, AttendanceRecord, Result
from sqlmodel import SQLModel

async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async for session in get_async_session():
        # Get the school
        result = await session.execute(select(School).limit(1))
        school = result.scalar_one_or_none()
        if not school:
            print("No school found. Please run the initial setup first.")
            return

        # Get Rahul Sharma's student record
        result = await session.execute(
            select(Student).where(Student.admission_number == "SJPS-2026-001")
        )
        student = result.scalar_one_or_none()
        if not student:
            print("Student not found.")
            return

        print(f"Seeding data for student: {student.id}")

        # Create subjects
        subjects_data = [
            {"name": "Mathematics", "code": "MATH101", "credits": 4, "description": "Algebra, Geometry, and Calculus"},
            {"name": "Physics", "code": "PHY101", "credits": 4, "description": "Mechanics, Thermodynamics, and Optics"},
            {"name": "Chemistry", "code": "CHEM101", "credits": 4, "description": "Organic and Inorganic Chemistry"},
            {"name": "English", "code": "ENG101", "credits": 3, "description": "Literature and Grammar"},
            {"name": "Computer Science", "code": "CS101", "credits": 4, "description": "Programming and Data Structures"},
            {"name": "Biology", "code": "BIO101", "credits": 3, "description": "Cell Biology and Genetics"},
        ]

        created_subjects = []
        for subj_data in subjects_data:
            # Check if subject already exists
            result = await session.execute(
                select(Subject).where(Subject.code == subj_data["code"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                created_subjects.append(existing)
                continue

            subject = Subject(
                school_id=school.id,
                name=subj_data["name"],
                code=subj_data["code"],
                credits=subj_data["credits"],
                description=subj_data["description"],
            )
            session.add(subject)
            created_subjects.append(subject)

        await session.commit()

        # Refresh to get IDs
        for subj in created_subjects:
            await session.refresh(subj)

        print(f"Created {len(created_subjects)} subjects")

        # Assign subjects to student
        for subject in created_subjects:
            result = await session.execute(
                select(StudentSubject).where(
                    StudentSubject.student_id == student.id,
                    StudentSubject.subject_id == subject.id,
                )
            )
            if not result.scalar_one_or_none():
                student_subject = StudentSubject(
                    student_id=student.id,
                    subject_id=subject.id,
                    academic_year="2026-2027",
                )
                session.add(student_subject)

        await session.commit()
        print("Assigned subjects to student")

        # Create attendance records for the last 30 days
        today = date.today()
        attendance_statuses = ["present"] * 22 + ["absent"] * 4 + ["late"] * 3 + ["excused"] * 1

        for i in range(30):
            record_date = today - timedelta(days=i)
            # Skip weekends
            if record_date.weekday() >= 5:
                continue

            # Check if record exists
            result = await session.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.student_id == student.id,
                    AttendanceRecord.record_date == record_date,
                )
            )
            if result.scalar_one_or_none():
                continue

            status = attendance_statuses[i % len(attendance_statuses)]
            remarks = None
            if status == "absent":
                remarks = "Medical leave"
            elif status == "late":
                remarks = "Traffic delay"
            elif status == "excused":
                remarks = "Family event"

            attendance = AttendanceRecord(
                student_id=student.id,
                record_date=record_date,
                status=status,
                remarks=remarks,
            )
            session.add(attendance)

        await session.commit()
        print("Created attendance records")

        # Create exam results
        exams = [
            {"name": "Mid-Term Exam", "date": today - timedelta(days=45)},
            {"name": "Unit Test 1", "date": today - timedelta(days=60)},
        ]

        # Marks for each subject in each exam
        marks_data = {
            "Mathematics": [(85, "A"), (78, "B+")],
            "Physics": [(92, "A+"), (88, "A")],
            "Chemistry": [(76, "B+"), (72, "B")],
            "English": [(88, "A"), (85, "A")],
            "Computer Science": [(95, "A+"), (92, "A+")],
            "Biology": [(82, "A"), (79, "B+")],
        }

        for subject in created_subjects:
            for i, exam in enumerate(exams):
                # Check if result exists
                result = await session.execute(
                    select(Result).where(
                        Result.student_id == student.id,
                        Result.subject_id == subject.id,
                        Result.exam_name == exam["name"],
                    )
                )
                if result.scalar_one_or_none():
                    continue

                marks, grade = marks_data.get(subject.name, [(75, "B+"), (70, "B")])[i]

                exam_result = Result(
                    student_id=student.id,
                    subject_id=subject.id,
                    exam_name=exam["name"],
                    exam_date=exam["date"],
                    max_marks=100.0,
                    marks_obtained=float(marks),
                    grade=grade,
                    academic_year="2026-2027",
                )
                session.add(exam_result)

        await session.commit()
        print("Created exam results")

        print("\nSample data seeded successfully!")
        print(f"- {len(created_subjects)} subjects")
        print(f"- ~22 attendance records")
        print(f"- {len(exams) * len(created_subjects)} exam results")
        break

if __name__ == "__main__":
    asyncio.run(seed_data())
