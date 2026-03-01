"""API router configuration."""
from fastapi import APIRouter

from app.api.v1 import (
    ai,
    assignments,
    auth,
    chat,
    escalations,
    homework,
    materials,
    messages,
    push,
    students,
    teacher,
    teachers,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(teachers.router)
api_router.include_router(students.router)
api_router.include_router(materials.router)
api_router.include_router(assignments.router)
api_router.include_router(chat.router)
api_router.include_router(ai.router)
api_router.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
api_router.include_router(homework.router, prefix="/homework", tags=["homework"])
api_router.include_router(escalations.router, prefix="/escalations", tags=["escalations"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(push.router, prefix="/push", tags=["push"])
