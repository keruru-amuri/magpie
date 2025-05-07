"""
Document relationship service for the MAGPIE platform.

This module provides services for managing document relationships,
versions, dependencies, and cross-references.
"""
import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from app.models.document_relationship import (
    DocumentVersion, DocumentReference, DocumentUpdateNotification,
    DocumentAnalytics, DocumentConflict, ReferenceType
)
from app.repositories.document_relationship_repository import (
    DocumentVersionRepository, DocumentReferenceRepository,
    DocumentNotificationRepository, DocumentConflictRepository,
    DocumentAnalyticsRepository
)
from app.core.db.connection import DatabaseConnectionFactory

# Configure logging
logger = logging.getLogger(__name__)


class DocumentRelationshipService:
    """
    Service for managing document relationships.
    """

    def __init__(
        self,
        version_repo: Optional[DocumentVersionRepository] = None,
        reference_repo: Optional[DocumentReferenceRepository] = None,
        notification_repo: Optional[DocumentNotificationRepository] = None,
        conflict_repo: Optional[DocumentConflictRepository] = None,
        analytics_repo: Optional[DocumentAnalyticsRepository] = None
    ):
        """
        Initialize document relationship service.

        Args:
            version_repo: Document version repository
            reference_repo: Document reference repository
            notification_repo: Document notification repository
            conflict_repo: Document conflict repository
            analytics_repo: Document analytics repository
        """
        # Create repositories if not provided
        self.version_repo = version_repo
        self.reference_repo = reference_repo
        self.notification_repo = notification_repo
        self.conflict_repo = conflict_repo
        self.analytics_repo = analytics_repo
        
        # Initialize repositories if not provided
        if not self.version_repo:
            with DatabaseConnectionFactory.session_context() as session:
                self.version_repo = DocumentVersionRepository(session)
        
        if not self.reference_repo:
            with DatabaseConnectionFactory.session_context() as session:
                self.reference_repo = DocumentReferenceRepository(session)
        
        if not self.notification_repo:
            with DatabaseConnectionFactory.session_context() as session:
                self.notification_repo = DocumentNotificationRepository(session)
        
        if not self.conflict_repo:
            with DatabaseConnectionFactory.session_context() as session:
                self.conflict_repo = DocumentConflictRepository(session)
        
        if not self.analytics_repo:
            with DatabaseConnectionFactory.session_context() as session:
                self.analytics_repo = DocumentAnalyticsRepository(session)

    # Version management methods

    def add_document_version(
        self,
        document_id: str,
        version: str,
        content: Dict[str, Any],
        changes: Optional[Dict[str, Any]] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[DocumentVersion]:
        """
        Add a new document version.

        Args:
            document_id: Document ID
            version: Version string
            content: Document content
            changes: Changes from previous version
            meta_data: Additional metadata

        Returns:
            DocumentVersion: Created document version or None if error
        """
        try:
            # Generate content hash
            content_hash = self._generate_content_hash(content)
            
            # Add version
            document_version = self.version_repo.add_version(
                document_id=document_id,
                version=version,
                content_hash=content_hash,
                changes=changes,
                meta_data=meta_data
            )
            
            if not document_version:
                logger.error(f"Failed to add version {version} for document {document_id}")
                return None
            
            # Check for affected documents
            affected_documents = self._get_affected_documents(document_id)
            
            if affected_documents:
                # Create notification
                notification_title = f"Document {document_id} updated to version {version}"
                notification_description = f"This update may affect {len(affected_documents)} related documents."
                
                self.notification_repo.add_notification(
                    document_id=document_id,
                    version_id=document_version.id,
                    title=notification_title,
                    description=notification_description,
                    severity="medium",
                    affected_documents=affected_documents
                )
            
            return document_version
        except Exception as e:
            logger.error(f"Error adding document version: {str(e)}")
            return None

    def get_document_version(
        self,
        document_id: str,
        version: Optional[str] = None
    ) -> Optional[DocumentVersion]:
        """
        Get a document version.

        Args:
            document_id: Document ID
            version: Version string (if None, get latest version)

        Returns:
            DocumentVersion: Document version or None if not found
        """
        return self.version_repo.get_version(document_id, version)

    def get_document_versions(
        self,
        document_id: str,
        limit: Optional[int] = None
    ) -> List[DocumentVersion]:
        """
        Get all versions of a document.

        Args:
            document_id: Document ID
            limit: Maximum number of versions to return

        Returns:
            List[DocumentVersion]: List of document versions
        """
        return self.version_repo.get_versions(document_id, limit)

    def verify_document_integrity(
        self,
        document_id: str,
        version: str,
        content: Dict[str, Any]
    ) -> bool:
        """
        Verify document integrity using content hash.

        Args:
            document_id: Document ID
            version: Version string
            content: Document content

        Returns:
            bool: True if document is valid, False otherwise
        """
        try:
            # Get version
            document_version = self.version_repo.get_version(document_id, version)
            
            if not document_version:
                logger.warning(f"Version {version} not found for document {document_id}")
                return False
            
            # Generate content hash
            content_hash = self._generate_content_hash(content)
            
            # Compare hashes
            return document_version.content_hash == content_hash
        except Exception as e:
            logger.error(f"Error verifying document integrity: {str(e)}")
            return False

    # Reference management methods

    def add_document_reference(
        self,
        source_document_id: str,
        target_document_id: str,
        reference_type: ReferenceType,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None,
        source_section_id: Optional[str] = None,
        target_section_id: Optional[str] = None,
        context: Optional[str] = None,
        relevance_score: float = 1.0,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[DocumentReference]:
        """
        Add a new document reference.

        Args:
            source_document_id: Source document ID
            target_document_id: Target document ID
            reference_type: Type of reference
            source_version: Source version string
            target_version: Target version string
            source_section_id: Source section ID
            target_section_id: Target section ID
            context: Context of the reference
            relevance_score: Relevance score
            meta_data: Additional metadata

        Returns:
            DocumentReference: Created document reference or None if error
        """
        try:
            # Get version IDs
            source_version_id = None
            target_version_id = None
            
            if source_version:
                source_version_obj = self.version_repo.get_version(source_document_id, source_version)
                if source_version_obj:
                    source_version_id = source_version_obj.id
            
            if target_version:
                target_version_obj = self.version_repo.get_version(target_document_id, target_version)
                if target_version_obj:
                    target_version_id = target_version_obj.id
            
            # Add reference
            return self.reference_repo.add_reference(
                source_document_id=source_document_id,
                target_document_id=target_document_id,
                reference_type=reference_type,
                source_version_id=source_version_id,
                target_version_id=target_version_id,
                source_section_id=source_section_id,
                target_section_id=target_section_id,
                context=context,
                relevance_score=relevance_score,
                meta_data=meta_data
            )
        except Exception as e:
            logger.error(f"Error adding document reference: {str(e)}")
            return None

    def get_document_references_from(
        self,
        document_id: str,
        version: Optional[str] = None,
        reference_type: Optional[ReferenceType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get references from a document.

        Args:
            document_id: Document ID
            version: Version string
            reference_type: Type of reference

        Returns:
            List[Dict[str, Any]]: List of document references with additional information
        """
        try:
            # Get version ID
            version_id = None
            if version:
                version_obj = self.version_repo.get_version(document_id, version)
                if version_obj:
                    version_id = version_obj.id
            
            # Get references
            references = self.reference_repo.get_references_from(
                document_id=document_id,
                version_id=version_id,
                reference_type=reference_type
            )
            
            # Format references
            formatted_references = []
            for ref in references:
                formatted_ref = {
                    "id": ref.id,
                    "source_document_id": ref.source_document_id,
                    "target_document_id": ref.target_document_id,
                    "reference_type": ref.reference_type.value,
                    "source_section_id": ref.source_section_id,
                    "target_section_id": ref.target_section_id,
                    "context": ref.context,
                    "relevance_score": ref.relevance_score,
                    "created_at": ref.created_at.isoformat() if ref.created_at else None,
                    "updated_at": ref.updated_at.isoformat() if ref.updated_at else None
                }
                
                # Add version information if available
                if ref.source_version:
                    formatted_ref["source_version"] = ref.source_version.version
                
                if ref.target_version:
                    formatted_ref["target_version"] = ref.target_version.version
                
                formatted_references.append(formatted_ref)
            
            return formatted_references
        except Exception as e:
            logger.error(f"Error getting document references: {str(e)}")
            return []

    def get_document_references_to(
        self,
        document_id: str,
        version: Optional[str] = None,
        reference_type: Optional[ReferenceType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get references to a document.

        Args:
            document_id: Document ID
            version: Version string
            reference_type: Type of reference

        Returns:
            List[Dict[str, Any]]: List of document references with additional information
        """
        try:
            # Get version ID
            version_id = None
            if version:
                version_obj = self.version_repo.get_version(document_id, version)
                if version_obj:
                    version_id = version_obj.id
            
            # Get references
            references = self.reference_repo.get_references_to(
                document_id=document_id,
                version_id=version_id,
                reference_type=reference_type
            )
            
            # Format references
            formatted_references = []
            for ref in references:
                formatted_ref = {
                    "id": ref.id,
                    "source_document_id": ref.source_document_id,
                    "target_document_id": ref.target_document_id,
                    "reference_type": ref.reference_type.value,
                    "source_section_id": ref.source_section_id,
                    "target_section_id": ref.target_section_id,
                    "context": ref.context,
                    "relevance_score": ref.relevance_score,
                    "created_at": ref.created_at.isoformat() if ref.created_at else None,
                    "updated_at": ref.updated_at.isoformat() if ref.updated_at else None
                }
                
                # Add version information if available
                if ref.source_version:
                    formatted_ref["source_version"] = ref.source_version.version
                
                if ref.target_version:
                    formatted_ref["target_version"] = ref.target_version.version
                
                formatted_references.append(formatted_ref)
            
            return formatted_references
        except Exception as e:
            logger.error(f"Error getting document references: {str(e)}")
            return []

    def update_document_references(
        self,
        document_id: str,
        old_version: str,
        new_version: str
    ) -> bool:
        """
        Update document references when a document is updated.

        Args:
            document_id: Document ID
            old_version: Old version string
            new_version: New version string

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get version IDs
            old_version_obj = self.version_repo.get_version(document_id, old_version)
            new_version_obj = self.version_repo.get_version(document_id, new_version)
            
            if not old_version_obj or not new_version_obj:
                logger.warning(f"Version not found for document {document_id}")
                return False
            
            # Get references from the document
            references_from = self.reference_repo.get_references_from(
                document_id=document_id,
                version_id=old_version_obj.id
            )
            
            # Get references to the document
            references_to = self.reference_repo.get_references_to(
                document_id=document_id,
                version_id=old_version_obj.id
            )
            
            # Update references from the document
            for ref in references_from:
                # Create new reference with new version
                self.reference_repo.add_reference(
                    source_document_id=ref.source_document_id,
                    target_document_id=ref.target_document_id,
                    reference_type=ref.reference_type,
                    source_version_id=new_version_obj.id,
                    target_version_id=ref.target_version_id,
                    source_section_id=ref.source_section_id,
                    target_section_id=ref.target_section_id,
                    context=ref.context,
                    relevance_score=ref.relevance_score,
                    meta_data=ref.meta_data
                )
            
            # Update references to the document
            for ref in references_to:
                # Create new reference with new version
                self.reference_repo.add_reference(
                    source_document_id=ref.source_document_id,
                    target_document_id=ref.target_document_id,
                    reference_type=ref.reference_type,
                    source_version_id=ref.source_version_id,
                    target_version_id=new_version_obj.id,
                    source_section_id=ref.source_section_id,
                    target_section_id=ref.target_section_id,
                    context=ref.context,
                    relevance_score=ref.relevance_score,
                    meta_data=ref.meta_data
                )
            
            return True
        except Exception as e:
            logger.error(f"Error updating document references: {str(e)}")
            return False

    # Notification methods

    def get_document_notifications(
        self,
        document_id: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get document update notifications.

        Args:
            document_id: Document ID
            is_read: Whether the notification is read
            limit: Maximum number of notifications to return

        Returns:
            List[Dict[str, Any]]: List of notifications
        """
        try:
            # Get notifications
            notifications = self.notification_repo.get_notifications(
                document_id=document_id,
                is_read=is_read,
                limit=limit
            )
            
            # Format notifications
            formatted_notifications = []
            for notification in notifications:
                formatted_notification = {
                    "id": notification.id,
                    "document_id": notification.document_id,
                    "notification_id": str(notification.notification_id),
                    "title": notification.title,
                    "description": notification.description,
                    "severity": notification.severity,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat() if notification.created_at else None,
                    "affected_documents": notification.affected_documents
                }
                
                # Add version information if available
                if notification.version:
                    formatted_notification["version"] = notification.version.version
                
                formatted_notifications.append(formatted_notification)
            
            return formatted_notifications
        except Exception as e:
            logger.error(f"Error getting document notifications: {str(e)}")
            return []

    def mark_notification_read(self, notification_id: int) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.notification_repo.mark_notification_read(notification_id)

    # Conflict management methods

    def add_document_conflict(
        self,
        document_id_1: str,
        document_id_2: str,
        conflict_type: str,
        description: str,
        severity: str,
        status: str = "open",
        resolution: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[DocumentConflict]:
        """
        Add a new document conflict.

        Args:
            document_id_1: First document ID
            document_id_2: Second document ID
            conflict_type: Type of conflict
            description: Conflict description
            severity: Conflict severity
            status: Conflict status
            resolution: Conflict resolution
            meta_data: Additional metadata

        Returns:
            DocumentConflict: Created conflict or None if error
        """
        return self.conflict_repo.add_conflict(
            document_id_1=document_id_1,
            document_id_2=document_id_2,
            conflict_type=conflict_type,
            description=description,
            severity=severity,
            status=status,
            resolution=resolution,
            meta_data=meta_data
        )

    def get_document_conflicts(
        self,
        document_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get document conflicts.

        Args:
            document_id: Document ID
            status: Conflict status
            severity: Conflict severity
            limit: Maximum number of conflicts to return

        Returns:
            List[Dict[str, Any]]: List of conflicts
        """
        try:
            # Get conflicts
            conflicts = self.conflict_repo.get_conflicts(
                document_id=document_id,
                status=status,
                severity=severity,
                limit=limit
            )
            
            # Format conflicts
            formatted_conflicts = []
            for conflict in conflicts:
                formatted_conflict = {
                    "id": conflict.id,
                    "document_id_1": conflict.document_id_1,
                    "document_id_2": conflict.document_id_2,
                    "conflict_type": conflict.conflict_type,
                    "description": conflict.description,
                    "severity": conflict.severity,
                    "status": conflict.status,
                    "resolution": conflict.resolution,
                    "created_at": conflict.created_at.isoformat() if conflict.created_at else None,
                    "updated_at": conflict.updated_at.isoformat() if conflict.updated_at else None
                }
                
                formatted_conflicts.append(formatted_conflict)
            
            return formatted_conflicts
        except Exception as e:
            logger.error(f"Error getting document conflicts: {str(e)}")
            return []

    def resolve_document_conflict(
        self,
        conflict_id: int,
        resolution: str,
        status: str = "resolved"
    ) -> bool:
        """
        Resolve a document conflict.

        Args:
            conflict_id: Conflict ID
            resolution: Conflict resolution
            status: Conflict status

        Returns:
            bool: True if successful, False otherwise
        """
        return self.conflict_repo.update_conflict(
            conflict_id=conflict_id,
            status=status,
            resolution=resolution
        )

    # Analytics methods

    def get_document_analytics(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analytics for a document.

        Args:
            document_id: Document ID

        Returns:
            Dict[str, Any]: Document analytics or None if not found
        """
        try:
            # Get analytics
            analytics = self.analytics_repo.get_analytics(document_id)
            
            if not analytics:
                return None
            
            # Format analytics
            formatted_analytics = {
                "document_id": analytics.document_id,
                "reference_count": analytics.reference_count,
                "view_count": analytics.view_count,
                "last_referenced_at": analytics.last_referenced_at.isoformat() if analytics.last_referenced_at else None,
                "last_viewed_at": analytics.last_viewed_at.isoformat() if analytics.last_viewed_at else None,
                "reference_distribution": analytics.reference_distribution
            }
            
            return formatted_analytics
        except Exception as e:
            logger.error(f"Error getting document analytics: {str(e)}")
            return None

    def record_document_view(self, document_id: str) -> bool:
        """
        Record a document view.

        Args:
            document_id: Document ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.analytics_repo.increment_view_count(document_id)

    def get_most_referenced_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most referenced documents.

        Args:
            limit: Maximum number of documents to return

        Returns:
            List[Dict[str, Any]]: List of document analytics
        """
        try:
            # Get analytics
            analytics_list = self.analytics_repo.get_most_referenced_documents(limit)
            
            # Format analytics
            formatted_analytics = []
            for analytics in analytics_list:
                formatted_analytics.append({
                    "document_id": analytics.document_id,
                    "reference_count": analytics.reference_count,
                    "view_count": analytics.view_count,
                    "last_referenced_at": analytics.last_referenced_at.isoformat() if analytics.last_referenced_at else None,
                    "last_viewed_at": analytics.last_viewed_at.isoformat() if analytics.last_viewed_at else None,
                    "reference_distribution": analytics.reference_distribution
                })
            
            return formatted_analytics
        except Exception as e:
            logger.error(f"Error getting most referenced documents: {str(e)}")
            return []

    def get_most_viewed_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most viewed documents.

        Args:
            limit: Maximum number of documents to return

        Returns:
            List[Dict[str, Any]]: List of document analytics
        """
        try:
            # Get analytics
            analytics_list = self.analytics_repo.get_most_viewed_documents(limit)
            
            # Format analytics
            formatted_analytics = []
            for analytics in analytics_list:
                formatted_analytics.append({
                    "document_id": analytics.document_id,
                    "reference_count": analytics.reference_count,
                    "view_count": analytics.view_count,
                    "last_referenced_at": analytics.last_referenced_at.isoformat() if analytics.last_referenced_at else None,
                    "last_viewed_at": analytics.last_viewed_at.isoformat() if analytics.last_viewed_at else None,
                    "reference_distribution": analytics.reference_distribution
                })
            
            return formatted_analytics
        except Exception as e:
            logger.error(f"Error getting most viewed documents: {str(e)}")
            return []

    # Helper methods

    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """
        Generate a hash of document content.

        Args:
            content: Document content

        Returns:
            str: Content hash
        """
        # Convert content to JSON string
        content_str = json.dumps(content, sort_keys=True)
        
        # Generate SHA-256 hash
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _get_affected_documents(self, document_id: str) -> List[str]:
        """
        Get documents that reference the given document.

        Args:
            document_id: Document ID

        Returns:
            List[str]: List of affected document IDs
        """
        # Get references to the document
        references = self.reference_repo.get_references_to(document_id)
        
        # Extract source document IDs
        affected_documents = [ref.source_document_id for ref in references]
        
        # Remove duplicates
        return list(set(affected_documents))


# Create a singleton instance for use throughout the application
document_relationship_service = DocumentRelationshipService()
