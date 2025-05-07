"""
Unit tests for the document notification service.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.document_notification_service import DocumentNotificationService


class TestDocumentNotificationService:
    """
    Test suite for the DocumentNotificationService class.
    """

    @pytest.fixture
    def mock_notification_repo(self):
        """
        Create a mock notification repository.
        """
        return MagicMock()

    @pytest.fixture
    def service(self, mock_notification_repo):
        """
        Create a document notification service with mock repository.
        """
        return DocumentNotificationService(
            notification_repo=mock_notification_repo
        )

    def test_create_update_notification(self, service, mock_notification_repo):
        """
        Test creating an update notification.
        """
        # Setup
        document_id = "doc-001"
        version_id = 1
        title = "Test notification"
        description = "Test description"
        severity = "medium"
        affected_documents = ["doc-002", "doc-003"]
        meta_data = {"key": "value"}
        
        # Mock notification repository
        mock_notification = MagicMock()
        mock_notification.id = 1
        mock_notification.document_id = document_id
        mock_notification.notification_id = "notif-001"
        mock_notification.title = title
        mock_notification.description = description
        mock_notification.severity = severity
        mock_notification.is_read = False
        mock_notification.created_at = datetime.utcnow()
        mock_notification.affected_documents = affected_documents
        mock_notification.version = None
        
        mock_notification_repo.add_notification.return_value = mock_notification

        # Execute
        result = service.create_update_notification(
            document_id=document_id,
            version_id=version_id,
            title=title,
            description=description,
            severity=severity,
            affected_documents=affected_documents,
            meta_data=meta_data
        )

        # Verify
        assert result["id"] == mock_notification.id
        assert result["document_id"] == mock_notification.document_id
        assert result["notification_id"] == str(mock_notification.notification_id)
        assert result["title"] == mock_notification.title
        assert result["description"] == mock_notification.description
        assert result["severity"] == mock_notification.severity
        assert result["is_read"] == mock_notification.is_read
        assert result["affected_documents"] == mock_notification.affected_documents
        mock_notification_repo.add_notification.assert_called_once_with(
            document_id=document_id,
            version_id=version_id,
            title=title,
            description=description,
            severity=severity,
            affected_documents=affected_documents,
            meta_data=meta_data
        )

    def test_create_update_notification_failure(self, service, mock_notification_repo):
        """
        Test creating an update notification with failure.
        """
        # Setup
        document_id = "doc-001"
        version_id = 1
        title = "Test notification"
        
        # Mock notification repository
        mock_notification_repo.add_notification.return_value = None

        # Execute
        result = service.create_update_notification(
            document_id=document_id,
            version_id=version_id,
            title=title
        )

        # Verify
        assert result is None
        mock_notification_repo.add_notification.assert_called_once()

    @patch('app.services.document_notification_service.document_relationship_service')
    def test_get_notifications(self, mock_relationship_service, service):
        """
        Test getting notifications.
        """
        # Setup
        document_id = "doc-001"
        is_read = False
        limit = 5
        
        # Mock relationship service
        mock_notifications = [{"id": 1, "title": "Test notification"}]
        mock_relationship_service.get_document_notifications.return_value = mock_notifications

        # Execute
        result = service.get_notifications(document_id, is_read, limit)

        # Verify
        assert result == mock_notifications
        mock_relationship_service.get_document_notifications.assert_called_once_with(
            document_id=document_id,
            is_read=is_read,
            limit=limit
        )

    def test_mark_notification_read(self, service, mock_notification_repo):
        """
        Test marking a notification as read.
        """
        # Setup
        notification_id = 1
        mock_notification_repo.mark_notification_read.return_value = True

        # Execute
        result = service.mark_notification_read(notification_id)

        # Verify
        assert result is True
        mock_notification_repo.mark_notification_read.assert_called_once_with(notification_id)

    @patch('app.services.document_notification_service.document_relationship_service')
    def test_create_document_update_notification(self, mock_relationship_service, service):
        """
        Test creating a document update notification.
        """
        # Setup
        document_id = "doc-001"
        old_version = "1.0"
        new_version = "2.0"
        changes = {"title": "Updated title"}
        
        # Mock relationship service
        mock_version = MagicMock()
        mock_version.id = 1
        mock_relationship_service.get_document_version.return_value = mock_version
        
        mock_affected_documents = ["doc-002", "doc-003"]
        mock_relationship_service._get_affected_documents.return_value = mock_affected_documents
        
        # Mock create_update_notification
        mock_notification = {"id": 1, "title": "Test notification"}
        with patch.object(service, 'create_update_notification', return_value=mock_notification):
            # Execute
            result = service.create_document_update_notification(
                document_id=document_id,
                old_version=old_version,
                new_version=new_version,
                changes=changes
            )

            # Verify
            assert result == mock_notification
            mock_relationship_service.get_document_version.assert_called_once_with(document_id, new_version)
            mock_relationship_service._get_affected_documents.assert_called_once_with(document_id)
            service.create_update_notification.assert_called_once()

    @patch('app.services.document_notification_service.document_relationship_service')
    def test_create_document_update_notification_no_version(self, mock_relationship_service, service):
        """
        Test creating a document update notification with no version found.
        """
        # Setup
        document_id = "doc-001"
        old_version = "1.0"
        new_version = "2.0"
        
        # Mock relationship service
        mock_relationship_service.get_document_version.return_value = None

        # Execute
        result = service.create_document_update_notification(
            document_id=document_id,
            old_version=old_version,
            new_version=new_version
        )

        # Verify
        assert result is None
        mock_relationship_service.get_document_version.assert_called_once_with(document_id, new_version)
        mock_relationship_service._get_affected_documents.assert_not_called()

    @patch('app.services.document_notification_service.document_relationship_service')
    def test_notify_affected_documents(self, mock_relationship_service, service):
        """
        Test notifying affected documents.
        """
        # Setup
        document_id = "doc-001"
        new_version = "2.0"
        changes = {"title": "Updated title"}
        
        # Mock relationship service
        mock_affected_documents = ["doc-002", "doc-003"]
        mock_relationship_service._get_affected_documents.return_value = mock_affected_documents
        
        mock_version = MagicMock()
        mock_version.id = 1
        mock_relationship_service.get_document_version.return_value = mock_version
        
        # Mock create_update_notification
        mock_notification1 = {"id": 1, "title": "Test notification 1"}
        mock_notification2 = {"id": 2, "title": "Test notification 2"}
        
        with patch.object(service, 'create_update_notification', side_effect=[mock_notification1, mock_notification2]):
            # Execute
            result = service.notify_affected_documents(
                document_id=document_id,
                new_version=new_version,
                changes=changes
            )

            # Verify
            assert len(result) == 2
            assert result[0] == mock_notification1
            assert result[1] == mock_notification2
            mock_relationship_service._get_affected_documents.assert_called_once_with(document_id)
            mock_relationship_service.get_document_version.assert_called_once_with(document_id, new_version)
            assert service.create_update_notification.call_count == 2

    @patch('app.services.document_notification_service.document_relationship_service')
    def test_notify_affected_documents_no_affected(self, mock_relationship_service, service):
        """
        Test notifying affected documents with no affected documents.
        """
        # Setup
        document_id = "doc-001"
        new_version = "2.0"
        
        # Mock relationship service
        mock_relationship_service._get_affected_documents.return_value = []

        # Execute
        result = service.notify_affected_documents(
            document_id=document_id,
            new_version=new_version
        )

        # Verify
        assert result == []
        mock_relationship_service._get_affected_documents.assert_called_once_with(document_id)
        mock_relationship_service.get_document_version.assert_not_called()

    @patch('app.services.document_notification_service.document_relationship_service')
    def test_notify_affected_documents_no_version(self, mock_relationship_service, service):
        """
        Test notifying affected documents with no version found.
        """
        # Setup
        document_id = "doc-001"
        new_version = "2.0"
        
        # Mock relationship service
        mock_affected_documents = ["doc-002", "doc-003"]
        mock_relationship_service._get_affected_documents.return_value = mock_affected_documents
        
        mock_relationship_service.get_document_version.return_value = None

        # Execute
        result = service.notify_affected_documents(
            document_id=document_id,
            new_version=new_version
        )

        # Verify
        assert result == []
        mock_relationship_service._get_affected_documents.assert_called_once_with(document_id)
        mock_relationship_service.get_document_version.assert_called_once_with(document_id, new_version)
