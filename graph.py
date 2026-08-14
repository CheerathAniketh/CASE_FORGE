"""
LangGraph Workflow Graph
Builds the state machine with nodes, edges, and conditional routing
"""

from langgraph.graph import StateGraph, END
from typing import Literal

from app.workflows import state
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
    def route_after_validation(state):
        # Safely handle both dictionaries and Pydantic objects using correct state names
        if isinstance(state, dict):
            is_valid = state.get("is_valid", False)
            retries = state.get("refinement_count", 0)
            max_retries = state.get("max_refinements", 2)
        else:
            is_valid = getattr(state, "is_valid", False)
            retries = getattr(state, "refinement_count", 0)
            max_retries = getattr(state, "max_refinements", 2)

        if is_valid:
            return "save"
        elif retries < max_retries:
            return "refine"
        else:
            return "error"

    # Apply the conditional routing
    workflow.add_conditional_edges(
        "validate",
        route_after_validation
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


async def _handle_error(state) -> dict:
    """
    Error handler node
    Called when max refinements exceeded
    """
    # Safely extract values preventing AttributeError crashes
    if isinstance(state, dict):
        user_input = state.get("input", {})
        user_id = user_input.get("user_id") if isinstance(user_input, dict) else getattr(user_input, "user_id", None)
        workflow_error = state.get("workflow_error", "Failed to generate valid case after max refinements")
        validation_errors = state.get("validation_errors", [])
    else:
        user_input = getattr(state, "input", None)
        user_id = getattr(user_input, "user_id", None) if user_input else None
        workflow_error = getattr(state, "workflow_error", "Failed to generate valid case after max refinements")
        validation_errors = getattr(state, "validation_errors", [])

    logger.error(
        "workflow_error_node",
        extra={
            "user_id": user_id,
            "error": workflow_error,
            "validation_errors": validation_errors
        }
    )
    
    return {
        "workflow_status": "error",
        "workflow_error": workflow_error
    }


# Create global graph instance
case_study_graph = build_case_study_graph()