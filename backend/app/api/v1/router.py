from fastapi import APIRouter

from app.api.v1 import auth, students, health, subjects, attendance, results, teachers, admin, fees, timetable, announcements, seed

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(results.router, prefix="/results", tags=["results"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(fees.router, prefix="/fees", tags=["fees"])
api_router.include_router(timetable.router, tags=["timetable"])
api_router.include_router(announcements.router, tags=["announcements"])
api_router.include_router(seed.router, prefix="/seed", tags=["seed"])
