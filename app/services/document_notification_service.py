"""
Document notification service for the MAGPIE platform.

This module provides services for managing document update notifications.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from app.models.document_relationship import DocumentUpdateNotification
from app.repositories.document_relationship_repository import DocumentNotificationRepository
from app.services.document_relationship_service import document_relationship_service
from app.core.db.connection import DatabaseConnectionFactory

# Configure logging
logger = logging.getLogger(__name__)


class DocumentNotificationService:
    """
    Service for managing document update notifications.
    """

    def __init__(
        self,
        notification_repo: Optional[DocumentNotificationRepository] = None
    ):
        """
        Initialize document notification service.

        Args:
            notification_repo: Document notification repository
        """
        # Create repository if not provided
        self.notification_repo = notification_repo
        
        # Initialize repository if not provided
        if not self.notification_repo:
            with DatabaseConnectionFactory.session_context() as session:
                self.notification_repo = DocumentNotificationRepository(session)

    def create_update_notification(
        self,
        document_id: str,
        version_id: int,
        title: str,
        description: Optional[str] = None,
        severity: Optional[str] = None,
        affected_documents: Optional[List[str]] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a document update notification.

        Args:
            document_id: Document ID
            version_id: Version ID
            title: Notification title
            description: Notification description
            severity: Notification severity
            affected_documents: List of affected document IDs
            meta_data: Additional metadata

        Returns:
            Dict[str, Any]: Created notification or None if error
        """
        try:
            # Create notification
            notification = self.notification_repo.add_notification(
                document_id=document_id,
                version_id=version_id,
                title=title,
                description=description,
                severity=severity,
                affected_documents=affected_documents,
                meta_data=meta_data
            )
            
            if not notification:
                logger.error(f"Failed to create notification for document {document_id}")
                return None
            
            # Format notification
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
            
            return formatted_notification
        except Exception as e:
            logger.error(f"Error creating document notification: {str(e)}")
            return None

    def get_notifications(
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
        return document_relationship_service.get_document_notifications(
            document_id=document_id,
            is_read=is_read,
            limit=limit
        )

    def mark_notification_read(self, notification_id: int) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.notification_repo.mark_notification_read(notification_id)

    def create_document_update_notification(
        self,
        document_id: str,
        old_version: str,
        new_version: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a notification for a document update.

        Args:
            document_id: Document ID
            old_version: Old version string
            new_version: New version string
            changes: Changes from old version to new version

        Returns:
            Dict[str, Any]: Created notification or None if error
        """
        try:
            # Get new version
            version = document_relationship_service.get_document_version(document_id, new_version)
            
            if not version:
                logger.warning(f"Version {new_version} not found for document {document_id}")
                return None
            
            # Get affected documents
            affected_documents = document_relationship_service._get_affected_documents(document_id)
            
            # Create notification title
            title = f"Document {document_id} updated from version {old_version} to {new_version}"
            
            # Create notification description
            description = f"This update may affect {len(affected_documents)} related documents."
            
            if changes:
                # Add changes to description
                description += "\n\nChanges:"
                for key, value in changes.items():
                    description += f"\n- {key}: {value}"
            
            # Create notification
            return self.create_update_notification(
                document_id=document_id,
                version_id=version.id,
                title=title,
                description=description,
                severity="medium",
                affected_documents=affected_documents,
                meta_data={"changes": changes} if changes else None
            )
        except Exception as e:
            logger.error(f"Error creating document update notification: {str(e)}")
            return None

    def notify_affected_documents(
        self,
        document_id: str,
        new_version: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Notify affected documents about a document update.

        Args:
            document_id: Document ID
            new_version: New version string
            changes: Changes in the new version

        Returns:
            List[Dict[str, Any]]: List of created notifications
        """
        try:
            # Get affected documents
            affected_documents = document_relationship_service._get_affected_documents(document_id)
            
            if not affected_documents:
                logger.info(f"No affected documents for {document_id}")
                return []
            
            # Get new version
            version = document_relationship_service.get_document_version(document_id, new_version)
            
            if not version:
                logger.warning(f"Version {new_version} not found for document {document_id}")
                return []
            
            # Create notifications for affected documents
            notifications = []
            for affected_doc_id in affected_documents:
                # Create notification title
                title = f"Referenced document {document_id} updated to version {new_version}"
                
                # Create notification description
                description = f"A document referenced by {affected_doc_id} has been updated."
                
                if changes:
                    # Add changes to description
                    description += "\n\nChanges:"
                    for key, value in changes.items():
                        description += f"\n- {key}: {value}"
                
                # Create notification
                notification = self.create_update_notification(
                    document_id=affected_doc_id,
                    version_id=version.id,
                    title=title,
                    description=description,
                    severity="medium",
                    affected_documents=[document_id],
                    meta_data={"referenced_document": document_id, "changes": changes} if changes else {"referenced_document": document_id}
                )
                
                if notification:
                    notifications.append(notification)
            
            return notifications
        except Exception as e:
            logger.error(f"Error notifying affected documents: {str(e)}")
            return []


# Create a singleton instance for use throughout the application
document_notification_service = DocumentNotificationService()
