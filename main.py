from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from app.db import init_db
from app.api.routes import router as api_router
from app.logger import get_logger
from app.services.groq import GroqService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    Startup: Initialize database, test Groq connection
    Shutdown: Cleanup
    """
    # ===== STARTUP =====
    logger.info("="*60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info("="*60)
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized")
        
        # Test Groq connection
        logger.info("Testing Groq API connection...")
        groq = GroqService()
        connection_ok = await groq.test_connection()
        if connection_ok:
            logger.info("Groq API connection successful")
        else:
            logger.warning("⚠️  Groq API connection test failed")
        
        logger.info(f"Ready at http://{settings.HOST}:{settings.PORT}")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise
    
    yield
    
    # ===== SHUTDOWN =====
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Case study generation engine for professional development",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )