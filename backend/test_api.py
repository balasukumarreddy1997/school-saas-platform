import asyncio
from sqlalchemy import select
from app.database import get_async_session
from app.models.user import User
from app.models.student import Student

async def test():
    async for session in get_async_session():
        # Get student user
        result = await session.execute(select(User).where(User.email == 'student'))
        user = result.scalar_one_or_none()
        print(f"User: {user.email}")
        print(f"  id type: {type(user.id)}, value: {user.id}")
        print(f"  school_id type: {type(user.school_id)}, value: {user.school_id}")

        # Try to get student with UUID directly
        print(f"\nQuerying Student with user.id directly...")
        result = await session.execute(select(Student).where(Student.user_id == user.id))
        student = result.scalar_one_or_none()
        print(f"Student found: {student is not None}")
        if student:
            print(f"  Student id: {student.id}")

        break

asyncio.run(test())
