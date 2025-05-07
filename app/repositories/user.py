"""
User repository for the MAGPIE platform.
"""
import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """
    Repository for User model.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            Optional[User]: User or None if not found
        """
        try:
            query = select(User).where(User.email == email)
            result = self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            Optional[User]: User or None if not found
        """
        try:
            query = select(User).where(User.username == username)
            result = self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None

    def get_by_role(self, role: UserRole) -> List[User]:
        """
        Get users by role.

        Args:
            role: User role

        Returns:
            List[User]: List of users
        """
        try:
            query = select(User).where(User.role == role)
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting users by role: {str(e)}")
            return []

    def get_active_users(self) -> List[User]:
        """
        Get active users.

        Returns:
            List[User]: List of active users
        """
        try:
            query = select(User).where(User.is_active == True)
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting active users: {str(e)}")
            return []

    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate user.

        Args:
            user_id: User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False

            user.is_active = False
            self.session.flush()

            # Update cache
            self._cache_set(user)

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deactivating user: {str(e)}")
            return False

    def activate_user(self, user_id: int) -> bool:
        """
        Activate user.

        Args:
            user_id: User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False

            user.is_active = True
            self.session.flush()

            # Update cache
            self._cache_set(user)

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error activating user: {str(e)}")
            return False

    def update_role(self, user_id: int, role: UserRole) -> bool:
        """
        Update user role.

        Args:
            user_id: User ID
            role: New role

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False

            user.role = role
            self.session.flush()

            # Update cache
            self._cache_set(user)

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating user role: {str(e)}")
            return False

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get multiple users with pagination.

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List[User]: List of users
        """
        return self.get_all(limit=limit, offset=skip)
