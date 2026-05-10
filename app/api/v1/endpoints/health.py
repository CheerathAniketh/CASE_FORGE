from fastapi import APIRouter, status
from datetime import datetime

from app.database.db import check_db_connection
from app.database.schema import HealthResponse
from app.utils.logger import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    
    Checks:
    - API is running
    - Database is connected
    
    Returns:
        Health status with component status
    """
    try:
        # Check database
        db_ok = await check_db_connection()
        db_status = "ok" if db_ok else "error"

        logger.info(
            "health_check",
            extra={
                "database": db_status
            }
        )

        return HealthResponse(
            status="ok" if db_ok else "degraded",
            database=db_status,
            groq="skipped",
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
            groq="skipped",
            timestamp=datetime.utcnow()
        )