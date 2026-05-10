from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1.router import router as api_v1_router
from app.middleware.error_handler import setup_exception_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.database.db import init_db
from app.utils.logger import setup_logging, get_logger

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Startup:
    - Initialize database tables
    - Log startup
    
    Shutdown:
    - Cleanup connections
    - Log shutdown
    """
    # Startup
    logger.info(
        "application_startup",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.VERSION,
            "debug": settings.DEBUG
        }
    )
    
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error(
            "database_initialization_failed",
            extra={"error": str(e)}
        )
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Case study generation engine for professional mindset building",
    version=settings.VERSION,
    lifespan=lifespan
)

# Add CORS middleware
allow_credentials = "*" not in settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Rate Limiting middleware
app.add_middleware(RateLimitMiddleware)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(api_v1_router)


# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Root endpoint
@app.get("/")
async def root(request: Request):
    """Root endpoint (Demo UI)"""
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )