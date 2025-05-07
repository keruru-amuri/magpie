"""
User model for the MAGPIE platform.
"""
import enum
from typing import List, Optional

from sqlalchemy import Boolean, Column, Enum, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """
    Enum for user roles.
    """

    ADMIN = "admin"
    MANAGER = "manager"
    ENGINEER = "engineer"
    TECHNICIAN = "technician"
    GUEST = "guest"

    def __str__(self):
        return self.value


class User(BaseModel):
    """
    User model for authentication and authorization.
    """

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.GUEST, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Relationships
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        String representation of the user.

        Returns:
            str: User representation
        """
        return f"<User {self.username} ({self.email})>"
