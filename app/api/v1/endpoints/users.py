from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.database.db import get_db
from app.core.security import get_current_user
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=Any)
async def get_my_profile(
    student_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the currently authenticated user's profile.
    
    This endpoint verifies the JWT token and returns user details
    from the database based on the student_id in the token.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_student_id(student_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "student_id": user.student_id,
        "email": user.email,
        "created_at": user.created_at
    }


@router.get("/me/stats", response_model=Any)
async def get_user_stats(
    student_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for the currently authenticated user.
    (Placeholder for Phase 1)
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_student_id(student_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # In a real implementation, you'd query the number of case studies, etc.
    # For now, returning dummy stats for the profile view
    return {
        "student_id": student_id,
        "total_case_studies": 0,  # TODO: Connect to CaseService
        "completed_solutions": 0,
        "average_score": 0.0
    }
