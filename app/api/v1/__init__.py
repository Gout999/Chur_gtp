"""API router configuration."""
from fastapi import APIRouter

from app.api.v1 import auth, teachers, students, materials, assignments, chat, ai

api_router = APIRouter()

# Include all routers (they already have their own prefixes)
api_router.include_router(auth.router)
api_router.include_router(teachers.router)
api_router.include_router(students.router)
api_router.include_router(materials.router)
api_router.include_router(assignments.router)
api_router.include_router(chat.router)
api_router.include_router(ai.router)
