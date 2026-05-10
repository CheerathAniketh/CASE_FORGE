from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import re

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
        student_id = auth_data.student_id.strip() if auth_data.student_id else ""
        if len(student_id) < 3 or not re.fullmatch(r"[A-Za-z0-9_-]+", student_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid student_id format"
            )

        # Get or create user based on student_id
        await user_service.get_or_create_user(
            student_id=student_id,
            email=auth_data.email
        )
        
        # Create access token
        access_token = create_access_token(student_id=student_id)
        
        return TokenResponse(access_token=access_token)
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )
