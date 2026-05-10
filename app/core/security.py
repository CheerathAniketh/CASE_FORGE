from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer()


def create_access_token(student_id: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": student_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return student_id"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        student_id: str = payload.get("sub")
        if student_id is None:
            return None
        return student_id
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    student_id = verify_token(token)
    
    if student_id is None:
        logger.warning("Invalid token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return student_id