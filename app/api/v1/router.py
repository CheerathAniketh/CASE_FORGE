from fastapi import APIRouter
from app.api.v1.endpoints import case_studies, auth, health

# Create router
router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
router.include_router(auth.router)
router.include_router(case_studies.router)
router.include_router(health.router)