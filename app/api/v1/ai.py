"""AI API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EnhancedNote, Material
from app.schemas import (
    MaterialEnhancementRequest, MaterialEnhancementResponse,
    EnhancedNoteResponse
)
from app.core.security import get_current_active_user, get_current_teacher

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/enhance", response_model=MaterialEnhancementResponse)
def request_material_enhancement(
    request: MaterialEnhancementRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Request AI enhancement for a material."""
    from app.services.ai import process_enhancement
    
    # Verify material exists
    material = db.query(Material).filter(Material.id == request.material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Create enhancement record
    enhancement = EnhancedNote(
        material_id=request.material_id,
        enhancement_settings=request.settings.model_dump(),
        status="pending"
    )
    
    db.add(enhancement)
    db.commit()
    db.refresh(enhancement)
    
    # Process enhancement in background
    background_tasks.add_task(process_enhancement, enhancement.id)
    
    return MaterialEnhancementResponse(
        enhancement_id=enhancement.id,
        status="pending",
        message="Enhancement request queued for processing"
    )


@router.get("/enhance/{enhancement_id}", response_model=EnhancedNoteResponse)
def get_enhancement_status(
    enhancement_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get enhancement status and result."""
    enhancement = db.query(EnhancedNote).filter(
        EnhancedNote.id == enhancement_id
    ).first()
    
    if not enhancement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enhancement not found"
        )
    
    return enhancement


@router.post("/enhance/{enhancement_id}/retry", response_model=MaterialEnhancementResponse)
def retry_enhancement(
    enhancement_id: int,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Retry a failed enhancement."""
    from app.services.ai import process_enhancement
    
    enhancement = db.query(EnhancedNote).filter(
        EnhancedNote.id == enhancement_id
    ).first()
    
    if not enhancement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enhancement not found"
        )
    
    # Reset status and retry
    enhancement.status = "pending"
    enhancement.error_message = None
    db.commit()
    
    # Process in background
    background_tasks.add_task(process_enhancement, enhancement.id)
    
    return MaterialEnhancementResponse(
        enhancement_id=enhancement.id,
        status="pending",
        message="Enhancement retry queued"
    )
