"""
LangGraph Nodes
Each node is a step in the case generation workflow
"""

import json
import re
import asyncio
from datetime import datetime
from typing import Dict, Any

from app.workflows.state import CaseWorkflowState
from app.services.groq import GroqService
from app.prompts import (
    get_case_generation_prompt,
    get_evaluation_prompt,
)
from app.logger import get_logger

logger = get_logger(__name__)


class CaseWorkflowNodes:
    """All nodes for the case generation workflow"""

    @staticmethod
    async def generate_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """
        Node 1: Generate raw case from Groq
        
        Input: state with user input (industry, complexity, focus)
        Output: raw case text + parsed JSON
        """
        logger.info(
            "node_generate_case_start",
            extra={
                "user_id": state.input.user_id,
                "industry": state.input.industry,
                "refinement_attempt": state.refinement_count
            }
        )

        try:
            groq = GroqService()
            
            prompt = get_case_generation_prompt(
                industry=state.input.industry,
                complexity=state.input.complexity,
                focus_area=state.input.focus_area,
                time_limit=state.input.time_limit,
            )

            # Call Groq
            raw_response = await groq.call(prompt)
            
            # Parse JSON
            cleaned_response = _clean_json_response(raw_response)
            
            try:
                case_json = json.loads(cleaned_response)
                is_valid_json = True
            except json.JSONDecodeError as e:
                logger.warning(
                    "json_decode_error",
                    extra={"error": str(e), "preview": raw_response[:100]}
                )
                case_json = None
                is_valid_json = False

            return {
                "generated_case_raw": raw_response,
                "generated_case_json": case_json,
                "groq_tokens_used": state.groq_tokens_used + 2048,  # estimate
                "workflow_status": "generated"
            }

        except Exception as e:
            logger.error(
                "node_generate_case_error",
                extra={"error": str(e)}
            )
            return {
                "workflow_error": f"Generation failed: {str(e)}",
                "workflow_status": "error"
            }

    @staticmethod
    async def validate_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """
        Node 2: Validate generated case quality
        
        Checks:
        - Required fields present
        - Content depth (problem statement length)
        - Sufficient questions
        """
        logger.info(
            "node_validate_case_start",
            extra={
                "user_id": state.input.user_id,
                "has_json": state.generated_case_json is not None
            }
        )

        # If JSON parsing failed
        if state.generated_case_json is None:
            return {
                "is_valid": False,
                "validation_errors": ["Invalid JSON format from LLM"],
                "validation_score": 0.0,
                "workflow_status": "validated"
            }

        errors = []
        score = 0.0
        case = state.generated_case_json

        # Check required fields
        required_fields = [
            "title",
            "industry",
            "company_name",
            "scenario_overview",
            "key_metrics",
            "discussion_questions",
            "solution_framework"
        ]

        missing = [f for f in required_fields if not case.get(f)]
        if missing:
            errors.append(f"Missing fields: {', '.join(missing)}")
        else:
            score += 0.3

        # Check content depth
        scenario = case.get("scenario_overview", "")
        if len(scenario) < 150:
            errors.append(f"Scenario too brief ({len(scenario)} chars, need 150+)")
        else:
            score += 0.3

        # Check questions count
        questions = case.get("discussion_questions", [])
        if len(questions) < state.input.num_questions:
            errors.append(
                f"Insufficient questions ({len(questions)}, need {state.input.num_questions})"
            )
        else:
            score += 0.4

        is_valid = len(errors) == 0 and score >= 0.7

        logger.info(
            "node_validate_case_result",
            extra={
                "is_valid": is_valid,
                "score": score,
                "errors": errors
            }
        )

        return {
            "is_valid": is_valid,
            "validation_errors": errors,
            "validation_score": score,
            "workflow_status": "validated"
        }

    @staticmethod
    async def refine_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """
        Node 3: Refine invalid case based on validation errors
        
        If case fails validation, use Groq to improve it
        """
        logger.info(
            "node_refine_case_start",
            extra={
                "attempt": state.refinement_count + 1,
                "errors": state.validation_errors
            }
        )

        try:
            groq = GroqService()
            
            # Build refinement prompt
            refinement_prompt = f"""
The case study you generated had these issues:
{chr(10).join([f"- {e}" for e in state.validation_errors])}

Original case:
{json.dumps(state.generated_case_json, indent=2)[:500]}...

Please improve the case by:
1. Expanding the scenario_overview (at least 150 characters)
2. Ensuring all required fields are filled
3. Adding more discussion questions if needed
4. Making it more realistic and detailed

{get_case_generation_prompt(
    industry=state.input.industry,
    complexity=state.input.complexity,
    focus_area=state.input.focus_area,
    time_limit=state.input.time_limit,
)}
"""

            raw_response = await groq.call(refinement_prompt)
            cleaned_response = _clean_json_response(raw_response)

            try:
                case_json = json.loads(cleaned_response)
            except json.JSONDecodeError:
                case_json = None

            return {
                "generated_case_raw": raw_response,
                "generated_case_json": case_json,
                "refinement_count": state.refinement_count + 1,
                "groq_tokens_used": state.groq_tokens_used + 2048,
                "workflow_status": "refined"
            }

        except Exception as e:
            logger.error(
                "node_refine_case_error",
                extra={"error": str(e)}
            )
            return {
                "workflow_error": f"Refinement failed: {str(e)}",
                "workflow_status": "error"
            }

    @staticmethod
    async def save_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """
        Node 4: Finalize and prepare case for saving
        
        Sets final output and completion status
        """
        logger.info(
            "node_save_case",
            extra={
                "user_id": state.input.user_id,
                "case_title": state.generated_case_json.get("title", "Unknown")
            }
        )

        end_time = datetime.utcnow()
        total_time_ms = int((end_time - state.start_time).total_seconds() * 1000)

        return {
            "final_case": state.generated_case_json,
            "end_time": end_time,
            "total_time_ms": total_time_ms,
            "workflow_status": "completed"
        }


def _clean_json_response(text: str) -> str:
    """
    Clean LLM response to extract valid JSON
    Handles markdown code blocks and whitespace
    """
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()