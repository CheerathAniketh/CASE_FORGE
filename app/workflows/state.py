"""
LangGraph State Definition
Defines the state that flows through all nodes in the workflow
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime


class CaseGenerationInput(BaseModel):
    """Input parameters for case generation"""
    user_id: int
    industry: str
    complexity: str
    focus_area: str
    time_limit: int = 60
    num_questions: int = 3


class CaseWorkflowState(BaseModel):
    """Complete state for the case generation workflow"""
    
    input: CaseGenerationInput
    generated_case_raw: Optional[str] = None
    generated_case_json: Optional[Dict[str, Any]] = None
    is_valid: bool = False
    validation_errors: List[str] = []
    validation_score: float = 0.0
    refinement_count: int = 0
    max_refinements: int = 2
    final_case: Optional[Dict[str, Any]] = None
    workflow_status: str = "pending"
    workflow_error: Optional[str] = None
    start_time: datetime = None
    end_time: Optional[datetime] = None
    total_time_ms: int = 0
    groq_tokens_used: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.start_time is None:
            self.start_time = datetime.utcnow()