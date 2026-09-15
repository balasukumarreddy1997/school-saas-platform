"""Seed sample announcements."""
import asyncio
import uuid
import aiosqlite
from datetime import datetime

async def seed_announcements():
    async with aiosqlite.connect("school_saas.db") as db:
        db.row_factory = aiosqlite.Row

        # Get school and admin user
        cursor = await db.execute("SELECT id FROM schools LIMIT 1")
        school = await cursor.fetchone()
        school_id = school['id']

        cursor = await db.execute("SELECT id FROM users WHERE email = 'admin'")
        admin = await cursor.fetchone()
        admin_id = admin['id']

        print(f"School: {school_id}, Admin: {admin_id}")

        # Create announcements table if not exists
        await db.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                id TEXT PRIMARY KEY,
                school_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT DEFAULT 'general',
                target_audience TEXT DEFAULT 'all',
                created_by TEXT NOT NULL,
                is_pinned INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (school_id) REFERENCES schools(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        announcements = [
            {
                "title": "Welcome to New Academic Year 2026-27",
                "content": "Dear Students and Parents,\n\nWe are excited to welcome you all to the new academic year 2026-27. This year promises to be filled with learning, growth, and exciting opportunities.\n\nPlease ensure you have all the required textbooks and materials. Classes begin on time at 8:00 AM.\n\nWishing everyone a successful academic year!",
                "type": "general",
                "target_audience": "all",
                "is_pinned": True,
            },
            {
                "title": "Annual Sports Day - September 25",
                "content": "Our Annual Sports Day will be held on September 25, 2026. All students are expected to participate in at least one event.\n\nEvents include:\n- 100m Race\n- 200m Race\n- Long Jump\n- Shot Put\n- Relay Race\n\nPractice sessions start next week. Contact your sports teacher for details.",
                "type": "event",
                "target_audience": "all",
                "is_pinned": False,
            },
            {
                "title": "Mid-Term Examination Schedule",
                "content": "Mid-term examinations will be conducted from October 10-20, 2026. The detailed timetable has been shared with class teachers.\n\nPlease ensure regular attendance and complete all assignments before the exams.",
                "type": "urgent",
                "target_audience": "students",
                "is_pinned": True,
            },
            {
                "title": "Parent-Teacher Meeting",
                "content": "A Parent-Teacher Meeting is scheduled for October 5, 2026 from 9:00 AM to 1:00 PM. All parents are requested to attend to discuss their child's progress.",
                "type": "event",
                "target_audience": "all",
                "is_pinned": False,
            },
            {
                "title": "Gandhi Jayanti Holiday",
                "content": "The school will remain closed on October 2, 2026 on account of Gandhi Jayanti. Regular classes will resume on October 3, 2026.",
                "type": "holiday",
                "target_audience": "all",
                "is_pinned": False,
            },
        ]

        now = datetime.utcnow().isoformat()
        count = 0

        for ann in announcements:
            # Check if exists
            cursor = await db.execute(
                "SELECT id FROM announcements WHERE school_id = ? AND title = ?",
                (school_id, ann['title'])
            )
            if await cursor.fetchone():
                continue

            ann_id = uuid.uuid4().hex
            await db.execute('''
                INSERT INTO announcements (id, school_id, title, content, type, target_audience, created_by, is_pinned, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ''', (ann_id, school_id, ann['title'], ann['content'], ann['type'], ann['target_audience'], admin_id, 1 if ann['is_pinned'] else 0, now, now))
            count += 1

        await db.commit()
        print(f"Created {count} announcements")
        print("Announcements seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_announcements())
