from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text, Enum, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class ComplexityEnum(str, enum.Enum):
    """Complexity levels for case studies"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class User(Base):
    """User model - represents a student"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_student_id_created", "student_id", "created_at"),
    )


class CaseStudy(Base):
    """Case Study model - represents a generated case"""
    __tablename__ = "case_studies"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Metadata
    title = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False, index=True)
    complexity = Column(Enum(ComplexityEnum), nullable=False, index=True)
    focus_area = Column(String(255), nullable=True)

    # Content - stored as JSONB for flexibility
    case_data = Column(JSON, nullable=False)

    # Performance metrics
    generation_time_ms = Column(Integer, nullable=True)
    model_used = Column(String(100), default="mixtral-8x7b-32768")
    tokens_used = Column(Integer, nullable=True)
    refinement_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
        Index("idx_industry_complexity", "industry", "complexity"),
    )


class UserSolution(Base):
    """User Solution model - for tracking student responses (Phase 2+)"""
    __tablename__ = "user_solutions"

    id = Column(Integer, primary_key=True, index=True)
    case_study_id = Column(Integer, ForeignKey("case_studies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    solution_text = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_case_user", "case_study_id", "user_id"),
    )