"""Teacher API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Class, Material, Assignment, ClassEnrollment, StudentProfile
from app.schemas import (
    ClassCreate, ClassResponse, ClassUpdate,
    MaterialCreate, MaterialResponse, MaterialUpdate,
    AssignmentCreate, AssignmentResponse, AssignmentUpdate,
    TeacherDashboardStats
)
from app.core.security import get_current_teacher

router = APIRouter(prefix="/teachers", tags=["Teachers"])


# ==================== CLASSES ====================

@router.get("/classes", response_model=List[ClassResponse])
def get_teacher_classes(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all classes for the current teacher."""
    teacher_profile = current_user.teacher_profile
    
    if not teacher_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    classes = db.query(Class).filter(Class.teacher_id == teacher_profile.id).all()
    return classes


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new class."""
    teacher_profile = current_user.teacher_profile
    
    if not teacher_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    new_class = Class(
        name=class_data.name,
        subject=class_data.subject,
        teacher_id=teacher_profile.id,
        schedule=class_data.schedule,
        color=class_data.color,
        description=class_data.description
    )
    
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return new_class


@router.get("/classes/{class_id}", response_model=ClassResponse)
def get_class(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a specific class by ID."""
    teacher_profile = current_user.teacher_profile
    
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    return class_obj


@router.put("/classes/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    class_data: ClassUpdate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update a class."""
    teacher_profile = current_user.teacher_profile
    
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    update_data = class_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(class_obj, field, value)
    
    db.commit()
    db.refresh(class_obj)
    
    return class_obj


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a class."""
    teacher_profile = current_user.teacher_profile
    
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    db.delete(class_obj)
    db.commit()
    
    return None


# ==================== CLASS ENROLLMENTS ====================

@router.post("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_201_CREATED)
def enroll_student(
    class_id: int,
    student_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Enroll a student in a class."""
    teacher_profile = current_user.teacher_profile
    
    # Verify the class belongs to the teacher
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify the student exists
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if already enrolled
    existing = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_id,
        ClassEnrollment.student_id == student_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already enrolled in this class"
        )
    
    enrollment = ClassEnrollment(
        class_id=class_id,
        student_id=student_id
    )
    
    db.add(enrollment)
    db.commit()
    
    return {"message": "Student enrolled successfully"}


@router.delete("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student(
    class_id: int,
    student_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Remove a student from a class."""
    teacher_profile = current_user.teacher_profile
    
    # Verify the class belongs to the teacher
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_id,
        ClassEnrollment.student_id == student_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    db.delete(enrollment)
    db.commit()
    
    return None


# ==================== MATERIALS ====================

@router.get("/materials", response_model=List[MaterialResponse])
def get_teacher_materials(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all materials uploaded by the teacher."""
    teacher_profile = current_user.teacher_profile
    
    materials = db.query(Material).filter(
        Material.uploaded_by == teacher_profile.id
    ).all()
    
    return materials


@router.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material_data: MaterialCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new material."""
    teacher_profile = current_user.teacher_profile
    
    new_material = Material(
        title=material_data.title,
        subject=material_data.subject,
        description=material_data.description,
        uploaded_by=teacher_profile.id,
        class_id=material_data.class_id,
        file_path="placeholder"  # TODO: Implement file upload
    )
    
    db.add(new_material)
    db.commit()
    db.refresh(new_material)
    
    return new_material


@router.get("/materials/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a specific material."""
    teacher_profile = current_user.teacher_profile
    
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.uploaded_by == teacher_profile.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    return material


@router.put("/materials/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_data: MaterialUpdate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update a material."""
    teacher_profile = current_user.teacher_profile
    
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.uploaded_by == teacher_profile.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    update_data = material_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(material, field, value)
    
    db.commit()
    db.refresh(material)
    
    return material


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a material."""
    teacher_profile = current_user.teacher_profile
    
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.uploaded_by == teacher_profile.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    db.delete(material)
    db.commit()
    
    return None


# ==================== ASSIGNMENTS ====================

@router.get("/assignments", response_model=List[AssignmentResponse])
def get_teacher_assignments(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all assignments created by the teacher."""
    teacher_profile = current_user.teacher_profile
    
    assignments = db.query(Assignment).join(Class).filter(
        Class.teacher_id == teacher_profile.id
    ).all()
    
    return assignments


@router.post("/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new assignment."""
    teacher_profile = current_user.teacher_profile
    
    # Verify the class belongs to the teacher
    class_obj = db.query(Class).filter(
        Class.id == assignment_data.class_id,
        Class.teacher_id == teacher_profile.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or not owned by you"
        )
    
    new_assignment = Assignment(
        title=assignment_data.title,
        description=assignment_data.description,
        class_id=assignment_data.class_id,
        due_date=assignment_data.due_date,
        max_score=assignment_data.max_score
    )
    
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    return new_assignment


@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a specific assignment."""
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


@router.put("/assignments/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update an assignment."""
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
    
    update_data = assignment_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    db.commit()
    db.refresh(assignment)
    
    return assignment


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete an assignment."""
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
    
    db.delete(assignment)
    db.commit()
    
    return None


# ==================== DASHBOARD ====================

@router.get("/dashboard/stats", response_model=TeacherDashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for the teacher."""
    teacher_profile = current_user.teacher_profile
    
    # Count classes
    total_classes = db.query(Class).filter(
        Class.teacher_id == teacher_profile.id
    ).count()
    
    # Count students (unique across all classes)
    total_students = db.query(ClassEnrollment).join(Class).filter(
        Class.teacher_id == teacher_profile.id
    ).distinct(ClassEnrollment.student_id).count()
    
    # Count materials
    total_materials = db.query(Material).filter(
        Material.uploaded_by == teacher_profile.id
    ).count()
    
    # Count assignments
    total_assignments = db.query(Assignment).join(Class).filter(
        Class.teacher_id == teacher_profile.id
    ).count()
    
    # Count pending submissions
    from app.models import Submission
    pending_submissions = db.query(Submission).join(Assignment).join(Class).filter(
        Class.teacher_id == teacher_profile.id,
        Submission.status == "submitted"
    ).count()
    
    return TeacherDashboardStats(
        total_classes=total_classes,
        total_students=total_students,
        total_materials=total_materials,
        total_assignments=total_assignments,
        pending_submissions=pending_submissions
    )
