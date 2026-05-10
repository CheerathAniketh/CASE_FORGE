from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.database.db import get_db
from app.core.security import get_current_user
from app.services.case_service import CaseService
from app.database.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=Any)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the currently authenticated user's profile.
    """
    return {
        "id": current_user.id,
        "student_id": current_user.student_id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


@router.get("/me/stats", response_model=Any)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time statistics for the currently authenticated user.
    Uses CaseService for optimized aggregation queries.
    """
    case_service = CaseService(db)
    stats = await case_service.get_user_stats(current_user.id)
    
    return stats
