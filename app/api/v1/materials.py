"""Material ingestion endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/ingest")
def ingest_material_endpoint(payload: dict) -> dict:
    return {"status": "queued", "payload": payload}
