"""
LangGraph Workflow Graph
Builds the state machine with nodes, edges, and conditional routing
"""

from langgraph.graph import StateGraph, END
from typing import Literal

from app.workflows.state import CaseWorkflowState
from app.workflows.nodes import CaseWorkflowNodes
from app.logger import get_logger

logger = get_logger(__name__)


def build_case_study_graph():
    """
    Build the LangGraph state machine for case study generation
    
    Flow:
    generate → validate → [if valid: save → END]
                       → [if invalid & retries left: refine → validate]
                       → [if max retries: error → END]
    
    This ensures high-quality cases with automatic refinement
    """
    
    workflow = StateGraph(CaseWorkflowState)

    # ===== ADD NODES =====
    workflow.add_node("generate", CaseWorkflowNodes.generate_case)
    workflow.add_node("validate", CaseWorkflowNodes.validate_case)
    workflow.add_node("refine", CaseWorkflowNodes.refine_case)
    workflow.add_node("save", CaseWorkflowNodes.save_case)
    workflow.add_node("error", _handle_error)

    # ===== ADD EDGES =====
    workflow.add_edge("generate", "validate")

    # Conditional edge after validation
    def route_after_validation(state: dict) -> str:
        """
        Router: Decide next step based on validation result
        """
        is_valid = state.get("is_valid", False)
        refinement_count = state.get("refinement_count", 0)
        max_refinements = state.get("max_refinements", 2)
        validation_errors = state.get("validation_errors", [])
        user_id = state.get("input", {}).get("user_id", "unknown")
        
        if is_valid:
            logger.info("validation_passed", extra={"user_id": user_id, "score": state.get("validation_score", 0)})
            return "save"
        elif refinement_count < max_refinements:
            logger.info("validation_failed_will_refine", extra={"user_id": user_id, "attempt": refinement_count + 1, "max": max_refinements})
            return "refine"
        else:
            logger.error("validation_failed_max_retries", extra={"user_id": user_id, "max": max_refinements})
            return "error"
    
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "save": "save",
            "refine": "refine",
            "error": "error"
        }
    )

    # After refinement, go back to validation (loop)
    workflow.add_edge("refine", "validate")

    # End states
    workflow.add_edge("save", END)
    workflow.add_edge("error", END)

    # Set entry point
    workflow.set_entry_point("generate")

    # Compile the graph
    graph = workflow.compile()
    
    logger.info("LangGraph compiled successfully")
    return graph


async def _handle_error(state: dict) -> dict:
    """
    Error handler node
    Called when max refinements exceeded
    """
    logger.error(
        "workflow_error_node",
        extra={
            "user_id": state.input.user_id,
            "error": state.workflow_error,
            "validation_errors": state.validation_errors
        }
    )
    return {
        "workflow_status": "error",
        "workflow_error": "Failed to generate valid case after max refinements"
    }


# Create global graph instance
case_study_graph = build_case_study_graph()