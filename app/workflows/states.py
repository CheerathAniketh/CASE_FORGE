from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class CaseGenerationInput(BaseModel):
    """Input state for case generation workflow"""
    industry: str = Field(..., description="Industry for the case")
    complexity: str = Field(..., description="Difficulty level")
    focus_area: Optional[str] = Field(None, description="Specific focus")
    time_limit_minutes: int = Field(60, description="Time limit")
    num_questions: int = Field(3, description="Number of questions")
    user_id: int = Field(..., description="User ID generating the case")


class CaseWorkflowState(BaseModel):
    """Complete state for the case generation workflow"""
    
    # Input
    input: CaseGenerationInput = Field(..., description="Initial input")
    
    # Step 1: Generation
    generated_case_raw: Optional[str] = Field(None, description="Raw GROQ response")
    generated_case_json: Optional[Dict[str, Any]] = Field(None, description="Parsed JSON case")
    generation_error: Optional[str] = Field(None, description="Generation error if any")
    
    # Step 2: Validation
    is_valid: bool = Field(False, description="Is case valid?")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_score: float = Field(0.0, ge=0.0, le=1.0, description="Quality score 0-1")
    
    # Step 3: Refinement tracking
    refinement_count: int = Field(0, description="Number of refinements attempted")
    max_refinements: int = Field(2, description="Max refinement attempts")
    
    # Final result
    final_case: Optional[Dict[str, Any]] = Field(None, description="Final case ready to save")
    
    # Metadata
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Workflow start")
    end_time: Optional[datetime] = Field(None, description="Workflow end")
    total_time_ms: Optional[int] = Field(None, description="Total execution time")
    groq_tokens_used: int = Field(0, description="Total GROQ tokens used")
    
    # Workflow status
    workflow_status: str = Field("started", description="Current workflow status")
    workflow_error: Optional[str] = Field(None, description="Workflow-level error")

    class Config:
        arbitrary_types_allowed = True