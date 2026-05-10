from langgraph.graph import StateGraph, END
from typing import Dict, Any, Literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.workflows.states import CaseWorkflowState
from app.workflows.nodes import CaseWorkflowNodes
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CaseStudyWorkflow:
    """
    LangGraph workflow for case study generation
    
    Workflow Pipeline:
    1. generate_case: Generate raw case via GROQ
    2. validate_case: Validate quality and completeness
    3. Decision:
       - If valid → save_case → END
       - If invalid & retries left → refine_case → validate_case (retry)
       - If max retries reached → ERROR
    
    This ensures consistent, high-quality case studies at scale.
    """

    def __init__(self, db_session: AsyncSession = None):
        self.db_session = db_session
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the LangGraph state machine"""
        workflow = StateGraph(CaseWorkflowState)

        # Add nodes
        workflow.add_node("generate", CaseWorkflowNodes.generate_case)
        workflow.add_node("validate", CaseWorkflowNodes.validate_case)
        workflow.add_node("refine", CaseWorkflowNodes.refine_case)
        workflow.add_node("save", CaseWorkflowNodes.save_case)
        workflow.add_node("error", self._handle_error)

        # Add edges
        workflow.add_edge("generate", "validate")

        # Conditional edge: based on validation result
        def route_after_validation(state: CaseWorkflowState) -> Literal["save", "refine", "error"]:
            """Route based on validation result"""
            if state.is_valid:
                logger.info(
                    "validation_passed",
                    extra={
                        "user_id": state.input.user_id,
                        "score": state.validation_score
                    }
                )
                return "save"
            elif state.refinement_count < state.max_refinements:
                logger.info(
                    "validation_failed_will_refine",
                    extra={
                        "user_id": state.input.user_id,
                        "attempt": state.refinement_count + 1,
                        "max": state.max_refinements,
                        "errors": state.validation_errors
                    }
                )
                return "refine"
            else:
                logger.error(
                    "validation_failed_max_retries",
                    extra={
                        "user_id": state.input.user_id,
                        "max_refinements": state.max_refinements,
                        "errors": state.validation_errors
                    }
                )
                return "error"

        workflow.add_conditional_edges("validate", route_after_validation)
        workflow.add_edge("refine", "validate")  # Loop back to validate
        workflow.add_edge("save", END)
        workflow.add_edge("error", END)

        # Set entry point
        workflow.set_entry_point("generate")

        return workflow.compile()

    async def execute(self, initial_state: CaseWorkflowState) -> CaseWorkflowState:
        """
        Execute the workflow
        
        Args:
            initial_state: Initial workflow state with user input
            
        Returns:
            Final workflow state with result
        """
        logger.info(
            "workflow_start",
            extra={
                "user_id": initial_state.input.user_id,
                "industry": initial_state.input.industry,
                "complexity": initial_state.input.complexity
            }
        )

        try:
            # Run the graph asynchronously
            final_state_dict = await self.graph.ainvoke(
                initial_state.model_dump(),
                config={"recursion_limit": 10}
            )

            final_state = CaseWorkflowState(**final_state_dict)

            if final_state.workflow_status == "completed":
                logger.info(
                    "workflow_success",
                    extra={
                        "user_id": final_state.input.user_id,
                        "total_time_ms": final_state.total_time_ms,
                        "tokens_used": final_state.groq_tokens_used,
                        "refinements": final_state.refinement_count
                    }
                )
            else:
                logger.error(
                    "workflow_failed",
                    extra={
                        "user_id": final_state.input.user_id,
                        "status": final_state.workflow_status,
                        "error": final_state.workflow_error
                    }
                )

            return final_state

        except Exception as e:
            logger.error(
                "workflow_execution_error",
                extra={
                    "error": str(e),
                    "user_id": initial_state.input.user_id
                }
            )
            raise

    @staticmethod
    async def _handle_error(state: CaseWorkflowState) -> Dict[str, Any]:
        """Handle workflow error state"""
        logger.error(
            "workflow_error_node",
            extra={
                "user_id": state.input.user_id,
                "error": state.workflow_error,
                "validation_errors": state.validation_errors
            }
        )
        return {
            "workflow_status": "error"
        }