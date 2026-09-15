"""Seed sample timetable data."""
import asyncio
import uuid
import aiosqlite

async def seed_timetable_data():
    db_path = "school_saas.db"

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Get school
        cursor = await db.execute("SELECT id FROM schools LIMIT 1")
        school = await cursor.fetchone()
        if not school:
            print("No school found.")
            return
        school_id = school['id']
        print(f"Found school ID: {school_id}")

        # Get subjects
        cursor = await db.execute("SELECT id, name FROM subjects WHERE school_id = ?", (school_id,))
        subjects_rows = await cursor.fetchall()
        subjects = {row['name']: row['id'] for row in subjects_rows}
        print(f"Found {len(subjects)} subjects: {list(subjects.keys())}")

        # Get teacher
        cursor = await db.execute("SELECT id FROM teachers LIMIT 1")
        teacher = await cursor.fetchone()
        teacher_id = teacher['id'] if teacher else None
        print(f"Teacher ID: {teacher_id}")

        # Sample timetable for class 10-A
        periods = [
            ("08:00", "08:45"),
            ("08:50", "09:35"),
            ("09:40", "10:25"),
            ("10:45", "11:30"),
            ("11:35", "12:20"),
            ("12:25", "13:10"),
        ]

        schedule = {
            0: ["Mathematics", "English", "Physics", "Chemistry", "Computer Science", "Hindi"],
            1: ["English", "Mathematics", "Chemistry", "Physics", "Hindi", "Computer Science"],
            2: ["Physics", "Chemistry", "Mathematics", "English", "Computer Science", "Hindi"],
            3: ["Chemistry", "Physics", "English", "Mathematics", "Hindi", "Computer Science"],
            4: ["Mathematics", "English", "Computer Science", "Hindi", "Physics", "Chemistry"],
            5: ["English", "Mathematics", "Physics", "Chemistry", None, None],
        }

        count = 0
        for day, day_subjects in schedule.items():
            for period_idx, subject_name in enumerate(day_subjects):
                if subject_name is None:
                    continue

                subject_id = subjects.get(subject_name)
                if not subject_id:
                    print(f"Subject not found: {subject_name}")
                    continue

                start_time, end_time = periods[period_idx]

                # Check if entry exists
                cursor = await db.execute(
                    "SELECT id FROM timetables WHERE school_id = ? AND class_name = ? AND day_of_week = ? AND start_time = ?",
                    (school_id, "10-A", day, start_time)
                )
                if await cursor.fetchone():
                    continue

                entry_id = uuid.uuid4().hex
                await db.execute(
                    """INSERT INTO timetables (id, school_id, class_name, subject_id, teacher_id, day_of_week, start_time, end_time, room, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                    (entry_id, school_id, "10-A", subject_id, teacher_id, day, start_time, end_time, f"Room {101 + period_idx}", 1)
                )
                count += 1

        await db.commit()
        print(f"Created {count} timetable entries")
        print("\nTimetable data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_timetable_data())
