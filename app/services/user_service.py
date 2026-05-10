from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.database.models import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user(self, student_id: str, email: Optional[str] = None) -> User:
        """
        Get existing user or create new one with race condition protection.
        """
        try:
            # 1. Try to find existing user (Standard case)
            query = select(User).where(User.student_id == student_id)
            result = await self.db.execute(query)
            user = result.scalars().first()

            if user:
                return user

            # 2. Try to create new user
            user = User(
                student_id=student_id,
                email=email
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info("user_created", extra={"student_id": student_id, "user_id": user.id})
            return user

        except IntegrityError:
            # 3. Handle race condition: user was created by another request between Step 1 and Step 2
            await self.db.rollback()
            logger.info("user_creation_race_condition_handled", extra={"student_id": student_id})
            
            # Try finding them again
            query = select(User).where(User.student_id == student_id)
            result = await self.db.execute(query)
            user = result.scalars().first()
            
            if user:
                return user
            raise  # Should not happen if it was an IntegrityError on student_id

        except Exception as e:
            logger.error("get_or_create_user_error", extra={"error": str(e), "student_id": student_id})
            await self.db.rollback()
            raise

    async def get_user_by_student_id(self, student_id: str) -> Optional[User]:
        """Get user by student_id."""
        try:
            query = select(User).where(User.student_id == student_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error("get_user_error", extra={"error": str(e), "student_id": student_id})
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by internal ID."""
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error("get_user_by_id_error", extra={"error": str(e), "user_id": user_id})
            return None