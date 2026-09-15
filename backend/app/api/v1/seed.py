"""Seed endpoint to initialize database with sample data."""
import uuid
from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_async_session
from app.core.security import get_password_hash

router = APIRouter()


@router.post("/init")
async def seed_database(session: AsyncSession = Depends(get_async_session)):
    """Initialize database with sample data. Call once after deployment."""

    now = datetime.utcnow().isoformat()

    # Check if already seeded
    result = await session.execute(text("SELECT COUNT(*) FROM schools"))
    count = result.scalar()
    if count and count > 0:
        return {"message": "Database already seeded", "school_count": count}

    # Create school
    school_id = uuid.uuid4().hex
    await session.execute(text("""
        INSERT INTO schools (id, name, code, address, phone, email, is_active, created_at, updated_at)
        VALUES (:id, :name, :code, :address, :phone, :email, :is_active, :created_at, :updated_at)
    """), {
        "id": school_id,
        "name": "St Joseph's Public School",
        "code": "SJPS",
        "address": "123 Education Lane, Knowledge City",
        "phone": "+91 9876543210",
        "email": "info@stjosephs.edu",
        "is_active": True,
        "created_at": now,
        "updated_at": now
    })

    # Create admin user
    admin_id = uuid.uuid4().hex
    admin_hash = get_password_hash("12345")
    await session.execute(text("""
        INSERT INTO users (id, email, hashed_password, full_name, role, school_id, is_active, is_superuser, created_at, updated_at)
        VALUES (:id, :email, :hashed_password, :full_name, :role, :school_id, :is_active, :is_superuser, :created_at, :updated_at)
    """), {
        "id": admin_id,
        "email": "admin",
        "hashed_password": admin_hash,
        "full_name": "Admin User",
        "role": "admin",
        "school_id": school_id,
        "is_active": True,
        "is_superuser": True,
        "created_at": now,
        "updated_at": now
    })

    # Create teacher user
    teacher_id = uuid.uuid4().hex
    teacher_hash = get_password_hash("12345")
    await session.execute(text("""
        INSERT INTO users (id, email, hashed_password, full_name, role, school_id, is_active, is_superuser, created_at, updated_at)
        VALUES (:id, :email, :hashed_password, :full_name, :role, :school_id, :is_active, :is_superuser, :created_at, :updated_at)
    """), {
        "id": teacher_id,
        "email": "teacher",
        "hashed_password": teacher_hash,
        "full_name": "Teacher User",
        "role": "teacher",
        "school_id": school_id,
        "is_active": True,
        "is_superuser": False,
        "created_at": now,
        "updated_at": now
    })

    # Create student user
    student_user_id = uuid.uuid4().hex
    student_hash = get_password_hash("12345")
    await session.execute(text("""
        INSERT INTO users (id, email, hashed_password, full_name, role, school_id, is_active, is_superuser, created_at, updated_at)
        VALUES (:id, :email, :hashed_password, :full_name, :role, :school_id, :is_active, :is_superuser, :created_at, :updated_at)
    """), {
        "id": student_user_id,
        "email": "student",
        "hashed_password": student_hash,
        "full_name": "Rahul Sharma",
        "role": "student",
        "school_id": school_id,
        "is_active": True,
        "is_superuser": False,
        "created_at": now,
        "updated_at": now
    })

    # Create student record
    student_id = uuid.uuid4().hex
    await session.execute(text("""
        INSERT INTO students (id, user_id, school_id, admission_number, class_name, section, roll_number, date_of_birth, guardian_name, guardian_phone, address, created_at, updated_at)
        VALUES (:id, :user_id, :school_id, :admission_number, :class_name, :section, :roll_number, :date_of_birth, :guardian_name, :guardian_phone, :address, :created_at, :updated_at)
    """), {
        "id": student_id,
        "user_id": student_user_id,
        "school_id": school_id,
        "admission_number": "SJPS-2026-001",
        "class_name": "10",
        "section": "A",
        "roll_number": 1,
        "date_of_birth": "2010-05-15",
        "guardian_name": "Mr. Sharma",
        "guardian_phone": "+91 9876543211",
        "address": "456 Student Street",
        "created_at": now,
        "updated_at": now
    })

    # Create subjects
    subjects_data = [
        ("Mathematics", "MATH101", "Core mathematics"),
        ("Physics", "PHY101", "Physics fundamentals"),
        ("Chemistry", "CHEM101", "Chemistry basics"),
        ("English", "ENG101", "English language"),
        ("Computer Science", "CS101", "Programming basics"),
    ]

    subject_ids = []
    for name, code, desc in subjects_data:
        subj_id = uuid.uuid4().hex
        subject_ids.append(subj_id)
        await session.execute(text("""
            INSERT INTO subjects (id, school_id, name, code, description, class_name, is_active, created_at, updated_at)
            VALUES (:id, :school_id, :name, :code, :description, :class_name, :is_active, :created_at, :updated_at)
        """), {
            "id": subj_id,
            "school_id": school_id,
            "name": name,
            "code": code,
            "description": desc,
            "class_name": "10",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        })

    # Create announcements
    announcements_data = [
        ("Welcome to New Academic Year 2026-27", "We are excited to welcome you all to the new academic year!", "general", True),
        ("Annual Sports Day - September 25", "Our Annual Sports Day will be held on September 25, 2026.", "event", False),
        ("Mid-Term Examination Schedule", "Mid-term examinations from October 10-20, 2026.", "urgent", True),
    ]

    for title, content, ann_type, is_pinned in announcements_data:
        ann_id = uuid.uuid4().hex
        await session.execute(text("""
            INSERT INTO announcements (id, school_id, title, content, type, target_audience, created_by, is_pinned, is_active, created_at, updated_at)
            VALUES (:id, :school_id, :title, :content, :type, :target_audience, :created_by, :is_pinned, :is_active, :created_at, :updated_at)
        """), {
            "id": ann_id,
            "school_id": school_id,
            "title": title,
            "content": content,
            "type": ann_type,
            "target_audience": "all",
            "created_by": admin_id,
            "is_pinned": is_pinned,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        })

    await session.commit()

    return {
        "message": "Database seeded successfully!",
        "data": {
            "school": "St Joseph's Public School",
            "users": {
                "admin": {"username": "admin", "password": "12345"},
                "teacher": {"username": "teacher", "password": "12345"},
                "student": {"username": "student", "password": "12345"}
            }
        }
    }
