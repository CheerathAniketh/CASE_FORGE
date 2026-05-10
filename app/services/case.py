import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
    """Core business logic for case studies"""

    def __init__(self, db: AsyncSession):
        self.db = db
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
        Generate a case study using Groq.
        
        Returns:
            {
                "success": bool,
                "case": CaseStudy object or None,
                "error": str if failed
            }
        """
        logger.info(f"Generating case: {industry} ({complexity})")
        
        try:
            # Get prompt and call Groq
            prompt = get_case_generation_prompt(
                industry=industry,
                complexity=complexity,
                focus_area=focus_area or "General Business",
                time_limit=time_limit,
            )
            
            start_time = datetime.utcnow()
            
            # Get JSON response from Groq
            case_data = await self.groq.parse_json_response(prompt)
            
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Convert complexity string to enum
            try:
                complexity_enum = ComplexityLevel(complexity.lower())
            except ValueError:
                complexity_enum = ComplexityLevel.INTERMEDIATE
            
            # Create database record
            case = CaseStudy(
                user_id=user_id,
                title=case_data.get("title", f"{industry} Case Study"),
                industry=industry,
                complexity=complexity_enum,
                focus_area=focus_area or "General",
                case_data=case_data,
                generation_time_ms=elapsed_ms,
                model_used="mixtral-8x7b-32768",
                tokens_used=2048,  # Estimate
                refinement_count=0,
            )
            
            self.db.add(case)
            await self.db.commit()
            await self.db.refresh(case)
            
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
            await self.db.rollback()
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
        
        Returns:
            {
                "success": bool,
                "scores": {
                    "overall": float,
                    "reasoning": float,
                    ...
                },
                "feedback": {...},
                "error": str if failed
            }
        """
        logger.info(f"Evaluating solution for case {case_id}")
        
        try:
            # Get the case
            query = select(CaseStudy).where(CaseStudy.id == case_id)
            result = await self.db.execute(query)
            case = result.scalars().first()
            
            if not case:
                return {
                    "success": False,
                    "error": "Case study not found",
                }
            
            # Get evaluation from Groq
            eval_prompt = get_evaluation_prompt(case.case_data, solution_text)
            evaluation = await self.groq.parse_json_response(eval_prompt)
            
            # Extract scores
            scores = {
                "overall": evaluation.get("overall_score", 0),
                "problem_understanding": evaluation.get("problem_understanding", 0),
                "analytical_rigor": evaluation.get("analytical_rigor", 0),
                "business_acumen": evaluation.get("business_acumen", 0),
                "communication": evaluation.get("communication", 0),
                "feasibility": evaluation.get("feasibility", 0),
            }
            
            # Save solution record
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
            
            self.db.add(user_solution)
            await self.db.commit()
            await self.db.refresh(user_solution)
            
            logger.info(f"Solution evaluated: {user_solution.uuid}")
            
            return {
                "success": True,
                "scores": scores,
                "feedback": evaluation,
                "solution_id": user_solution.id,
            }
        
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def get_user_cases(self, user_id: int, limit: int = 10) -> list:
        """Get user's case history"""
        try:
            query = select(CaseStudy).where(
                CaseStudy.user_id == user_id
            ).order_by(
                CaseStudy.created_at.desc()
            ).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        
        except Exception as e:
            logger.error(f"Failed to get user cases: {str(e)}")
            return []