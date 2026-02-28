"""Escalation endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/")
def create_escalation(payload: dict) -> dict:
    return {"status": "received", "payload": payload}
