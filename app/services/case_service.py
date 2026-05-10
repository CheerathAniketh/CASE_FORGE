from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Dict, Any, Optional

from app.core.config import settings
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

            # Convert string complexity to Enum member
            try:
                comp_enum = ComplexityEnum(complexity.lower())
            except ValueError:
                comp_enum = ComplexityEnum.INTERMEDIATE

            case = CaseStudy(
                user_id=user_id,
                title=final_state.final_case.get("title", f"{industry} Case Study"),
                industry=industry,
                complexity=comp_enum,
                focus_area=focus_area,
                case_data=final_state.final_case,
                generation_time_ms=final_state.total_time_ms,
                model_used=settings.GROQ_MODEL,
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
        """
        try:
            query = select(CaseStudy).where(
                (CaseStudy.uuid == case_uuid) & (CaseStudy.user_id == user_id)
            )
            result = await self.db.execute(query)
            case = result.scalars().first()
            
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
        Get paginated case history for a user using optimized count.
        """
        try:
            # Get total count using aggregation (Optimized)
            count_query = select(func.count()).select_from(CaseStudy).where(CaseStudy.user_id == user_id)
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0

            # Get paginated cases (newest first)
            query = select(CaseStudy).where(
                CaseStudy.user_id == user_id
            ).order_by(
                desc(CaseStudy.created_at)
            ).offset(skip).limit(limit)

            result = await self.db.execute(query)
            cases = result.scalars().all()

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
        Get statistics for a user using database aggregation.
        """
        try:
            # Optimized aggregation query
            stats_query = select(
                func.count(CaseStudy.id).label("total_cases"),
                func.sum(CaseStudy.tokens_used).label("total_tokens"),
                func.sum(CaseStudy.generation_time_ms).label("total_time"),
                func.avg(CaseStudy.generation_time_ms).label("avg_time")
            ).where(CaseStudy.user_id == user_id)
            
            stats_result = await self.db.execute(stats_query)
            stats = stats_result.one()

            if not stats.total_cases:
                return {
                    "total_cases": 0,
                    "total_tokens_used": 0,
                    "total_generation_time_ms": 0,
                    "avg_generation_time_ms": 0,
                    "industries": []
                }

            # Get distinct industries
            ind_query = select(CaseStudy.industry).where(CaseStudy.user_id == user_id).distinct()
            ind_result = await self.db.execute(ind_query)
            industries = [r for r in ind_result.scalars().all()]

            return {
                "total_cases": stats.total_cases,
                "total_tokens_used": int(stats.total_tokens or 0),
                "total_generation_time_ms": int(stats.total_time or 0),
                "avg_generation_time_ms": int(stats.avg_time or 0),
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