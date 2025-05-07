"""
Document Metadata Model for the MAGPIE platform.

This module defines the data models for document metadata, including
standardized formats, taxonomy, and classification systems.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.base import Base


class MetadataStandard(str, Enum):
    """Metadata standards supported by the system."""
    ATA = "ata"
    S1000D = "s1000d"
    DITA = "dita"
    CUSTOM = "custom"


class DocumentMetadata(Base):
    """
    Document metadata model for storing standardized metadata.
    """
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), nullable=False, index=True, unique=True)
    standard = Column(String(50), nullable=False, default=MetadataStandard.CUSTOM)
    metadata_content = Column(JSONB, nullable=False, default={})  # Renamed from 'metadata' to avoid SQLAlchemy reserved name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "standard": self.standard,
            "metadata": self.metadata_content,  # Use renamed field but keep the same key in the dict
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DocumentTag(Base):
    """
    Document tag model for taxonomy and classification.
    """
    __tablename__ = "document_tag"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DocumentAudit(Base):
    """
    Document audit model for tracking document validation and compliance.
    """
    __tablename__ = "document_audit"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), nullable=False, index=True)
    audit_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "audit_type": self.audit_type,
            "status": self.status,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        }


class DocumentTaxonomy(Base):
    """
    Document taxonomy model for hierarchical classification.
    """
    __tablename__ = "document_taxonomy"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("document_taxonomy.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Self-referential relationship
    children = relationship("DocumentTaxonomy",
                           backref="parent",
                           remote_side=[id],
                           cascade="all, delete-orphan")

    def to_dict(self, include_children: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_children and self.children:
            result["children"] = [child.to_dict(include_children=True) for child in self.children]

        return result


class DocumentTaxonomyAssignment(Base):
    """
    Document taxonomy assignment model for associating documents with taxonomy nodes.
    """
    __tablename__ = "document_taxonomy_assignment"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), nullable=False, index=True)
    taxonomy_id = Column(Integer, ForeignKey("document_taxonomy.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    taxonomy = relationship("DocumentTaxonomy")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "taxonomy_id": self.taxonomy_id,
            "taxonomy_name": self.taxonomy.name if self.taxonomy else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
