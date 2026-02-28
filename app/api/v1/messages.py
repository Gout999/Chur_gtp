"""Messaging endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/")
def post_message(payload: dict) -> dict:
    return {"status": "sent", "payload": payload}
