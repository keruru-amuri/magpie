"""
Document relationship repository for the MAGPIE platform.

This module provides repository classes for managing document relationships,
versions, and dependencies.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Set, Union

# Helper function for timezone-aware UTC timestamps
def utcnow():
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)

from sqlalchemy import select, and_, or_, desc, func, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.document_relationship import (
    DocumentVersion, DocumentReference, DocumentUpdateNotification,
    DocumentAnalytics, DocumentConflict, ReferenceType
)
from app.repositories.base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)


class DocumentVersionRepository(BaseRepository):
    """
    Repository for document versions.

    Note: This repository doesn't use a specific model class for the BaseRepository,
    but instead operates directly on the session.
    """

    def add_version(
        self,
        document_id: str,
        version: str,
        content_hash: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[DocumentVersion]:
        """
        Add a new document version.

        Args:
            document_id: Document ID
            version: Version string
            content_hash: Hash of document content
            changes: Changes from previous version
            meta_data: Additional metadata

        Returns:
            DocumentVersion: Created document version or None if error
        """
        try:
            # Check if version already exists
            stmt = select(DocumentVersion).where(
                and_(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.version == version
                )
            )
            existing_version = self.session.execute(stmt).scalar_one_or_none()

            if existing_version:
                logger.warning(f"Version {version} already exists for document {document_id}")
                return existing_version

            # Create new version
            document_version = DocumentVersion(
                document_id=document_id,
                version=version,
                content_hash=content_hash,
                changes=changes,
                meta_data=meta_data
            )

            self.session.add(document_version)
            self.session.commit()

            return document_version
        except SQLAlchemyError as e:
            logger.error(f"Error adding document version: {str(e)}")
            self.session.rollback()
            return None

    def get_version(
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
        try:
            if version:
                # Get specific version
                stmt = select(DocumentVersion).where(
                    and_(
                        DocumentVersion.document_id == document_id,
                        DocumentVersion.version == version
                    )
                )
            else:
                # Get latest version
                stmt = select(DocumentVersion).where(
                    DocumentVersion.document_id == document_id
                ).order_by(desc(DocumentVersion.created_at)).limit(1)

            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting document version: {str(e)}")
            return None

    def get_versions(
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
        try:
            stmt = select(DocumentVersion).where(
                DocumentVersion.document_id == document_id
            ).order_by(desc(DocumentVersion.created_at))

            if limit:
                stmt = stmt.limit(limit)

            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting document versions: {str(e)}")
            return []

    def update_version(
        self,
        document_id: str,
        version: str,
        is_active: Optional[bool] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a document version.

        Args:
            document_id: Document ID
            version: Version string
            is_active: Whether the version is active
            meta_data: Additional metadata

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get version
            stmt = select(DocumentVersion).where(
                and_(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.version == version
                )
            )
            document_version = self.session.execute(stmt).scalar_one_or_none()

            if not document_version:
                logger.warning(f"Version {version} not found for document {document_id}")
                return False

            # Update version
            if is_active is not None:
                document_version.is_active = is_active

            if meta_data:
                if document_version.meta_data:
                    document_version.meta_data.update(meta_data)
                else:
                    document_version.meta_data = meta_data

            self.session.commit()

            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating document version: {str(e)}")
            self.session.rollback()
            return False


class DocumentReferenceRepository(BaseRepository):
    """
    Repository for document references.
    """

    def add_reference(
        self,
        source_document_id: str,
        target_document_id: str,
        reference_type: ReferenceType,
        source_version_id: Optional[int] = None,
        target_version_id: Optional[int] = None,
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
            source_version_id: Source version ID
            target_version_id: Target version ID
            source_section_id: Source section ID
            target_section_id: Target section ID
            context: Context of the reference
            relevance_score: Relevance score
            meta_data: Additional metadata

        Returns:
            DocumentReference: Created document reference or None if error
        """
        try:
            # Check if reference already exists
            stmt = select(DocumentReference).where(
                and_(
                    DocumentReference.source_document_id == source_document_id,
                    DocumentReference.target_document_id == target_document_id,
                    DocumentReference.source_version_id == source_version_id,
                    DocumentReference.target_version_id == target_version_id,
                    DocumentReference.source_section_id == source_section_id,
                    DocumentReference.target_section_id == target_section_id
                )
            )
            existing_reference = self.session.execute(stmt).scalar_one_or_none()

            if existing_reference:
                logger.warning(f"Reference already exists from {source_document_id} to {target_document_id}")
                return existing_reference

            # Create new reference
            document_reference = DocumentReference(
                source_document_id=source_document_id,
                target_document_id=target_document_id,
                source_version_id=source_version_id,
                target_version_id=target_version_id,
                reference_type=reference_type,
                source_section_id=source_section_id,
                target_section_id=target_section_id,
                context=context,
                relevance_score=relevance_score,
                meta_data=meta_data
            )

            self.session.add(document_reference)
            self.session.commit()

            # Update analytics
            self._update_reference_analytics(target_document_id)

            return document_reference
        except SQLAlchemyError as e:
            logger.error(f"Error adding document reference: {str(e)}")
            self.session.rollback()
            return None

    def get_references_from(
        self,
        document_id: str,
        version_id: Optional[int] = None,
        reference_type: Optional[ReferenceType] = None
    ) -> List[DocumentReference]:
        """
        Get references from a document.

        Args:
            document_id: Document ID
            version_id: Version ID
            reference_type: Type of reference

        Returns:
            List[DocumentReference]: List of document references
        """
        try:
            # Build query
            conditions = [DocumentReference.source_document_id == document_id]

            if version_id:
                conditions.append(DocumentReference.source_version_id == version_id)

            if reference_type:
                conditions.append(DocumentReference.reference_type == reference_type)

            stmt = select(DocumentReference).where(and_(*conditions))

            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting document references: {str(e)}")
            return []

    def get_references_to(
        self,
        document_id: str,
        version_id: Optional[int] = None,
        reference_type: Optional[ReferenceType] = None
    ) -> List[DocumentReference]:
        """
        Get references to a document.

        Args:
            document_id: Document ID
            version_id: Version ID
            reference_type: Type of reference

        Returns:
            List[DocumentReference]: List of document references
        """
        try:
            # Build query
            conditions = [DocumentReference.target_document_id == document_id]

            if version_id:
                conditions.append(DocumentReference.target_version_id == version_id)

            if reference_type:
                conditions.append(DocumentReference.reference_type == reference_type)

            stmt = select(DocumentReference).where(and_(*conditions))

            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting document references: {str(e)}")
            return []

    def update_reference(
        self,
        reference_id: int,
        reference_type: Optional[ReferenceType] = None,
        relevance_score: Optional[float] = None,
        is_active: Optional[bool] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a document reference.

        Args:
            reference_id: Reference ID
            reference_type: Type of reference
            relevance_score: Relevance score
            is_active: Whether the reference is active
            meta_data: Additional metadata

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get reference
            stmt = select(DocumentReference).where(DocumentReference.id == reference_id)
            document_reference = self.session.execute(stmt).scalar_one_or_none()

            if not document_reference:
                logger.warning(f"Reference {reference_id} not found")
                return False

            # Update reference
            if reference_type:
                document_reference.reference_type = reference_type

            if relevance_score is not None:
                document_reference.relevance_score = relevance_score

            if is_active is not None:
                document_reference.is_active = is_active

            if meta_data:
                if document_reference.meta_data:
                    document_reference.meta_data.update(meta_data)
                else:
                    document_reference.meta_data = meta_data

            document_reference.updated_at = utcnow()

            self.session.commit()

            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating document reference: {str(e)}")
            self.session.rollback()
            return False

    def delete_reference(self, reference_id: int) -> bool:
        """
        Delete a document reference.

        Args:
            reference_id: Reference ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get reference
            stmt = select(DocumentReference).where(DocumentReference.id == reference_id)
            document_reference = self.session.execute(stmt).scalar_one_or_none()

            if not document_reference:
                logger.warning(f"Reference {reference_id} not found")
                return False

            # Delete reference
            self.session.delete(document_reference)
            self.session.commit()

            # Update analytics
            self._update_reference_analytics(document_reference.target_document_id)

            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting document reference: {str(e)}")
            self.session.rollback()
            return False

    def _update_reference_analytics(self, document_id: str) -> None:
        """
        Update reference analytics for a document.

        Args:
            document_id: Document ID
        """
        try:
            # Count references to document
            stmt = select(func.count()).where(DocumentReference.target_document_id == document_id)
            reference_count = self.session.execute(stmt).scalar_one()

            # Get reference distribution
            stmt = select(
                DocumentReference.reference_type,
                func.count()
            ).where(
                DocumentReference.target_document_id == document_id
            ).group_by(DocumentReference.reference_type)

            reference_distribution = {}
            for reference_type, count in self.session.execute(stmt).all():
                reference_distribution[reference_type.value] = count

            # Update or create analytics
            stmt = select(DocumentAnalytics).where(DocumentAnalytics.document_id == document_id)
            analytics = self.session.execute(stmt).scalar_one_or_none()

            if analytics:
                analytics.reference_count = reference_count
                analytics.reference_distribution = reference_distribution
                analytics.last_referenced_at = utcnow()
            else:
                analytics = DocumentAnalytics(
                    document_id=document_id,
                    reference_count=reference_count,
                    reference_distribution=reference_distribution,
                    last_referenced_at=utcnow()
                )
                self.session.add(analytics)

            self.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error updating reference analytics: {str(e)}")
            self.session.rollback()


class DocumentNotificationRepository(BaseRepository):
    """
    Repository for document update notifications.
    """

    def add_notification(
        self,
        document_id: str,
        version_id: int,
        title: str,
        description: Optional[str] = None,
        severity: Optional[str] = None,
        affected_documents: Optional[List[str]] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[DocumentUpdateNotification]:
        """
        Add a new document update notification.

        Args:
            document_id: Document ID
            version_id: Version ID
            title: Notification title
            description: Notification description
            severity: Notification severity
            affected_documents: List of affected document IDs
            meta_data: Additional metadata

        Returns:
            DocumentUpdateNotification: Created notification or None if error
        """
        try:
            # Create new notification
            notification = DocumentUpdateNotification(
                document_id=document_id,
                version_id=version_id,
                title=title,
                description=description,
                severity=severity,
                affected_documents=affected_documents,
                meta_data=meta_data
            )

            self.session.add(notification)
            self.session.commit()

            return notification
        except SQLAlchemyError as e:
            logger.error(f"Error adding document notification: {str(e)}")
            self.session.rollback()
            return None

    def get_notifications(
        self,
        document_id: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[DocumentUpdateNotification]:
        """
        Get document update notifications.

        Args:
            document_id: Document ID
            is_read: Whether the notification is read
            limit: Maximum number of notifications to return

        Returns:
            List[DocumentUpdateNotification]: List of notifications
        """
        try:
            # Build query
            conditions = []

            if document_id:
                conditions.append(DocumentUpdateNotification.document_id == document_id)

            if is_read is not None:
                conditions.append(DocumentUpdateNotification.is_read == is_read)

            stmt = select(DocumentUpdateNotification)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            stmt = stmt.order_by(desc(DocumentUpdateNotification.created_at))

            if limit:
                stmt = stmt.limit(limit)

            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
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
        try:
            # Get notification
            stmt = select(DocumentUpdateNotification).where(
                DocumentUpdateNotification.id == notification_id
            )
            notification = self.session.execute(stmt).scalar_one_or_none()

            if not notification:
                logger.warning(f"Notification {notification_id} not found")
                return False

            # Mark as read
            notification.is_read = True

            self.session.commit()

            return True
        except SQLAlchemyError as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            self.session.rollback()
            return False


class DocumentConflictRepository(BaseRepository):
    """
    Repository for document conflicts.
    """

    def add_conflict(
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
        try:
            # Check if conflict already exists
            stmt = select(DocumentConflict).where(
                and_(
                    DocumentConflict.document_id_1 == document_id_1,
                    DocumentConflict.document_id_2 == document_id_2,
                    DocumentConflict.conflict_type == conflict_type
                )
            )
            existing_conflict = self.session.execute(stmt).scalar_one_or_none()

            if existing_conflict:
                logger.warning(f"Conflict already exists between {document_id_1} and {document_id_2}")
                return existing_conflict

            # Create new conflict
            conflict = DocumentConflict(
                document_id_1=document_id_1,
                document_id_2=document_id_2,
                conflict_type=conflict_type,
                description=description,
                severity=severity,
                status=status,
                resolution=resolution,
                meta_data=meta_data
            )

            self.session.add(conflict)
            self.session.commit()

            return conflict
        except SQLAlchemyError as e:
            logger.error(f"Error adding document conflict: {str(e)}")
            self.session.rollback()
            return None

    def get_conflicts(
        self,
        document_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DocumentConflict]:
        """
        Get document conflicts.

        Args:
            document_id: Document ID
            status: Conflict status
            severity: Conflict severity
            limit: Maximum number of conflicts to return

        Returns:
            List[DocumentConflict]: List of conflicts
        """
        try:
            # Build query
            conditions = []

            if document_id:
                conditions.append(
                    or_(
                        DocumentConflict.document_id_1 == document_id,
                        DocumentConflict.document_id_2 == document_id
                    )
                )

            if status:
                conditions.append(DocumentConflict.status == status)

            if severity:
                conditions.append(DocumentConflict.severity == severity)

            stmt = select(DocumentConflict)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            stmt = stmt.order_by(desc(DocumentConflict.created_at))

            if limit:
                stmt = stmt.limit(limit)

            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting document conflicts: {str(e)}")
            return []

    def update_conflict(
        self,
        conflict_id: int,
        status: Optional[str] = None,
        resolution: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a document conflict.

        Args:
            conflict_id: Conflict ID
            status: Conflict status
            resolution: Conflict resolution
            meta_data: Additional metadata

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get conflict
            stmt = select(DocumentConflict).where(DocumentConflict.id == conflict_id)
            conflict = self.session.execute(stmt).scalar_one_or_none()

            if not conflict:
                logger.warning(f"Conflict {conflict_id} not found")
                return False

            # Update conflict
            if status:
                conflict.status = status

            if resolution:
                conflict.resolution = resolution

            if meta_data:
                if conflict.meta_data:
                    conflict.meta_data.update(meta_data)
                else:
                    conflict.meta_data = meta_data

            conflict.updated_at = utcnow()

            self.session.commit()

            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating document conflict: {str(e)}")
            self.session.rollback()
            return False


class DocumentAnalyticsRepository(BaseRepository):
    """
    Repository for document analytics.
    """

    def get_analytics(self, document_id: str) -> Optional[DocumentAnalytics]:
        """
        Get analytics for a document.

        Args:
            document_id: Document ID

        Returns:
            DocumentAnalytics: Document analytics or None if not found
        """
        try:
            stmt = select(DocumentAnalytics).where(DocumentAnalytics.document_id == document_id)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting document analytics: {str(e)}")
            return None

    def increment_view_count(self, document_id: str) -> bool:
        """
        Increment view count for a document.

        Args:
            document_id: Document ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get analytics
            stmt = select(DocumentAnalytics).where(DocumentAnalytics.document_id == document_id)
            analytics = self.session.execute(stmt).scalar_one_or_none()

            if analytics:
                # Update analytics
                analytics.view_count += 1
                analytics.last_viewed_at = utcnow()
            else:
                # Create new analytics
                analytics = DocumentAnalytics(
                    document_id=document_id,
                    view_count=1,
                    last_viewed_at=utcnow()
                )
                self.session.add(analytics)

            self.session.commit()

            return True
        except SQLAlchemyError as e:
            logger.error(f"Error incrementing view count: {str(e)}")
            self.session.rollback()
            return False

    def get_most_referenced_documents(self, limit: int = 10) -> List[DocumentAnalytics]:
        """
        Get most referenced documents.

        Args:
            limit: Maximum number of documents to return

        Returns:
            List[DocumentAnalytics]: List of document analytics
        """
        try:
            stmt = select(DocumentAnalytics).order_by(
                desc(DocumentAnalytics.reference_count)
            ).limit(limit)

            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting most referenced documents: {str(e)}")
            return []

    def get_most_viewed_documents(self, limit: int = 10) -> List[DocumentAnalytics]:
        """
        Get most viewed documents.

        Args:
            limit: Maximum number of documents to return

        Returns:
            List[DocumentAnalytics]: List of document analytics
        """
        try:
            stmt = select(DocumentAnalytics).order_by(
                desc(DocumentAnalytics.view_count)
            ).limit(limit)

            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting most viewed documents: {str(e)}")
            return []
