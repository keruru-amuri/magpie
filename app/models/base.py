"""
Base model for all database models in the MAGPIE platform.
"""
import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr

from app.core.db.connection import Base


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """
    Base model for all models in the application.
    """
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name automatically from class name.
        
        Returns:
            str: Table name
        """
        return cls.__name__.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            Dict[str, Any]: Model as dictionary
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """
        Create model instance from dictionary.
        
        Args:
            data: Dictionary with model data
            
        Returns:
            BaseModel: Model instance
        """
        return cls(**data)
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Update model instance from dictionary.
        
        Args:
            data: Dictionary with model data
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
