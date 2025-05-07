"""
Document relationship models for the MAGPIE platform.

This module defines models for document relationships, versions, and dependencies.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Union, Tuple

# Helper function for timezone-aware UTC timestamps
def utcnow():
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Table, Text, Enum as SQLEnum, JSON, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

# Use JSONB directly instead of JSONBType
JSONBType = JSONB


class ReferenceType(str, Enum):
    """
    Enum for reference types.
    """
    CITATION = "citation"  # Document cites another document
    SUPERSEDES = "supersedes"  # Document supersedes another document
    SUPPLEMENTS = "supplements"  # Document supplements another document
    RELATED = "related"  # Documents are related
    IMPLEMENTS = "implements"  # Document implements requirements from another document
    CONFLICTS = "conflicts"  # Document conflicts with another document


class DocumentVersion(BaseModel):
    """
    Document version model for tracking document versions.
    """
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    content_hash = Column(String(255), nullable=True)  # Hash of document content for integrity
    changes = Column(JSONBType, nullable=True)  # Changes from previous version
    meta_data = Column(JSONBType, nullable=True)

    # Relationships
    references = relationship(
        "DocumentReference",
        foreign_keys="[DocumentReference.source_version_id]",
        back_populates="source_version",
        cascade="all, delete-orphan"
    )
    referenced_by = relationship(
        "DocumentReference",
        foreign_keys="[DocumentReference.target_version_id]",
        back_populates="target_version",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('document_id', 'version', name='uix_document_version'),
    )


class DocumentReference(BaseModel):
    """
    Document reference model for tracking references between documents.
    """
    id = Column(Integer, primary_key=True, index=True)
    source_document_id = Column(String(255), nullable=False, index=True)
    target_document_id = Column(String(255), nullable=False, index=True)
    source_version_id = Column(Integer, ForeignKey("document_version.id"), nullable=True)
    target_version_id = Column(Integer, ForeignKey("document_version.id"), nullable=True)
    reference_type = Column(SQLEnum(ReferenceType), nullable=False)
    source_section_id = Column(String(255), nullable=True)  # Section in source document
    target_section_id = Column(String(255), nullable=True)  # Section in target document
    context = Column(Text, nullable=True)  # Context of the reference
    relevance_score = Column(Float, default=1.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    meta_data = Column(JSONBType, nullable=True)

    # Relationships
    source_version = relationship(
        "DocumentVersion",
        foreign_keys=[source_version_id],
        back_populates="references"
    )
    target_version = relationship(
        "DocumentVersion",
        foreign_keys=[target_version_id],
        back_populates="referenced_by"
    )

    __table_args__ = (
        UniqueConstraint(
            'source_document_id', 'target_document_id',
            'source_version_id', 'target_version_id',
            'source_section_id', 'target_section_id',
            name='uix_document_reference'
        ),
    )


class DocumentUpdateNotification(BaseModel):
    """
    Document update notification model for tracking document updates.
    """
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey("document_version.id"), nullable=False)
    notification_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), nullable=True)  # e.g., "high", "medium", "low"
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    affected_documents = Column(JSONBType, nullable=True)  # List of affected document IDs
    meta_data = Column(JSONBType, nullable=True)

    # Relationships
    version = relationship("DocumentVersion")


class DocumentAnalytics(BaseModel):
    """
    Document analytics model for tracking document usage and references.
    """
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), nullable=False, index=True)
    reference_count = Column(Integer, default=0, nullable=False)  # Number of times referenced
    view_count = Column(Integer, default=0, nullable=False)  # Number of times viewed
    last_referenced_at = Column(DateTime, nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)
    reference_distribution = Column(JSONBType, nullable=True)  # Distribution of reference types
    meta_data = Column(JSONBType, nullable=True)

    __table_args__ = (
        UniqueConstraint('document_id', name='uix_document_analytics'),
    )


class DocumentConflict(BaseModel):
    """
    Document conflict model for tracking conflicts between documents.
    """
    id = Column(Integer, primary_key=True, index=True)
    document_id_1 = Column(String(255), nullable=False, index=True)
    document_id_2 = Column(String(255), nullable=False, index=True)
    conflict_type = Column(String(100), nullable=False)  # e.g., "content", "procedure", "requirement"
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)  # e.g., "high", "medium", "low"
    status = Column(String(50), default="open", nullable=False)  # e.g., "open", "resolved", "ignored"
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    meta_data = Column(JSONBType, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            'document_id_1', 'document_id_2', 'conflict_type',
            name='uix_document_conflict'
        ),
    )
