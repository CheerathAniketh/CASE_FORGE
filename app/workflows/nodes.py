import json
import time
import re
import asyncio
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.workflows.states import CaseWorkflowState
from app.utils.prompts import (
    get_case_generation_prompt,
    get_case_validation_prompt,
    get_case_refinement_prompt
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize LangChain GROQ LLM (Lazy initialization inside nodes is better, but this is fine for MVP)
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model_name=settings.GROQ_MODEL,
    temperature=settings.GROQ_TEMPERATURE,
    max_tokens=settings.GROQ_MAX_TOKENS,
)


def clean_json_response(text: str) -> str:
    """
    Cleans LLM response to extract valid JSON.
    Handles markdown code blocks (```json ... ```) and leading/trailing whitespace.
    """
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()


class CaseWorkflowNodes:
    """Nodes for LangGraph case generation workflow"""

    @staticmethod
    async def generate_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """Node 1: Generate raw case from GROQ"""
        logger.info(
            "node_generate_case_start",
            extra={
                "user_id": state.input.user_id,
                "industry": state.input.industry,
                "refinement_attempt": state.refinement_count
            }
        )

        try:
            prompt = get_case_generation_prompt(
                industry=state.input.industry,
                complexity=state.input.complexity,
                focus_area=state.input.focus_area,
                time_limit=state.input.time_limit_minutes,
                num_questions=state.input.num_questions
            )

            start_time = time.time()
            message = HumanMessage(content=prompt)
            response = await asyncio.wait_for(
                llm.ainvoke([message]),
                timeout=settings.GROQ_TIMEOUT
            )
            elapsed_ms = int((time.time() - start_time) * 1000)

            raw_case = response.content
            cleaned_case = clean_json_response(raw_case)

            try:
                case_json = json.loads(cleaned_case)
            except json.JSONDecodeError as e:
                case_json = None
                logger.warning(
                    "json_parse_failed",
                    extra={
                        "error": str(e),
                        "raw_preview": raw_case[:100]
                    }
                )

            tokens_used = response.response_metadata.get("token_usage", {}).get("completion_tokens", 0)

            return {
                "generated_case_raw": raw_case,
                "generated_case_json": case_json,
                "groq_tokens_used": state.groq_tokens_used + tokens_used,
                "workflow_status": "generated"
            }

        except Exception as e:
            logger.error("node_generate_case_error", extra={"error": str(e)})
            return {
                "workflow_error": f"Generation failed: {str(e)}",
                "workflow_status": "error"
            }

    @staticmethod
    async def validate_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """Node 2: Validate generated case quality"""
        if state.generated_case_json is None:
            return {
                "is_valid": False,
                "validation_errors": ["Invalid JSON format"],
                "validation_score": 0.0,
                "workflow_status": "validated"
            }

        errors = []
        score = 0.0
        case = state.generated_case_json

        # Check fields
        required_fields = [
            "title", "industry", "complexity", "problem_statement",
            "discussion_questions", "solution_framework", "key_learnings"
        ]
        
        missing = [f for f in required_fields if not case.get(f)]
        if missing:
            errors.append(f"Missing required fields: {', '.join(missing)}")
        else:
            score += 0.4

        # Check content depth
        if len(case.get("problem_statement", "")) < 100:
            errors.append("Problem statement is too brief")
        else:
            score += 0.3

        # Check questions
        questions = case.get("discussion_questions", [])
        if len(questions) < state.input.num_questions:
            errors.append(f"Insufficient questions (got {len(questions)}, expected {state.input.num_questions})")
        else:
            score += 0.3

        is_valid = len(errors) == 0 and score >= 0.7

        return {
            "is_valid": is_valid,
            "validation_errors": errors,
            "validation_score": score,
            "workflow_status": "validated"
        }

    @staticmethod
    async def refine_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """Node 3: Refine invalid case"""
        logger.info("node_refine_case_start", extra={"attempt": state.refinement_count + 1})

        try:
            prompt = get_case_refinement_prompt(
                original_case=state.generated_case_raw,
                validation_errors=state.validation_errors,
                refinement_attempt=state.refinement_count + 1
            )

            message = HumanMessage(content=prompt)
            response = await asyncio.wait_for(
                llm.ainvoke([message]),
                timeout=settings.GROQ_TIMEOUT
            )
            
            raw_case = response.content
            cleaned_case = clean_json_response(raw_case)

            try:
                case_json = json.loads(cleaned_case)
            except json.JSONDecodeError:
                case_json = None

            tokens_used = response.response_metadata.get("token_usage", {}).get("completion_tokens", 0)

            return {
                "generated_case_raw": raw_case,
                "generated_case_json": case_json,
                "refinement_count": state.refinement_count + 1,
                "groq_tokens_used": state.groq_tokens_used + tokens_used,
                "workflow_status": "refined"
            }

        except Exception as e:
            logger.error("node_refine_case_error", extra={"error": str(e)})
            return {
                "workflow_error": f"Refinement failed: {str(e)}",
                "workflow_status": "error"
            }

    @staticmethod
    async def save_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """Node 4: Finalize case state"""
        from datetime import datetime
        
        end_time = datetime.utcnow()
        total_time_ms = int((end_time - state.start_time).total_seconds() * 1000)

        return {
            "final_case": state.generated_case_json,
            "end_time": end_time,
            "total_time_ms": total_time_ms,
            "workflow_status": "completed"
        }