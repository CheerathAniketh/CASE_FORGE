from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.cache import cache_get, cache_set
from app.db import get_db_session
from app.services.case import CaseService
from app.services.workflow import WorkflowService
from app.logger import get_logger
from app.services.leaderboard import LeaderboardService, RankingMetric, DEFAULT_METRIC
logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1")


# ============ REQUEST/RESPONSE MODELS ============

class GenerateCaseRequest(BaseModel):
    user_id: int
    industry: str
    complexity: str
    focus_area: str = None
    time_limit: int = 60


class EvaluateSolutionRequest(BaseModel):
    user_id: int
    case_id: int
    solution: str


# ============ ENDPOINTS ============

@router.get("/leaderboard")
async def get_leaderboard(
    metric: RankingMetric = DEFAULT_METRIC,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
):
    """Get ranked leaderboard by a given metric"""
    service = LeaderboardService(db)
    rankings = await service.get_leaderboard(metric=metric, limit=limit)
    return {
        "success": True,
        "metric": metric,
        "leaderboard": rankings,
    }
@router.post("/cases/generate")
async def generate_case(
    request: GenerateCaseRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Generate a new case study using LangGraph"""
    cache_key = f"case:{request.user_id}:{request.industry}:{request.complexity}:{request.focus_area}"

    cached = await cache_get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit for {cache_key} — returning existing case, not regenerating")
        return cached

    logger.info(f"User {request.user_id} generating case: {request.industry}")

    service = WorkflowService(db)
    result = await service.generate_case_with_workflow(
        user_id=request.user_id,
        industry=request.industry,
        complexity=request.complexity,
        focus_area=request.focus_area,
        time_limit=request.time_limit,
    )

    if not result["success"]:
        logger.error(f"Generation failed: {result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])

    case = result["case"]
    response = {
        "success": True,
        "case_id": case.id,
        "case_uuid": case.uuid,
        "title": case.title,
        "industry": case.industry,
        "complexity": case.complexity.value,
        "case_data": case.case_data,
        "generation_time_ms": result["total_time_ms"],
        "refinements_used": result["refinements_used"],
    }

    await cache_set(cache_key, response, ttl_seconds=10)
    return response

@router.post("/solutions/evaluate")
async def evaluate_solution(
    request: EvaluateSolutionRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Evaluate a student's solution"""
    logger.info(f"User {request.user_id} evaluating solution for case {request.case_id}")
    
    service = CaseService(db)
    result = await service.evaluate_solution(
        user_id=request.user_id,
        case_id=request.case_id,
        solution_text=request.solution,
    )
    
    if not result["success"]:
        logger.error(f"Evaluation failed: {result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "success": True,
        "solution_id": result["solution_id"],
        "scores": result["scores"],
        "feedback": result["feedback"],
    }


@router.get("/cases/{case_id}")
async def get_case(case_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get a specific case study"""
    from app.models import CaseStudy
    
    query = select(CaseStudy).where(CaseStudy.id == case_id)
    result = await db.execute(query)
    case = result.scalars().first()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {
        "success": True,
        "case_id": case.id,
        "title": case.title,
        "industry": case.industry,
        "case_data": case.case_data,
    }


@router.get("/users/{user_id}/cases")
async def get_user_cases(user_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get user's case history"""
    service = CaseService(db)
    cases = await service.get_user_cases(user_id)
    
    return {
        "success": True,
        "user_id": user_id,
        "cases": [
            {
                "id": c.id,
                "uuid": c.uuid,
                "title": c.title,
                "industry": c.industry,
                "complexity": c.complexity.value,
                "created_at": c.created_at.isoformat(),
            }
            for c in cases
        ],
        "total": len(cases),
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "CaseForge API is running",
    }
