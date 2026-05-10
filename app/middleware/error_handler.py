from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers"""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all uncaught exceptions"""
        logger.error(
            "unhandled_exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error": str(exc),
                "error_type": type(exc).__name__
            }
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if False else "An unexpected error occurred",  # Hide details in production
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError"""
        logger.warning(
            "value_error",
            extra={
                "path": request.url.path,
                "error": str(exc)
            }
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Invalid input",
                "detail": str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }
        )