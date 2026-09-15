import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect("school_saas.db") as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, school_id FROM timetables LIMIT 3")
        rows = await cursor.fetchall()
        for row in rows:
            print("Timetable school_id:", row["school_id"])

        cursor = await db.execute("SELECT id, school_id FROM users WHERE email = 'student'")
        user = await cursor.fetchone()
        print("User school_id:", user["school_id"])

asyncio.run(check())
