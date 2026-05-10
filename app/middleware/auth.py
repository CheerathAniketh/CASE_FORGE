from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.database.schema import AuthRequest, AuthResponse
from app.services.user_service import UserService
from app.core.security import create_access_token
from app.core.config import settings
from app.utils.logger import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/login", response_model=AuthResponse)
async def login(
    request: AuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint - create JWT token for a student.
    
    For MVP, simple student_id based authentication (no password).
    Generates JWT token valid for 24 hours.
    
    Args:
        request: AuthRequest with student_id
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        400: Invalid student_id
        500: Internal error
    """
    logger.info(
        "endpoint_login",
        extra={"student_id": request.student_id}
    )

    try:
        # Validate student_id
        if not request.student_id or len(request.student_id) < 1:
            logger.warning(
                "login_invalid_student_id",
                extra={"student_id": request.student_id}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid student_id"
            )

        # Get or create user
        user_service = UserService(db)
        user = await user_service.get_or_create_user(request.student_id)

        # Create token
        token = create_access_token(request.student_id)

        logger.info(
            "login_success",
            extra={
                "student_id": request.student_id,
                "user_id": user.id,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        )

        return AuthResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "login_exception",
            extra={
                "student_id": request.student_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )