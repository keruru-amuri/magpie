"""
Unit tests for the document relationship service.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.document_relationship_service import DocumentRelationshipService
from app.models.document_relationship import ReferenceType


class TestDocumentRelationshipService:
    """
    Test suite for the DocumentRelationshipService class.
    """

    @pytest.fixture
    def mock_version_repo(self):
        """
        Create a mock version repository.
        """
        return MagicMock()

    @pytest.fixture
    def mock_reference_repo(self):
        """
        Create a mock reference repository.
        """
        return MagicMock()

    @pytest.fixture
    def mock_notification_repo(self):
        """
        Create a mock notification repository.
        """
        return MagicMock()

    @pytest.fixture
    def mock_conflict_repo(self):
        """
        Create a mock conflict repository.
        """
        return MagicMock()

    @pytest.fixture
    def mock_analytics_repo(self):
        """
        Create a mock analytics repository.
        """
        return MagicMock()

    @pytest.fixture
    def service(self, mock_version_repo, mock_reference_repo, mock_notification_repo, mock_conflict_repo, mock_analytics_repo):
        """
        Create a document relationship service with mock repositories.
        """
        return DocumentRelationshipService(
            version_repo=mock_version_repo,
            reference_repo=mock_reference_repo,
            notification_repo=mock_notification_repo,
            conflict_repo=mock_conflict_repo,
            analytics_repo=mock_analytics_repo
        )

    def test_add_document_version(self, service, mock_version_repo, mock_notification_repo):
        """
        Test adding a document version.
        """
        # Setup
        document_id = "doc-001"
        version = "1.0"
        content = {"title": "Test Document", "content": "Test content"}
        changes = {"title": "Updated title"}
        meta_data = {"author": "Test Author"}

        # Mock version repository
        mock_version = MagicMock()
        mock_version.id = 1
        mock_version_repo.add_version.return_value = mock_version

        # Mock _get_affected_documents
        with patch.object(service, '_get_affected_documents', return_value=["doc-002"]):
            # Execute
            result = service.add_document_version(
                document_id=document_id,
                version=version,
                content=content,
                changes=changes,
                meta_data=meta_data
            )

            # Verify
            assert result == mock_version
            mock_version_repo.add_version.assert_called_once()
            mock_notification_repo.add_notification.assert_called_once()

    def test_add_document_version_no_affected_documents(self, service, mock_version_repo, mock_notification_repo):
        """
        Test adding a document version with no affected documents.
        """
        # Setup
        document_id = "doc-001"
        version = "1.0"
        content = {"title": "Test Document", "content": "Test content"}

        # Mock version repository
        mock_version = MagicMock()
        mock_version.id = 1
        mock_version_repo.add_version.return_value = mock_version

        # Mock _get_affected_documents
        with patch.object(service, '_get_affected_documents', return_value=[]):
            # Execute
            result = service.add_document_version(
                document_id=document_id,
                version=version,
                content=content
            )

            # Verify
            assert result == mock_version
            mock_version_repo.add_version.assert_called_once()
            mock_notification_repo.add_notification.assert_not_called()

    def test_get_document_version(self, service, mock_version_repo):
        """
        Test getting a document version.
        """
        # Setup
        document_id = "doc-001"
        version = "1.0"
        mock_version = MagicMock()
        mock_version_repo.get_version.return_value = mock_version

        # Execute
        result = service.get_document_version(document_id, version)

        # Verify
        assert result == mock_version
        mock_version_repo.get_version.assert_called_once_with(document_id, version)

    def test_get_document_versions(self, service, mock_version_repo):
        """
        Test getting document versions.
        """
        # Setup
        document_id = "doc-001"
        limit = 5
        mock_versions = [MagicMock(), MagicMock()]
        mock_version_repo.get_versions.return_value = mock_versions

        # Execute
        result = service.get_document_versions(document_id, limit)

        # Verify
        assert result == mock_versions
        mock_version_repo.get_versions.assert_called_once_with(document_id, limit)

    def test_verify_document_integrity_valid(self, service, mock_version_repo):
        """
        Test verifying document integrity with valid content.
        """
        # Setup
        document_id = "doc-001"
        version = "1.0"
        content = {"title": "Test Document", "content": "Test content"}
        
        # Mock version repository
        mock_version = MagicMock()
        mock_version.content_hash = service._generate_content_hash(content)
        mock_version_repo.get_version.return_value = mock_version

        # Execute
        result = service.verify_document_integrity(document_id, version, content)

        # Verify
        assert result is True
        mock_version_repo.get_version.assert_called_once_with(document_id, version)

    def test_verify_document_integrity_invalid(self, service, mock_version_repo):
        """
        Test verifying document integrity with invalid content.
        """
        # Setup
        document_id = "doc-001"
        version = "1.0"
        content = {"title": "Test Document", "content": "Test content"}
        
        # Mock version repository
        mock_version = MagicMock()
        mock_version.content_hash = "invalid_hash"
        mock_version_repo.get_version.return_value = mock_version

        # Execute
        result = service.verify_document_integrity(document_id, version, content)

        # Verify
        assert result is False
        mock_version_repo.get_version.assert_called_once_with(document_id, version)

    def test_add_document_reference(self, service, mock_version_repo, mock_reference_repo):
        """
        Test adding a document reference.
        """
        # Setup
        source_document_id = "doc-001"
        target_document_id = "doc-002"
        reference_type = ReferenceType.CITATION
        source_version = "1.0"
        target_version = "2.0"
        source_section_id = "section-001"
        target_section_id = "section-002"
        context = "Test context"
        relevance_score = 0.8
        
        # Mock version repository
        source_version_obj = MagicMock()
        source_version_obj.id = 1
        target_version_obj = MagicMock()
        target_version_obj.id = 2
        
        mock_version_repo.get_version.side_effect = [source_version_obj, target_version_obj]
        
        # Mock reference repository
        mock_reference = MagicMock()
        mock_reference_repo.add_reference.return_value = mock_reference

        # Execute
        result = service.add_document_reference(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            reference_type=reference_type,
            source_version=source_version,
            target_version=target_version,
            source_section_id=source_section_id,
            target_section_id=target_section_id,
            context=context,
            relevance_score=relevance_score
        )

        # Verify
        assert result == mock_reference
        mock_version_repo.get_version.assert_any_call(source_document_id, source_version)
        mock_version_repo.get_version.assert_any_call(target_document_id, target_version)
        mock_reference_repo.add_reference.assert_called_once_with(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            reference_type=reference_type,
            source_version_id=source_version_obj.id,
            target_version_id=target_version_obj.id,
            source_section_id=source_section_id,
            target_section_id=target_section_id,
            context=context,
            relevance_score=relevance_score,
            meta_data=None
        )

    def test_get_document_references_from(self, service, mock_reference_repo):
        """
        Test getting references from a document.
        """
        # Setup
        document_id = "doc-001"
        reference_type = ReferenceType.CITATION
        
        # Mock reference repository
        mock_reference = MagicMock()
        mock_reference.id = 1
        mock_reference.source_document_id = document_id
        mock_reference.target_document_id = "doc-002"
        mock_reference.reference_type = reference_type
        mock_reference.source_section_id = "section-001"
        mock_reference.target_section_id = "section-002"
        mock_reference.context = "Test context"
        mock_reference.relevance_score = 0.8
        mock_reference.created_at = datetime.utcnow()
        mock_reference.updated_at = datetime.utcnow()
        mock_reference.source_version = None
        mock_reference.target_version = None
        
        mock_reference_repo.get_references_from.return_value = [mock_reference]

        # Execute
        result = service.get_document_references_from(
            document_id=document_id,
            reference_type=reference_type
        )

        # Verify
        assert len(result) == 1
        assert result[0]["id"] == mock_reference.id
        assert result[0]["source_document_id"] == mock_reference.source_document_id
        assert result[0]["target_document_id"] == mock_reference.target_document_id
        assert result[0]["reference_type"] == mock_reference.reference_type.value
        mock_reference_repo.get_references_from.assert_called_once()

    def test_get_document_references_to(self, service, mock_reference_repo):
        """
        Test getting references to a document.
        """
        # Setup
        document_id = "doc-001"
        reference_type = ReferenceType.CITATION
        
        # Mock reference repository
        mock_reference = MagicMock()
        mock_reference.id = 1
        mock_reference.source_document_id = "doc-002"
        mock_reference.target_document_id = document_id
        mock_reference.reference_type = reference_type
        mock_reference.source_section_id = "section-001"
        mock_reference.target_section_id = "section-002"
        mock_reference.context = "Test context"
        mock_reference.relevance_score = 0.8
        mock_reference.created_at = datetime.utcnow()
        mock_reference.updated_at = datetime.utcnow()
        mock_reference.source_version = None
        mock_reference.target_version = None
        
        mock_reference_repo.get_references_to.return_value = [mock_reference]

        # Execute
        result = service.get_document_references_to(
            document_id=document_id,
            reference_type=reference_type
        )

        # Verify
        assert len(result) == 1
        assert result[0]["id"] == mock_reference.id
        assert result[0]["source_document_id"] == mock_reference.source_document_id
        assert result[0]["target_document_id"] == mock_reference.target_document_id
        assert result[0]["reference_type"] == mock_reference.reference_type.value
        mock_reference_repo.get_references_to.assert_called_once()

    def test_update_document_references(self, service, mock_version_repo, mock_reference_repo):
        """
        Test updating document references.
        """
        # Setup
        document_id = "doc-001"
        old_version = "1.0"
        new_version = "2.0"
        
        # Mock version repository
        old_version_obj = MagicMock()
        old_version_obj.id = 1
        new_version_obj = MagicMock()
        new_version_obj.id = 2
        
        mock_version_repo.get_version.side_effect = [old_version_obj, new_version_obj]
        
        # Mock reference repository
        mock_reference_from = MagicMock()
        mock_reference_from.source_document_id = document_id
        mock_reference_from.target_document_id = "doc-002"
        mock_reference_from.reference_type = ReferenceType.CITATION
        mock_reference_from.source_version_id = old_version_obj.id
        mock_reference_from.target_version_id = 3
        mock_reference_from.source_section_id = "section-001"
        mock_reference_from.target_section_id = "section-002"
        mock_reference_from.context = "Test context"
        mock_reference_from.relevance_score = 0.8
        mock_reference_from.meta_data = None
        
        mock_reference_to = MagicMock()
        mock_reference_to.source_document_id = "doc-003"
        mock_reference_to.target_document_id = document_id
        mock_reference_to.reference_type = ReferenceType.RELATED
        mock_reference_to.source_version_id = 4
        mock_reference_to.target_version_id = old_version_obj.id
        mock_reference_to.source_section_id = "section-003"
        mock_reference_to.target_section_id = "section-004"
        mock_reference_to.context = "Test context 2"
        mock_reference_to.relevance_score = 0.9
        mock_reference_to.meta_data = None
        
        mock_reference_repo.get_references_from.return_value = [mock_reference_from]
        mock_reference_repo.get_references_to.return_value = [mock_reference_to]

        # Execute
        result = service.update_document_references(document_id, old_version, new_version)

        # Verify
        assert result is True
        mock_version_repo.get_version.assert_any_call(document_id, old_version)
        mock_version_repo.get_version.assert_any_call(document_id, new_version)
        mock_reference_repo.get_references_from.assert_called_once_with(document_id=document_id, version_id=old_version_obj.id)
        mock_reference_repo.get_references_to.assert_called_once_with(document_id=document_id, version_id=old_version_obj.id)
        mock_reference_repo.add_reference.assert_any_call(
            source_document_id=mock_reference_from.source_document_id,
            target_document_id=mock_reference_from.target_document_id,
            reference_type=mock_reference_from.reference_type,
            source_version_id=new_version_obj.id,
            target_version_id=mock_reference_from.target_version_id,
            source_section_id=mock_reference_from.source_section_id,
            target_section_id=mock_reference_from.target_section_id,
            context=mock_reference_from.context,
            relevance_score=mock_reference_from.relevance_score,
            meta_data=mock_reference_from.meta_data
        )
        mock_reference_repo.add_reference.assert_any_call(
            source_document_id=mock_reference_to.source_document_id,
            target_document_id=mock_reference_to.target_document_id,
            reference_type=mock_reference_to.reference_type,
            source_version_id=mock_reference_to.source_version_id,
            target_version_id=new_version_obj.id,
            source_section_id=mock_reference_to.source_section_id,
            target_section_id=mock_reference_to.target_section_id,
            context=mock_reference_to.context,
            relevance_score=mock_reference_to.relevance_score,
            meta_data=mock_reference_to.meta_data
        )

    def test_get_document_notifications(self, service, mock_notification_repo):
        """
        Test getting document notifications.
        """
        # Setup
        document_id = "doc-001"
        is_read = False
        limit = 5
        
        # Mock notification repository
        mock_notification = MagicMock()
        mock_notification.id = 1
        mock_notification.document_id = document_id
        mock_notification.notification_id = "notif-001"
        mock_notification.title = "Test notification"
        mock_notification.description = "Test description"
        mock_notification.severity = "medium"
        mock_notification.is_read = is_read
        mock_notification.created_at = datetime.utcnow()
        mock_notification.affected_documents = ["doc-002"]
        mock_notification.version = None
        
        mock_notification_repo.get_notifications.return_value = [mock_notification]

        # Execute
        result = service.get_document_notifications(document_id, is_read, limit)

        # Verify
        assert len(result) == 1
        assert result[0]["id"] == mock_notification.id
        assert result[0]["document_id"] == mock_notification.document_id
        assert result[0]["notification_id"] == str(mock_notification.notification_id)
        assert result[0]["title"] == mock_notification.title
        mock_notification_repo.get_notifications.assert_called_once_with(document_id=document_id, is_read=is_read, limit=limit)

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

    def test_get_document_analytics(self, service, mock_analytics_repo):
        """
        Test getting document analytics.
        """
        # Setup
        document_id = "doc-001"
        
        # Mock analytics repository
        mock_analytics = MagicMock()
        mock_analytics.document_id = document_id
        mock_analytics.reference_count = 5
        mock_analytics.view_count = 10
        mock_analytics.last_referenced_at = datetime.utcnow()
        mock_analytics.last_viewed_at = datetime.utcnow()
        mock_analytics.reference_distribution = {"citation": 3, "related": 2}
        
        mock_analytics_repo.get_analytics.return_value = mock_analytics

        # Execute
        result = service.get_document_analytics(document_id)

        # Verify
        assert result["document_id"] == mock_analytics.document_id
        assert result["reference_count"] == mock_analytics.reference_count
        assert result["view_count"] == mock_analytics.view_count
        assert result["reference_distribution"] == mock_analytics.reference_distribution
        mock_analytics_repo.get_analytics.assert_called_once_with(document_id)

    def test_record_document_view(self, service, mock_analytics_repo):
        """
        Test recording a document view.
        """
        # Setup
        document_id = "doc-001"
        mock_analytics_repo.increment_view_count.return_value = True

        # Execute
        result = service.record_document_view(document_id)

        # Verify
        assert result is True
        mock_analytics_repo.increment_view_count.assert_called_once_with(document_id)

    def test_get_most_referenced_documents(self, service, mock_analytics_repo):
        """
        Test getting most referenced documents.
        """
        # Setup
        limit = 5
        
        # Mock analytics repository
        mock_analytics1 = MagicMock()
        mock_analytics1.document_id = "doc-001"
        mock_analytics1.reference_count = 10
        mock_analytics1.view_count = 20
        mock_analytics1.reference_distribution = {"citation": 5, "related": 5}
        
        mock_analytics2 = MagicMock()
        mock_analytics2.document_id = "doc-002"
        mock_analytics2.reference_count = 5
        mock_analytics2.view_count = 10
        mock_analytics2.reference_distribution = {"citation": 3, "related": 2}
        
        mock_analytics_repo.get_most_referenced_documents.return_value = [mock_analytics1, mock_analytics2]

        # Execute
        result = service.get_most_referenced_documents(limit)

        # Verify
        assert len(result) == 2
        assert result[0]["document_id"] == mock_analytics1.document_id
        assert result[0]["reference_count"] == mock_analytics1.reference_count
        assert result[1]["document_id"] == mock_analytics2.document_id
        assert result[1]["reference_count"] == mock_analytics2.reference_count
        mock_analytics_repo.get_most_referenced_documents.assert_called_once_with(limit)

    def test_get_most_viewed_documents(self, service, mock_analytics_repo):
        """
        Test getting most viewed documents.
        """
        # Setup
        limit = 5
        
        # Mock analytics repository
        mock_analytics1 = MagicMock()
        mock_analytics1.document_id = "doc-001"
        mock_analytics1.reference_count = 10
        mock_analytics1.view_count = 20
        mock_analytics1.reference_distribution = {"citation": 5, "related": 5}
        
        mock_analytics2 = MagicMock()
        mock_analytics2.document_id = "doc-002"
        mock_analytics2.reference_count = 5
        mock_analytics2.view_count = 10
        mock_analytics2.reference_distribution = {"citation": 3, "related": 2}
        
        mock_analytics_repo.get_most_viewed_documents.return_value = [mock_analytics1, mock_analytics2]

        # Execute
        result = service.get_most_viewed_documents(limit)

        # Verify
        assert len(result) == 2
        assert result[0]["document_id"] == mock_analytics1.document_id
        assert result[0]["view_count"] == mock_analytics1.view_count
        assert result[1]["document_id"] == mock_analytics2.document_id
        assert result[1]["view_count"] == mock_analytics2.view_count
        mock_analytics_repo.get_most_viewed_documents.assert_called_once_with(limit)
