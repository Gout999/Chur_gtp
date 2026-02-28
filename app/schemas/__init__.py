"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum


# ==================== ENUMS ====================

class UserRole(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class AssignmentStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"


class MistakeStatus(str, Enum):
    UNRESOLVED = "unresolved"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"


class EnhancementStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ==================== TOKEN SCHEMAS ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    email: Optional[str] = None


# ==================== TEACHER PROFILE SCHEMAS ====================

class TeacherProfileBase(BaseModel):
    school: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None


class TeacherProfileCreate(TeacherProfileBase):
    pass


class TeacherProfileUpdate(TeacherProfileBase):
    pass


class TeacherProfileResponse(TeacherProfileBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int


# ==================== STUDENT PROFILE SCHEMAS ====================

class StudentProfileBase(BaseModel):
    grade: Optional[str] = None
    school: Optional[str] = None


class StudentProfileCreate(StudentProfileBase):
    pass


class StudentProfileUpdate(StudentProfileBase):
    pass


class StudentProfileResponse(StudentProfileBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int


# ==================== CLASS SCHEMAS ====================

class ClassBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=100)
    schedule: Optional[str] = None
    color: str = Field(default="blue", max_length=50)
    description: Optional[str] = None


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    schedule: Optional[str] = None
    color: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class ClassResponse(ClassBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    teacher_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ClassWithStudents(ClassResponse):
    students: List[StudentProfileResponse] = []


class ClassEnrollmentCreate(BaseModel):
    class_id: int
    student_id: int


class ClassEnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    class_id: int
    student_id: int
    enrolled_at: datetime


# ==================== MATERIAL SCHEMAS ====================

class MaterialBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class MaterialCreate(MaterialBase):
    class_id: Optional[int] = None


class MaterialUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    class_id: Optional[int] = None


class MaterialResponse(MaterialBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_path: str
    file_type: Optional[str] = None
    uploaded_by: int
    class_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==================== ENHANCED NOTE SCHEMAS ====================

class EnhancementSettings(BaseModel):
    study_mode: str = Field(..., description="quick, detailed, or exam_prep")
    focus: str = Field(..., description="concepts, examples, practice, or all")
    style: str = Field(..., description="bullet_points, paragraphs, tables, or mind_map")
    difficulty: Optional[str] = Field(None, description="basic, intermediate, or advanced")


class EnhancedNoteCreate(BaseModel):
    material_id: int
    enhancement_settings: EnhancementSettings


class EnhancedNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    material_id: int
    enhancement_settings: Dict[str, Any]
    status: EnhancementStatus
    content: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class EnhancedNoteUpdate(BaseModel):
    enhancement_settings: Optional[EnhancementSettings] = None


# ==================== ASSIGNMENT SCHEMAS ====================

class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    max_score: float = Field(default=100.0, ge=0)


class AssignmentCreate(AssignmentBase):
    class_id: int


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    max_score: Optional[float] = Field(None, ge=0)


class AssignmentResponse(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    class_id: int
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class AssignmentWithSubmissions(AssignmentResponse):
    submissions: List["SubmissionResponse"] = []


# ==================== SUBMISSION SCHEMAS ====================

class SubmissionBase(BaseModel):
    content: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    assignment_id: int


class SubmissionUpdate(BaseModel):
    content: Optional[str] = None


class SubmissionGrade(BaseModel):
    score: float = Field(..., ge=0)
    feedback: Optional[str] = None


class SubmissionResponse(SubmissionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    assignment_id: int
    student_id: int
    file_path: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    status: AssignmentStatus
    submitted_at: datetime
    graded_at: Optional[datetime] = None


class SubmissionWithStudent(SubmissionResponse):
    student: Optional[StudentProfileResponse] = None


# ==================== MISTAKE SCHEMAS ====================

class MistakeBase(BaseModel):
    subject: str = Field(..., min_length=1, max_length=100)
    topic: Optional[str] = Field(None, max_length=255)
    question: str = Field(..., min_length=1)
    correct_answer: str = Field(..., min_length=1)
    student_answer: Optional[str] = None
    explanation: Optional[str] = None


class MistakeCreate(MistakeBase):
    pass


class MistakeUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    topic: Optional[str] = Field(None, max_length=255)
    question: Optional[str] = Field(None, min_length=1)
    correct_answer: Optional[str] = Field(None, min_length=1)
    student_answer: Optional[str] = None
    explanation: Optional[str] = None
    status: Optional[MistakeStatus] = None


class MistakeResponse(MistakeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    student_id: int
    status: MistakeStatus
    created_at: datetime
    updated_at: Optional[datetime] = None


class MistakeStats(BaseModel):
    total: int
    unresolved: int
    reviewing: int
    resolved: int
    by_subject: Dict[str, int]


# ==================== CHAT SCHEMAS ====================

class ChatSessionBase(BaseModel):
    session_type: str = Field(default="homework", max_length=50)
    title: Optional[str] = Field(None, max_length=255)


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)


class ChatSessionResponse(ChatSessionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ChatMessageBase(BaseModel):
    role: str = Field(..., max_length=50)  # user, assistant, system
    content: str = Field(..., min_length=1)


class ChatMessageCreate(ChatMessageBase):
    session_id: int


class ChatMessageResponse(ChatMessageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_id: int
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    message: ChatMessageResponse
    session_id: int


# ==================== AI ENHANCEMENT SCHEMAS ====================

class MaterialEnhancementRequest(BaseModel):
    material_id: int
    settings: EnhancementSettings


class MaterialEnhancementResponse(BaseModel):
    enhancement_id: int
    status: EnhancementStatus
    content: Optional[str] = None
    message: str


# ==================== DASHBOARD/STATS SCHEMAS ====================

class TeacherDashboardStats(BaseModel):
    total_classes: int
    total_students: int
    total_materials: int
    total_assignments: int
    pending_submissions: int


class StudentDashboardStats(BaseModel):
    total_classes: int
    pending_assignments: int
    completed_assignments: int
    total_mistakes: int
    unresolved_mistakes: int


# ==================== PAGINATION SCHEMAS ====================

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool
