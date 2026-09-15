from fastapi import APIRouter

from app.api.v1 import auth, students, health, subjects, attendance, results

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(results.router, prefix="/results", tags=["results"])
