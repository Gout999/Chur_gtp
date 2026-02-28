"""Assignments API endpoints (public/shared)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assignment, Submission, Class, TeacherProfile
from app.schemas import (
    AssignmentResponse, AssignmentWithSubmissions,
    SubmissionResponse, SubmissionGrade, SubmissionWithStudent
)
from app.core.security import get_current_active_user, get_current_teacher

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("/", response_model=List[AssignmentResponse])
def get_assignments(
    class_id: int = None,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all assignments (filtered by class if provided)."""
    query = db.query(Assignment)
    
    if class_id:
        query = query.filter(Assignment.class_id == class_id)
    
    assignments = query.all()
    return assignments


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific assignment."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return assignment


@router.get("/{assignment_id}/with-submissions", response_model=AssignmentWithSubmissions)
def get_assignment_with_submissions(
    assignment_id: int,
    current_user = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get assignment with all submissions (teacher only)."""
    teacher_profile = current_user.teacher_profile
    
    assignment = db.query(Assignment).join(Class).filter(
        Assignment.id == assignment_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return assignment


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionWithStudent])
def get_assignment_submissions(
    assignment_id: int,
    current_user = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all submissions for an assignment (teacher only)."""
    teacher_profile = current_user.teacher_profile
    
    assignment = db.query(Assignment).join(Class).filter(
        Assignment.id == assignment_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    submissions = db.query(Submission).filter(
        Submission.assignment_id == assignment_id
    ).all()
    
    return submissions


@router.post("/{assignment_id}/submissions/{submission_id}/grade", 
             response_model=SubmissionResponse)
def grade_submission(
    assignment_id: int,
    submission_id: int,
    grade_data: SubmissionGrade,
    current_user = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Grade a submission (teacher only)."""
    from datetime import datetime
    
    teacher_profile = current_user.teacher_profile
    
    # Verify assignment belongs to teacher
    assignment = db.query(Assignment).join(Class).filter(
        Assignment.id == assignment_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Get submission
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.assignment_id == assignment_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Update grade
    submission.score = grade_data.score
    submission.feedback = grade_data.feedback
    submission.status = "graded"
    submission.graded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(submission)
    
    return submission
