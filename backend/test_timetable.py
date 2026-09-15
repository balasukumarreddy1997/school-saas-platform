import asyncio
from sqlalchemy import select, and_
from app.database import get_async_session
from app.models.user import User
from app.models.student import Student
from app.models.timetable import Timetable
from app.models.academic import Subject

async def test():
    async for session in get_async_session():
        # Get student user
        result = await session.execute(select(User).where(User.email == 'student'))
        user = result.scalar_one_or_none()
        print(f"User: {user.email}, ID: {user.id}, school_id: {user.school_id}")

        user_id_str = str(user.id).replace('-', '')
        school_id_str = str(user.school_id).replace('-', '')
        print(f"User ID (str): {user_id_str}")
        print(f"School ID (str): {school_id_str}")

        # Get student
        result = await session.execute(select(Student).where(Student.user_id == user_id_str))
        student = result.scalar_one_or_none()
        print(f"Student found: {student is not None}")

        # Get timetable
        result = await session.execute(
            select(Timetable).where(
                and_(
                    Timetable.school_id == school_id_str,
                    Timetable.class_name == "10-A",
                    Timetable.is_active == True,
                )
            ).order_by(Timetable.day_of_week, Timetable.start_time)
        )
        entries = result.scalars().all()
        print(f"Found {len(entries)} timetable entries")

        for entry in entries[:3]:
            print(f"  - Day {entry.day_of_week}: {entry.start_time}-{entry.end_time}, subject_id={entry.subject_id}")
            # Get subject
            sub_result = await session.execute(select(Subject).where(Subject.id == entry.subject_id))
            subject = sub_result.scalar_one_or_none()
            print(f"    Subject: {subject.name if subject else 'NOT FOUND'}")

        break

asyncio.run(test())
