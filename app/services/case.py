import json
from datetime import datetime
from sqlalchemy import select

from app.db import async_session
from app.models import CaseStudy, UserSolution, ComplexityLevel
from app.services.groq import GroqService
from app.prompts import (
    get_case_generation_prompt,
    get_evaluation_prompt,
    get_feedback_prompt,
)
from app.logger import get_logger

logger = get_logger(__name__)


class CaseService:
    """Core business logic for case studies.

    NOTE: no longer takes `db` in the constructor. Each method opens its own
    short-lived session right before/after the Groq call, instead of holding
    one request-scoped session open for the whole request (including the
    multi-second Groq wait).
    """

    def __init__(self):
        self.groq = GroqService()

    async def generate_case(
        self,
        user_id: int,
        industry: str,
        complexity: str,
        focus_area: str = None,
        time_limit: int = 60,
    ) -> dict:
        """
        NOTE: this method appears unused — app/api/routes.py calls
        WorkflowService.generate_case_with_workflow() instead, not this.
        Confirm with your team whether this is dead code before relying on
        it; left functional (and fixed to use the short-session pattern +
        real GROQ_MODEL setting) in case it's used elsewhere.
        """
        logger.info(f"Generating case: {industry} ({complexity})")

        try:
            prompt = get_case_generation_prompt(
                industry=industry,
                complexity=complexity,
                focus_area=focus_area or "General Business",
                time_limit=time_limit,
            )

            start_time = datetime.utcnow()
            case_data = await self.groq.parse_json_response(prompt)
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            try:
                complexity_enum = ComplexityLevel(complexity.lower())
            except ValueError:
                complexity_enum = ComplexityLevel.INTERMEDIATE

            from config import settings

            async with async_session() as session:
                case = CaseStudy(
                    user_id=user_id,
                    title=case_data.get("title", f"{industry} Case Study"),
                    industry=industry,
                    complexity=complexity_enum,
                    focus_area=focus_area or "General",
                    case_data=case_data,
                    generation_time_ms=elapsed_ms,
                    model_used=settings.GROQ_MODEL,  # was hardcoded to a stale model name
                    tokens_used=2048,  # Estimate
                    refinement_count=0,
                )

                session.add(case)
                await session.commit()
                await session.refresh(case)

            logger.info(f"Case generated successfully: {case.uuid}")

            return {
                "success": True,
                "case": case,
                "case_id": case.id,
                "case_uuid": case.uuid,
                "elapsed_ms": elapsed_ms,
            }

        except Exception as e:
            logger.error(f"Case generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def evaluate_solution(
        self,
        user_id: int,
        case_id: int,
        solution_text: str,
    ) -> dict:
        """
        Evaluate a student's solution to a case study.

        Session pattern: short session to fetch the case -> Groq call with
        NO session open -> short session to save the result.
        """
        logger.info(f"Evaluating solution for case {case_id}")

        try:
            # 1. Fetch the case — short-lived session, closed immediately after
            async with async_session() as session:
                query = select(CaseStudy).where(CaseStudy.id == case_id)
                result = await session.execute(query)
                case = result.scalars().first()

            if not case:
                return {
                    "success": False,
                    "error": "Case study not found",
                }

            # 2. Groq call — no DB session open during this
            eval_prompt = get_evaluation_prompt(case.case_data, solution_text)
            evaluation = await self.groq.parse_json_response(eval_prompt)

            scores = {
                "overall": evaluation.get("overall_score", 0),
                "problem_understanding": evaluation.get("problem_understanding", 0),
                "analytical_rigor": evaluation.get("analytical_rigor", 0),
                "business_acumen": evaluation.get("business_acumen", 0),
                "communication": evaluation.get("communication", 0),
                "feasibility": evaluation.get("feasibility", 0),
            }

            # 3. Save the solution — fresh short-lived session
            async with async_session() as session:
                user_solution = UserSolution(
                    user_id=user_id,
                    case_id=case_id,
                    solution_text=solution_text,
                    overall_score=scores["overall"],
                    reasoning_score=scores["analytical_rigor"],
                    communication_score=scores["communication"],
                    business_acumen_score=scores["business_acumen"],
                    feedback_data=evaluation,
                )

                session.add(user_solution)
                await session.commit()
                await session.refresh(user_solution)

            logger.info(f"Solution evaluated: {user_solution.uuid}")

            return {
                "success": True,
                "scores": scores,
                "feedback": evaluation,
                "solution_id": user_solution.id,
            }

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_user_cases(self, user_id: int, limit: int = 10) -> list:
        """Get user's case history. Pure fast read — short-lived session is
        fine here since there's no Groq call in this method at all."""
        try:
            async with async_session() as session:
                query = select(CaseStudy).where(
                    CaseStudy.user_id == user_id
                ).order_by(
                    CaseStudy.created_at.desc()
                ).limit(limit)

                result = await session.execute(query)
                return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get user cases: {str(e)}")
            return []