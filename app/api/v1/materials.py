"""Materials API endpoints (public/shared)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Material, EnhancedNote
from app.schemas import (
    MaterialResponse, EnhancedNoteCreate, EnhancedNoteResponse, EnhancedNoteUpdate
)
from app.core.security import get_current_active_user

router = APIRouter(prefix="/materials", tags=["Materials"])


@router.get("/", response_model=List[MaterialResponse])
def get_materials(
    subject: str = None,
    class_id: int = None,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all materials (filtered by subject or class if provided)."""
    query = db.query(Material)
    
    if subject:
        query = query.filter(Material.subject == subject)
    
    if class_id:
        query = query.filter(Material.class_id == class_id)
    
    materials = query.all()
    return materials


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific material."""
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    return material


@router.get("/{material_id}/enhancements", response_model=List[EnhancedNoteResponse])
def get_material_enhancements(
    material_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all AI enhancements for a material."""
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    enhancements = db.query(EnhancedNote).filter(
        EnhancedNote.material_id == material_id
    ).all()
    
    return enhancements


@router.post("/{material_id}/enhancements", 
             response_model=EnhancedNoteResponse, 
             status_code=status.HTTP_201_CREATED)
def create_enhancement(
    material_id: int,
    enhancement_data: EnhancedNoteCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Request AI enhancement for a material."""
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    enhancement = EnhancedNote(
        material_id=material_id,
        enhancement_settings=enhancement_data.enhancement_settings.model_dump(),
        status="pending"
    )
    
    db.add(enhancement)
    db.commit()
    db.refresh(enhancement)
    
    return enhancement


@router.get("/enhancements/{enhancement_id}", response_model=EnhancedNoteResponse)
def get_enhancement(
    enhancement_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific enhancement."""
    enhancement = db.query(EnhancedNote).filter(
        EnhancedNote.id == enhancement_id
    ).first()
    
    if not enhancement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enhancement not found"
        )
    
    return enhancement


@router.put("/enhancements/{enhancement_id}", response_model=EnhancedNoteResponse)
def update_enhancement(
    enhancement_id: int,
    enhancement_data: EnhancedNoteUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an enhancement request."""
    enhancement = db.query(EnhancedNote).filter(
        EnhancedNote.id == enhancement_id
    ).first()
    
    if not enhancement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enhancement not found"
        )
    
    update_data = enhancement_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(enhancement, field, value)
    
    db.commit()
    db.refresh(enhancement)
    
    return enhancement
