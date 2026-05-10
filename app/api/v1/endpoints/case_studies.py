from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database.db import get_db
from app.database.schema import (
    CaseStudyGenerateRequest,
    CaseStudyResponse,
    CaseStudyListResponse
)
from app.services.case_service import CaseService
from app.services.user_service import UserService
from app.core.security import get_current_user
from app.utils.logger import get_logger

router = APIRouter(prefix="/case-studies", tags=["case-studies"])
logger = get_logger(__name__)


@router.post("/generate", response_model=CaseStudyResponse, status_code=201)
async def generate_case(
    request: CaseStudyGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Generate a new case study.
    
    This endpoint orchestrates the entire case generation pipeline:
    1. Authenticate user
    2. Get or create user in database
    3. Execute LangGraph workflow:
       - Generate case via GROQ
       - Validate quality (auto-refine if needed, max 2 retries)
       - Save to database
    4. Return complete case study
    
    Expected response time: 1-5 seconds (depending on GROQ latency and refinements)
    
    Args:
        request: Case generation parameters
        db: Database session
        current_user: Authenticated student_id (from JWT)
        
    Returns:
        Generated case study with metadata
        
    Raises:
        400: Invalid request
        401: Unauthorized
        500: Generation failed
    """
    logger.info(
        "endpoint_generate_case",
        extra={
            "student_id": current_user,
            "industry": request.industry,
            "complexity": request.complexity.value
        }
    )

    try:
        # Get or create user
        user_service = UserService(db)
        user = await user_service.get_or_create_user(current_user)

        # Generate case
        case_service = CaseService(db)
        result = await case_service.generate_case(
            user_id=user.id,
            industry=request.industry,
            complexity=request.complexity.value,
            focus_area=request.focus_area,
            time_limit=request.time_limit_minutes or 60,
            num_questions=request.num_questions or 3
        )

        if not result["success"]:
            logger.error(
                "case_generation_failed",
                extra={
                    "student_id": current_user,
                    "error": result.get("error"),
                    "validation_errors": result.get("validation_errors", [])
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to generate case study")
            )

        case = result["case"]

        logger.info(
            "case_generated_response",
            extra={
                "student_id": current_user,
                "case_uuid": case.uuid,
                "generation_time_ms": result.get("generation_time_ms"),
                "tokens_used": result.get("tokens_used"),
                "refinements_used": result.get("refinements_used", 0)
            }
        )

        return CaseStudyResponse.from_orm(case)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "case_generation_exception",
            extra={
                "student_id": current_user,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{case_uuid}", response_model=CaseStudyResponse)
async def get_case(
    case_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific case study by UUID.
    
    Only the user who created the case can retrieve it.
    
    Args:
        case_uuid: Case UUID
        db: Database session
        current_user: Authenticated student_id
        
    Returns:
        Case study details
        
    Raises:
        401: Unauthorized
        404: Case not found
    """
    logger.info(
        "endpoint_get_case",
        extra={
            "student_id": current_user,
            "case_uuid": case_uuid
        }
    )

    try:
        # Get user
        user_service = UserService(db)
        user = await user_service.get_or_create_user(current_user)

        # Get case
        case_service = CaseService(db)
        case = await case_service.get_case_by_uuid(case_uuid, user.id)

        if not case:
            logger.warning(
                "case_not_found",
                extra={
                    "student_id": current_user,
                    "case_uuid": case_uuid
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        return CaseStudyResponse.from_orm(case)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_case_exception",
            extra={
                "student_id": current_user,
                "case_uuid": case_uuid,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/user/history", response_model=CaseStudyListResponse)
async def get_user_history(
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(10, ge=1, le=100, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get user's case study history (paginated).
    
    Returns cases in descending order (newest first).
    
    Args:
        skip: Number of cases to skip
        limit: Number of cases to return (max 100)
        db: Database session
        current_user: Authenticated student_id
        
    Returns:
        List of cases with total count
        
    Raises:
        401: Unauthorized
    """
    logger.info(
        "endpoint_user_history",
        extra={
            "student_id": current_user,
            "skip": skip,
            "limit": limit
        }
    )

    try:
        # Get user
        user_service = UserService(db)
        user = await user_service.get_or_create_user(current_user)

        # Get cases
        case_service = CaseService(db)
        result = await case_service.get_user_cases(
            user_id=user.id,
            skip=skip,
            limit=limit
        )

        logger.info(
            "user_history_retrieved",
            extra={
                "student_id": current_user,
                "total": result["total"],
                "returned": len(result["cases"])
            }
        )

        return CaseStudyListResponse(
            total=result["total"],
            cases=[CaseStudyResponse.from_orm(c) for c in result["cases"]]
        )

    except Exception as e:
        logger.error(
            "get_user_history_exception",
            extra={
                "student_id": current_user,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )