"""SQLAlchemy models for ChurGPT backend."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles enumeration."""
    TEACHER = "teacher"
    STUDENT = "student"


class AssignmentStatus(str, enum.Enum):
    """Assignment status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"


class MistakeStatus(str, enum.Enum):
    """Mistake status enumeration."""
    UNRESOLVED = "unresolved"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"


class EnhancementStatus(str, enum.Enum):
    """AI enhancement status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """User model for authentication and basic info."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    chat_sessions = relationship("ChatSession", back_populates="user")


class TeacherProfile(Base):
    """Teacher profile with additional information."""
    __tablename__ = "teacher_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    school = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    classes = relationship("Class", back_populates="teacher")


class StudentProfile(Base):
    """Student profile with additional information."""
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    grade = Column(String(50), nullable=True)
    school = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="student_profile")
    class_enrollments = relationship("ClassEnrollment", back_populates="student")
    submissions = relationship("Submission", back_populates="student")
    mistakes = relationship("Mistake", back_populates="student")


class Class(Base):
    """Class/Course model."""
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teacher_profiles.id"), nullable=False)
    schedule = Column(String(255), nullable=True)
    color = Column(String(50), default="blue")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher = relationship("TeacherProfile", back_populates="classes")
    enrollments = relationship("ClassEnrollment", back_populates="class_")
    materials = relationship("Material", back_populates="class_")
    assignments = relationship("Assignment", back_populates="class_")


class ClassEnrollment(Base):
    """Many-to-many relationship between students and classes."""
    __tablename__ = "class_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    class_ = relationship("Class", back_populates="enrollments")
    student = relationship("StudentProfile", back_populates="class_enrollments")


class Material(Base):
    """Learning material uploaded by teachers."""
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("teacher_profiles.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    class_ = relationship("Class", back_populates="materials")
    enhanced_notes = relationship("EnhancedNote", back_populates="material")


class EnhancedNote(Base):
    """AI-enhanced notes generated from materials."""
    __tablename__ = "enhanced_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    enhancement_settings = Column(JSON, nullable=False)  # Study mode, focus, style preferences
    status = Column(Enum(EnhancementStatus), default=EnhancementStatus.PENDING)
    content = Column(Text, nullable=True)  # The enhanced content
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    material = relationship("Material", back_populates="enhanced_notes")


class Assignment(Base):
    """Assignment created by teachers."""
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    max_score = Column(Float, default=100.0)
    file_path = Column(String(500), nullable=True)  # Attached file
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    class_ = relationship("Class", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")


class Submission(Base):
    """Student submission for assignments."""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PENDING)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    graded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("StudentProfile", back_populates="submissions")


class Mistake(Base):
    """Student mistake tracking for learning improvement."""
    __tablename__ = "mistakes"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    topic = Column(String(255), nullable=True)
    question = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    student_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    status = Column(Enum(MistakeStatus), default=MistakeStatus.UNRESOLVED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    student = relationship("StudentProfile", back_populates="mistakes")


class ChatSession(Base):
    """Chat session for AI assistant."""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_type = Column(String(50), default="homework")  # homework, general, etc.
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """Individual chat message in a session."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
