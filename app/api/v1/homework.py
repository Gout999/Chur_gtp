"""Homework marker API: accept image upload, return AI marking result."""
import base64
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.homework_marker import mark_homework_from_image

LOG = logging.getLogger("eduguide.homework")

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_IMAGE_MIME = {"image/png", "image/jpeg"}
MAX_HOMEWORK_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB

router = APIRouter()


class CriteriaScoreItem(BaseModel):
    name: str
    score: float
    comment: Optional[str] = None


class HomeworkMarkResponse(BaseModel):
    score: float
    max_score: int
    feedback: str
    criteria_scores: Optional[List[CriteriaScoreItem]] = None
    model_used: str


@router.post("/mark", response_model=HomeworkMarkResponse)
async def mark_homework(
    file: UploadFile = File(..., description="Homework image (PNG, JPG, JPEG)"),
    rubric: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    max_score: int = Form(100),
) -> HomeworkMarkResponse:
    """
    Upload a homework image and receive structured marking feedback from the vision model.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
        )

    content_type = (file.content_type or "").strip().lower()
    if content_type and content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Allowed: {', '.join(sorted(ALLOWED_IMAGE_MIME))}",
        )

    raw = await file.read()
    if len(raw) > MAX_HOMEWORK_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_HOMEWORK_IMAGE_BYTES // (1024 * 1024)} MB",
        )
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    try:
        image_b64 = base64.b64encode(raw).decode("ascii")
    except Exception as e:
        LOG.warning("Base64 encode failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid image data") from e

    mime = content_type or ("image/png" if suffix == ".png" else "image/jpeg")

    try:
        result = mark_homework_from_image(
            image_base64=image_b64,
            content_type=mime,
            rubric=rubric,
            subject=subject,
            max_score=max_score,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except RuntimeError as e:
        LOG.warning("Homework marking failed: %s", e)
        raise HTTPException(status_code=502, detail="Marking failed; please try again.") from e

    criteria = result.get("criteria_scores")
    if criteria is not None:
        criteria = [CriteriaScoreItem(**c) for c in criteria if isinstance(c, dict)]

    return HomeworkMarkResponse(
        score=result["score"],
        max_score=result["max_score"],
        feedback=result["feedback"],
        criteria_scores=criteria,
        model_used=result["model_used"],
    )
