from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.core.security import create_access_token
from app.services.user_service import UserService
from app.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    student_id: str
    email: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(
    auth_data: AuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Simple login endpoint for students.
    Returns a JWT token for the provided student_id.
    """
    user_service = UserService(db)
    
    try:
        # Get or create user based on student_id
        await user_service.get_or_create_user(
            student_id=auth_data.student_id,
            email=auth_data.email
        )
        
        # Create access token
        access_token = create_access_token(student_id=auth_data.student_id)
        
        return TokenResponse(access_token=access_token)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )
