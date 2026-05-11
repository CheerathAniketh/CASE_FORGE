"""
Workflow Service
Executes the LangGraph state machine for case generation
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.workflows.state import CaseWorkflowState, CaseGenerationInput
from app.models import CaseStudy, ComplexityLevel
from app.logger import get_logger
from graph import case_study_graph

logger = get_logger(__name__)


class WorkflowService:
    """
    Service that executes LangGraph workflow
    Handles: generation → validation → refinement → saving
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph = case_study_graph

    async def generate_case_with_workflow(
        self,
        user_id: int,
        industry: str,
        complexity: str,
        focus_area: str,
        time_limit: int = 60,
    ) -> dict:
        """
        Execute LangGraph workflow to generate a case study
        
        Returns:
            {
                "success": bool,
                "case": CaseStudy or None,
                "error": str if failed,
                "refinements_used": int,
                "total_time_ms": int
            }
        """
        
        logger.info(
            "workflow_generation_start",
            extra={
                "user_id": user_id,
                "industry": industry,
                "complexity": complexity,
                "focus_area": focus_area
            }
        )

        try:
            # Create initial state
            input_state = CaseGenerationInput(
                user_id=user_id,
                industry=industry,
                complexity=complexity,
                focus_area=focus_area,
                time_limit=time_limit,
                num_questions=3
            )

            initial_state = CaseWorkflowState(input=input_state)

            # Execute the graph
            logger.info("workflow_execution_start")
            
            final_state_dict = await self.graph.ainvoke(
                initial_state.model_dump(),
                {"recursion_limit": 10}
            )

            final_state = CaseWorkflowState(**final_state_dict)

            logger.info(
                "workflow_execution_complete",
                extra={
                    "status": final_state.workflow_status,
                    "refinements": final_state.refinement_count,
                    "total_time_ms": final_state.total_time_ms
                }
            )

            # Check if workflow succeeded
            if final_state.workflow_status != "completed" or not final_state.final_case:
                logger.error(
                    "workflow_failed",
                    extra={
                        "status": final_state.workflow_status,
                        "error": final_state.workflow_error,
                        "validation_errors": final_state.validation_errors
                    }
                )
                return {
                    "success": False,
                    "error": final_state.workflow_error or "Workflow failed",
                    "validation_errors": final_state.validation_errors,
                    "refinements_used": final_state.refinement_count
                }

            # Save to database
            logger.info(
                "workflow_saving_to_db",
                extra={
                    "user_id": user_id,
                    "case_title": final_state.final_case.get("title", "Unknown")
                }
            )

            try:
                comp_enum = ComplexityLevel(complexity.lower())
            except ValueError:
                comp_enum = ComplexityLevel.INTERMEDIATE

            case = CaseStudy(
                user_id=user_id,
                title=final_state.final_case.get("title", f"{industry} Case Study"),
                industry=industry,
                complexity=comp_enum,
                focus_area=focus_area,
                case_data=final_state.final_case,
                generation_time_ms=final_state.total_time_ms,
                model_used="llama-3.3-70b-versatile",
                tokens_used=final_state.groq_tokens_used,
                refinement_count=final_state.refinement_count
            )

            self.db.add(case)
            await self.db.commit()
            await self.db.refresh(case)

            logger.info(
                "case_saved_successfully",
                extra={
                    "case_id": case.id,
                    "case_uuid": case.uuid,
                    "total_time_ms": final_state.total_time_ms,
                    "refinements_used": final_state.refinement_count
                }
            )

            return {
                "success": True,
                "case": case,
                "case_id": case.id,
                "case_uuid": case.uuid,
                "refinements_used": final_state.refinement_count,
                "total_time_ms": final_state.total_time_ms,
                "tokens_used": final_state.groq_tokens_used
            }

        except Exception as e:
            logger.error(
                "workflow_generation_exception",
                extra={
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            await self.db.rollback()
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "error_type": type(e).__name__
            }