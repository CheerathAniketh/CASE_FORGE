from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database.db import get_db, check_db_connection
from app.database.schema import HealthResponse
from app.services.groq_service import GroqService
from app.utils.logger import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    
    Checks:
    - API is running
    - Database is connected
    - GROQ API is accessible
    
    Returns:
        Health status with component status
    """
    try:
        # Check database
        db_ok = await check_db_connection()
        db_status = "ok" if db_ok else "error"

        # Check GROQ
        groq_service = GroqService()
        groq_ok = await groq_service.test_connection()
        groq_status = "ok" if groq_ok else "error"

        logger.info(
            "health_check",
            extra={
                "database": db_status,
                "groq": groq_status
            }
        )

        return HealthResponse(
            status="ok" if db_ok and groq_ok else "degraded",
            database=db_status,
            groq=groq_status,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(
            "health_check_error",
            extra={"error": str(e)}
        )
        return HealthResponse(
            status="error",
            database="error",
            groq="error",
            timestamp=datetime.utcnow()
        )