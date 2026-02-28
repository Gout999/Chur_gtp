"""Student endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{student_id}")
def get_student(student_id: str) -> dict:
    return {"student_id": student_id}
