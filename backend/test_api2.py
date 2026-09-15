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
        print(f"User school_id: {user.school_id}")
        print(f"  school_id.hex: {user.school_id.hex}")

        school_id_str = user.school_id.hex
        print(f"\nQuerying Timetable with school_id_str: {school_id_str}")

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
        print(f"Found {len(entries)} entries")

        if entries:
            entry = entries[0]
            print(f"\nFirst entry subject_id: {entry.subject_id}")
            # Get subject
            result = await session.execute(select(Subject).where(Subject.id == entry.subject_id))
            subject = result.scalar_one_or_none()
            print(f"Subject: {subject.name if subject else 'NOT FOUND'}")

        break

asyncio.run(test())
