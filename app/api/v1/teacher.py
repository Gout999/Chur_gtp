"""Teacher endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/profile")
def get_teacher_profile() -> dict:
    return {"id": "teacher-demo", "role": "teacher"}
