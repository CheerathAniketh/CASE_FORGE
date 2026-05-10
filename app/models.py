from sqlalchemy import Column, String, Integer, DateTime, JSON, Float, Enum
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid
from app.db import Base


class ComplexityLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CaseStudy(Base):
    """Case study model"""
    __tablename__ = "case_studies"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    user_id = Column(Integer, index=True)
    
    title = Column(String(200))
    industry = Column(String(100), index=True)
    complexity = Column(Enum(ComplexityLevel), index=True)
    focus_area = Column(String(200), nullable=True)
    
    # Full case data stored as JSON
    case_data = Column(JSON)
    
    # Metadata
    generation_time_ms = Column(Integer)
    tokens_used = Column(Integer, default=0)
    model_used = Column(String(100))
    refinement_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class UserSolution(Base):
    """User's solution to a case study"""
    __tablename__ = "user_solutions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    user_id = Column(Integer, index=True)
    case_id = Column(Integer, index=True)
    
    solution_text = Column(String(5000))
    
    # Evaluation scores
    overall_score = Column(Float, nullable=True)
    reasoning_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    business_acumen_score = Column(Float, nullable=True)
    
    # Feedback
    feedback_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)