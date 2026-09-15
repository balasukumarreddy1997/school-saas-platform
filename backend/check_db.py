import aiosqlite
import asyncio

async def check():
    async with aiosqlite.connect("school_saas.db") as db:
        cursor = await db.execute("SELECT id, user_id FROM students LIMIT 1")
        row = await cursor.fetchone()
        print("Student: id=%s, user_id=%s" % (row[0], row[1]))

        cursor = await db.execute("SELECT id FROM users WHERE email='student'")
        row = await cursor.fetchone()
        print("User id: %s" % row[0])

asyncio.run(check())
