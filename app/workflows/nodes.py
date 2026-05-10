import json
import time
from typing import Dict, Any
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

# Initialize LangChain GROQ LLM
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model_name=settings.GROQ_MODEL,
    temperature=settings.GROQ_TEMPERATURE,
    max_tokens=settings.GROQ_MAX_TOKENS,
)


class CaseWorkflowNodes:
    """Nodes for LangGraph case generation workflow"""

    @staticmethod
    async def generate_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """
        Node 1: Generate raw case from GROQ
        
        Input: state.input (industry, complexity, etc.)
        Output: state.generated_case_raw, state.generated_case_json, state.groq_tokens_used
        Transitions: Always → validate_case
        """
        logger.info(
            "node_generate_case_start",
            extra={
                "user_id": state.input.user_id,
                "industry": state.input.industry,
                "refinement_attempt": state.refinement_count + 1
            }
        )

        try:
            # Build prompt
            prompt = get_case_generation_prompt(
                industry=state.input.industry,
                complexity=state.input.complexity,
                focus_area=state.input.focus_area,
                time_limit=state.input.time_limit_minutes,
                num_questions=state.input.num_questions
            )

            # Call GROQ via LangChain
            start_time = time.time()
            message = HumanMessage(content=prompt)
            response = await llm.ainvoke([message])
            elapsed_ms = int((time.time() - start_time) * 1000)

            raw_case = response.content

            # Try to parse JSON
            try:
                case_json = json.loads(raw_case)
                parsed_successfully = True
            except json.JSONDecodeError as e:
                case_json = None
                parsed_successfully = False
                logger.warning(
                    "json_parse_failed",
                    extra={
                        "error": str(e),
                        "raw_response_length": len(raw_case)
                    }
                )

            # Extract token usage
            tokens_used = response.response_metadata.get("token_usage", {}).get("completion_tokens", 0)
            input_tokens = response.response_metadata.get("token_usage", {}).get("prompt_tokens", 0)

            logger.info(
                "node_generate_case_success",
                extra={
                    "elapsed_ms": elapsed_ms,
                    "parsed": parsed_successfully,
                    "output_tokens": tokens_used,
                    "input_tokens": input_tokens
                }
            )

            return {
                "generated_case_raw": raw_case,
                "generated_case_json": case_json,
                "groq_tokens_used": state.groq_tokens_used + tokens_used,
                "workflow_status": "generated"
            }

        except Exception as e:
            logger.error(
                "node_generate_case_error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return {
                "generation_error": str(e),
                "workflow_error": f"Generation failed: {str(e)}",
                "workflow_status": "error"
            }

    @staticmethod
    async def validate_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """
        Node 2: Validate generated case quality
        
        Checks:
        - Is it valid JSON?
        - Does it have required fields?
        - Is content length adequate?
        
        Transitions:
        - Valid → save_case
        - Invalid & refinement_count < max → refine_case
        - Invalid & max retries → error
        """
        logger.info(
            "node_validate_case_start",
            extra={
                "user_id": state.input.user_id,
                "has_json": state.generated_case_json is not None
            }
        )

        errors = []
        score = 0.0

        # Check 1: JSON parsing
        if state.generated_case_json is None:
            errors.append("Failed to parse JSON response")
            score += 0
        else:
            score += 0.25
            logger.info("validation_check_json_pass")

        # Check 2: Required fields
        required_fields = [
            "title", "industry", "complexity", "problem_statement",
            "discussion_questions", "solution_framework", "key_learnings"
        ]

        if state.generated_case_json:
            missing_fields = [
                f for f in required_fields
                if f not in state.generated_case_json
                or not state.generated_case_json.get(f)
            ]

            if missing_fields:
                errors.append(f"Missing fields: {', '.join(missing_fields)}")
                logger.warning(
                    "validation_missing_fields",
                    extra={"missing": missing_fields}
                )
            else:
                score += 0.25
                logger.info("validation_check_fields_pass")

            # Check 3: Content length
            title_len = len(state.generated_case_json.get("title", ""))
            problem_len = len(state.generated_case_json.get("problem_statement", ""))

            if title_len < 5:
                errors.append("Title too short")
            else:
                score += 0.15

            if problem_len < 50:
                errors.append("Problem statement too short")
            else:
                score += 0.15

            # Check 4: Questions count
            questions = state.generated_case_json.get("discussion_questions", [])
            if len(questions) < state.input.num_questions:
                errors.append(
                    f"Not enough questions (got {len(questions)}, expected {state.input.num_questions})"
                )
            else:
                score += 0.20

        is_valid = score >= 0.7 and len(errors) == 0

        logger.info(
            "node_validate_case_result",
            extra={
                "score": score,
                "valid": is_valid,
                "num_errors": len(errors),
                "refinements_used": state.refinement_count
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
        Node 3: Refine invalid case
        
        Called if validation fails but we have retries left.
        Transitions: Always → validate_case (retry validation)
        """
        logger.info(
            "node_refine_case_start",
            extra={
                "user_id": state.input.user_id,
                "refinement_attempt": state.refinement_count + 1,
                "max_refinements": state.max_refinements,
                "num_errors": len(state.validation_errors)
            }
        )

        try:
            prompt = get_case_refinement_prompt(
                original_case=state.generated_case_raw,
                validation_errors=state.validation_errors,
                refinement_attempt=state.refinement_count + 1
            )

            start_time = time.time()
            message = HumanMessage(content=prompt)
            response = await llm.ainvoke([message])
            elapsed_ms = int((time.time() - start_time) * 1000)

            raw_case = response.content

            # Try to parse refined JSON
            try:
                case_json = json.loads(raw_case)
                parsed_successfully = True
            except json.JSONDecodeError:
                case_json = None
                parsed_successfully = False
                logger.warning(
                    "refinement_json_parse_failed",
                    extra={"attempt": state.refinement_count + 1}
                )

            tokens_used = response.response_metadata.get("token_usage", {}).get("completion_tokens", 0)

            logger.info(
                "node_refine_case_success",
                extra={
                    "elapsed_ms": elapsed_ms,
                    "parsed": parsed_successfully,
                    "tokens_used": tokens_used
                }
            )

            return {
                "generated_case_raw": raw_case,
                "generated_case_json": case_json,
                "refinement_count": state.refinement_count + 1,
                "groq_tokens_used": state.groq_tokens_used + tokens_used,
                "workflow_status": "refined"
            }

        except Exception as e:
            logger.error(
                "node_refine_case_error",
                extra={
                    "error": str(e),
                    "refinement_attempt": state.refinement_count + 1
                }
            )
            return {
                "workflow_error": f"Refinement failed: {str(e)}",
                "workflow_status": "error"
            }

    @staticmethod
    async def save_case(state: CaseWorkflowState) -> Dict[str, Any]:
        """
        Node 4: Save validated case to database
        
        This node should be called ONLY when is_valid=True
        It just returns the final case (actual DB save happens in case_service)
        
        Transitions: Always → end
        """
        logger.info(
            "node_save_case_start",
            extra={
                "user_id": state.input.user_id,
                "has_case_data": state.generated_case_json is not None
            }
        )

        try:
            from datetime import datetime

            end_time = datetime.utcnow()
            total_time_ms = int((end_time - state.start_time).total_seconds() * 1000)

            logger.info(
                "node_save_case_success",
                extra={
                    "total_time_ms": total_time_ms,
                    "tokens_used": state.groq_tokens_used,
                    "refinements": state.refinement_count
                }
            )

            return {
                "final_case": state.generated_case_json,
                "end_time": end_time,
                "total_time_ms": total_time_ms,
                "workflow_status": "completed"
            }

        except Exception as e:
            logger.error(
                "node_save_case_error",
                extra={"error": str(e)}
            )
            return {
                "workflow_error": f"Save failed: {str(e)}",
                "workflow_status": "error"
            }