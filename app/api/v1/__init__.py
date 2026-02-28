"""API v1 router registration."""
from fastapi import APIRouter

from .escalations import router as escalations_router
from .materials import router as materials_router
from .messages import router as messages_router
from .students import router as students_router
from .teacher import router as teacher_router

api_router = APIRouter()
api_router.include_router(teacher_router, prefix="/teacher", tags=["teacher"])
api_router.include_router(materials_router, prefix="/materials", tags=["materials"])
api_router.include_router(students_router, prefix="/students", tags=["students"])
api_router.include_router(escalations_router, prefix="/escalations", tags=["escalations"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])

__all__ = ["api_router"]
