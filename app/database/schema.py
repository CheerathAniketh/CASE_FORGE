from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ComplexityEnum(str, Enum):
    """Complexity levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# ===== Request Schemas =====

class CaseStudyGenerateRequest(BaseModel):
    """Request body for generating a case study"""
    industry: str = Field(..., min_length=1, max_length=100, description="Industry for the case")
    complexity: ComplexityEnum = Field(..., description="Difficulty level")
    focus_area: Optional[str] = Field(None, max_length=255, description="Specific focus area")
    time_limit_minutes: Optional[int] = Field(60, ge=30, le=180, description="Time limit in minutes")
    num_questions: Optional[int] = Field(3, ge=1, le=10, description="Number of questions")


class AuthRequest(BaseModel):
    """Request body for authentication"""
    student_id: str = Field(..., min_length=1, max_length=100, description="Student ID")


# ===== Response Schemas =====

class CaseStudyResponse(BaseModel):
    """Response for a single case study"""
    uuid: str
    title: str
    industry: str
    complexity: str
    focus_area: Optional[str]
    case_data: Dict[str, Any]
    created_at: datetime
    generation_time_ms: Optional[int]
    tokens_used: Optional[int]
    refinement_count: int

    class Config:
        from_attributes = True


class CaseStudyListResponse(BaseModel):
    """Response for listing case studies"""
    total: int = Field(..., description="Total number of cases")
    cases: List[CaseStudyResponse] = Field(..., description="List of cases")


class AuthResponse(BaseModel):
    """Response for authentication"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class HealthResponse(BaseModel):
    """Response for health check"""
    status: str
    database: str
    groq: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    status_code: int
    timestamp: datetime