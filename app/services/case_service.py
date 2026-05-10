from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Dict, Any, Optional

from app.workflows.case_workflow import CaseStudyWorkflow
from app.workflows.states import CaseWorkflowState, CaseGenerationInput
from app.database.models import CaseStudy, User, ComplexityEnum
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CaseService:
    """
    Service for case study generation and management.
    
    Orchestrates:
    1. LangGraph workflow (case generation)
    2. Database operations (persistence)
    3. Error handling and logging
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_case(
        self,
        user_id: int,
        industry: str,
        complexity: str,
        focus_area: Optional[str] = None,
        time_limit: int = 60,
        num_questions: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a case study using LangGraph workflow.
        
        This orchestrates:
        1. Create initial workflow state
        2. Execute LangGraph workflow (generate → validate → refine → save)
        3. Save to database
        4. Return result with metadata
        
        Args:
            user_id: User ID generating the case
            industry: Industry for the case
            complexity: Difficulty level
            focus_area: Optional specific focus
            time_limit: Time limit in minutes
            num_questions: Number of questions
            
        Returns:
            Dict with success status and case data or error
        """
        logger.info(
            "case_generation_start",
            extra={
                "user_id": user_id,
                "industry": industry,
                "complexity": complexity
            }
        )

        try:
            # Create initial workflow state
            input_state = CaseGenerationInput(
                industry=industry,
                complexity=complexity,
                focus_area=focus_area,
                time_limit_minutes=time_limit,
                num_questions=num_questions,
                user_id=user_id
            )

            initial_state = CaseWorkflowState(input=input_state)

            # Execute workflow
            logger.info("workflow_execute_start")
            workflow = CaseStudyWorkflow(db_session=self.db)
            final_state = await workflow.execute(initial_state)

            # Check if workflow completed successfully
            if final_state.workflow_status != "completed" or not final_state.final_case:
                logger.error(
                    "case_generation_workflow_failed",
                    extra={
                        "user_id": user_id,
                        "status": final_state.workflow_status,
                        "error": final_state.workflow_error
                    }
                )
                return {
                    "success": False,
                    "error": final_state.workflow_error or "Workflow failed",
                    "validation_errors": final_state.validation_errors
                }

            # Workflow succeeded, now save to database
            logger.info(
                "workflow_completed_saving_to_db",
                extra={
                    "user_id": user_id,
                    "final_case_title": final_state.final_case.get("title", "Unknown")
                }
            )

            case = CaseStudy(
                user_id=user_id,
                title=final_state.final_case.get("title", f"{industry} Case Study"),
                industry=industry,
                complexity=complexity,
                focus_area=focus_area,
                case_data=final_state.final_case,
                generation_time_ms=final_state.total_time_ms,
                model_used="mixtral-8x7b-32768",
                tokens_used=final_state.groq_tokens_used,
                refinement_count=final_state.refinement_count
            )

            self.db.add(case)
            await self.db.commit()
            await self.db.refresh(case)

            logger.info(
                "case_generation_success",
                extra={
                    "user_id": user_id,
                    "case_uuid": case.uuid,
                    "generation_time_ms": final_state.total_time_ms,
                    "tokens_used": final_state.groq_tokens_used,
                    "refinements_used": final_state.refinement_count
                }
            )

            return {
                "success": True,
                "case": case,
                "generation_time_ms": final_state.total_time_ms,
                "tokens_used": final_state.groq_tokens_used,
                "refinements_used": final_state.refinement_count
            }

        except Exception as e:
            logger.error(
                "case_generation_exception",
                extra={
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            await self.db.rollback()
            return {
                "success": False,
                "error": "Internal server error during case generation"
            }

    async def get_case_by_uuid(
        self,
        case_uuid: str,
        user_id: int
    ) -> Optional[CaseStudy]:
        """
        Retrieve a case study by UUID (with user auth check).
        
        Args:
            case_uuid: Case UUID
            user_id: User ID (for auth verification)
            
        Returns:
            CaseStudy object or None
        """
        try:
            query = select(CaseStudy).where(
                (CaseStudy.uuid == case_uuid) & (CaseStudy.user_id == user_id)
            )
            result = await self.db.execute(query)
            case = result.scalars().first()
            
            if not case:
                logger.warning(
                    "case_not_found",
                    extra={"case_uuid": case_uuid, "user_id": user_id}
                )
            
            return case
        
        except Exception as e:
            logger.error(
                "get_case_error",
                extra={"error": str(e), "case_uuid": case_uuid}
            )
            return None

    async def get_user_cases(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get paginated case history for a user.
        
        Args:
            user_id: User ID
            skip: Pagination skip
            limit: Pagination limit
            
        Returns:
            Dict with total count and case list
        """
        try:
            # Get total count
            count_query = select(CaseStudy).where(CaseStudy.user_id == user_id)
            count_result = await self.db.execute(count_query)
            total = len(count_result.scalars().all())

            # Get paginated cases (newest first)
            query = select(CaseStudy).where(
                CaseStudy.user_id == user_id
            ).order_by(
                desc(CaseStudy.created_at)
            ).offset(skip).limit(limit)

            result = await self.db.execute(query)
            cases = result.scalars().all()

            logger.info(
                "user_cases_retrieved",
                extra={
                    "user_id": user_id,
                    "total": total,
                    "returned": len(cases)
                }
            )

            return {
                "total": total,
                "cases": cases,
                "skip": skip,
                "limit": limit
            }

        except Exception as e:
            logger.error(
                "get_user_cases_error",
                extra={"error": str(e), "user_id": user_id}
            )
            return {
                "total": 0,
                "cases": [],
                "skip": skip,
                "limit": limit
            }

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with user statistics
        """
        try:
            query = select(CaseStudy).where(CaseStudy.user_id == user_id)
            result = await self.db.execute(query)
            cases = result.scalars().all()

            if not cases:
                return {
                    "total_cases": 0,
                    "total_tokens_used": 0,
                    "total_generation_time_ms": 0,
                    "avg_generation_time_ms": 0,
                    "industries": []
                }

            total_tokens = sum(c.tokens_used or 0 for c in cases)
            total_time = sum(c.generation_time_ms or 0 for c in cases)
            industries = list(set(c.industry for c in cases))

            return {
                "total_cases": len(cases),
                "total_tokens_used": total_tokens,
                "total_generation_time_ms": total_time,
                "avg_generation_time_ms": total_time // len(cases) if cases else 0,
                "industries": industries
            }

        except Exception as e:
            logger.error(
                "get_user_stats_error",
                extra={"error": str(e), "user_id": user_id}
            )
            return {
                "total_cases": 0,
                "total_tokens_used": 0,
                "total_generation_time_ms": 0,
                "avg_generation_time_ms": 0,
                "industries": []
            }