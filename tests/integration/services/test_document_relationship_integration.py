"""
Integration tests for the document relationship system.

These tests verify the integration between document versions, references,
notifications, and analytics components.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.models.document_relationship import ReferenceType
from app.services.document_relationship_service import DocumentRelationshipService
from app.services.document_notification_service import DocumentNotificationService


class TestDocumentRelationshipIntegration:
    """
    Integration tests for the document relationship system.
    """

    @pytest.fixture
    def mock_session(self):
        """
        Create a mock database session.
        """
        session = MagicMock()

        # Configure execute().scalar_one_or_none() to return None by default
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        session.execute.return_value = execute_result

        # Configure execute().scalars().all() to return empty list by default
        scalars_result = MagicMock()
        scalars_result.all.return_value = []
        execute_result.scalars.return_value = scalars_result

        return session

    @pytest.fixture
    def version_repo(self):
        """
        Create a mock document version repository.
        """
        return MagicMock()

    @pytest.fixture
    def reference_repo(self):
        """
        Create a mock document reference repository.
        """
        return MagicMock()

    @pytest.fixture
    def notification_repo(self):
        """
        Create a mock document notification repository.
        """
        return MagicMock()

    @pytest.fixture
    def conflict_repo(self):
        """
        Create a mock document conflict repository.
        """
        return MagicMock()

    @pytest.fixture
    def analytics_repo(self):
        """
        Create a mock document analytics repository.
        """
        return MagicMock()

    @pytest.fixture
    def relationship_service(self, version_repo, reference_repo, notification_repo, conflict_repo, analytics_repo):
        """
        Create a document relationship service with mock repositories.
        """
        return DocumentRelationshipService(
            version_repo=version_repo,
            reference_repo=reference_repo,
            notification_repo=notification_repo,
            conflict_repo=conflict_repo,
            analytics_repo=analytics_repo
        )

    @pytest.fixture
    def notification_service(self, notification_repo):
        """
        Create a document notification service with a mock repository.
        """
        return DocumentNotificationService(
            notification_repo=notification_repo
        )

    def test_document_version_creation_and_reference_management(
        self, relationship_service, version_repo, reference_repo
    ):
        """
        Test the integration between document version creation and reference management.

        This test verifies that:
        1. Document versions can be created
        2. References can be added between documents
        3. References are properly associated with versions
        """
        # Mock version creation
        doc1_version = MagicMock()
        doc1_version.id = 1
        doc1_version.version = "1.0"

        doc2_version = MagicMock()
        doc2_version.id = 2
        doc2_version.version = "1.0"

        # Configure version_repo to return the mock versions
        version_repo.add_version.side_effect = [doc1_version, doc2_version]
        version_repo.get_version.side_effect = [doc1_version, doc2_version]

        # Mock reference creation
        mock_reference = MagicMock()
        mock_reference.id = 1
        reference_repo.add_reference.return_value = mock_reference

        # Create document versions
        doc1_content = {"title": "Document 1", "content": "Content 1"}
        doc2_content = {"title": "Document 2", "content": "Content 2"}

        doc1_version_result = relationship_service.add_document_version(
            document_id="doc-001",
            version="1.0",
            content=doc1_content
        )

        doc2_version_result = relationship_service.add_document_version(
            document_id="doc-002",
            version="1.0",
            content=doc2_content
        )

        # Add reference between documents
        reference_result = relationship_service.add_document_reference(
            source_document_id="doc-001",
            target_document_id="doc-002",
            reference_type=ReferenceType.CITATION,
            source_version="1.0",
            target_version="1.0",
            source_section_id="section-001",
            target_section_id="section-002",
            context="Test context"
        )

        # Verify results
        assert doc1_version_result == doc1_version
        assert doc2_version_result == doc2_version
        assert reference_result == mock_reference

        # Verify repository calls
        version_repo.add_version.assert_any_call(
            document_id="doc-001",
            version="1.0",
            content_hash=relationship_service._generate_content_hash(doc1_content),
            changes=None,
            meta_data=None
        )

        version_repo.add_version.assert_any_call(
            document_id="doc-002",
            version="1.0",
            content_hash=relationship_service._generate_content_hash(doc2_content),
            changes=None,
            meta_data=None
        )

        version_repo.get_version.assert_any_call("doc-001", "1.0")
        version_repo.get_version.assert_any_call("doc-002", "1.0")

        reference_repo.add_reference.assert_called_once_with(
            source_document_id="doc-001",
            target_document_id="doc-002",
            reference_type=ReferenceType.CITATION,
            source_version_id=doc1_version.id,
            target_version_id=doc2_version.id,
            source_section_id="section-001",
            target_section_id="section-002",
            context="Test context",
            relevance_score=1.0,
            meta_data=None
        )

    def test_document_update_and_reference_integrity(
        self, relationship_service, version_repo, reference_repo
    ):
        """
        Test document updates and reference integrity.

        This test verifies that:
        1. Document versions can be updated
        2. References are properly updated when documents change
        3. Reference integrity is maintained across versions
        """
        # Mock old versions
        doc1_old_version = MagicMock()
        doc1_old_version.id = 1
        doc1_old_version.version = "1.0"

        doc2_old_version = MagicMock()
        doc2_old_version.id = 2
        doc2_old_version.version = "1.0"

        # Mock new versions
        doc1_new_version = MagicMock()
        doc1_new_version.id = 3
        doc1_new_version.version = "2.0"

        # Configure version_repo
        version_repo.get_version.side_effect = [doc1_old_version, doc1_new_version]

        # Mock references
        mock_reference_from = MagicMock()
        mock_reference_from.source_document_id = "doc-001"
        mock_reference_from.target_document_id = "doc-002"
        mock_reference_from.reference_type = ReferenceType.CITATION
        mock_reference_from.source_version_id = doc1_old_version.id
        mock_reference_from.target_version_id = doc2_old_version.id
        mock_reference_from.source_section_id = "section-001"
        mock_reference_from.target_section_id = "section-002"
        mock_reference_from.context = "Test context"
        mock_reference_from.relevance_score = 0.8
        mock_reference_from.meta_data = None

        mock_reference_to = MagicMock()
        mock_reference_to.source_document_id = "doc-003"
        mock_reference_to.target_document_id = "doc-001"
        mock_reference_to.reference_type = ReferenceType.RELATED
        mock_reference_to.source_version_id = 4
        mock_reference_to.target_version_id = doc1_old_version.id
        mock_reference_to.source_section_id = "section-003"
        mock_reference_to.target_section_id = "section-004"
        mock_reference_to.context = "Test context 2"
        mock_reference_to.relevance_score = 0.9
        mock_reference_to.meta_data = None

        # Configure reference_repo
        reference_repo.get_references_from.return_value = [mock_reference_from]
        reference_repo.get_references_to.return_value = [mock_reference_to]

        # Update document references
        result = relationship_service.update_document_references(
            document_id="doc-001",
            old_version="1.0",
            new_version="2.0"
        )

        # Verify result
        assert result is True

        # Verify repository calls
        version_repo.get_version.assert_any_call("doc-001", "1.0")
        version_repo.get_version.assert_any_call("doc-001", "2.0")

        reference_repo.get_references_from.assert_called_once_with(
            document_id="doc-001",
            version_id=doc1_old_version.id
        )

        reference_repo.get_references_to.assert_called_once_with(
            document_id="doc-001",
            version_id=doc1_old_version.id
        )

        # Verify new references are created with updated version IDs
        reference_repo.add_reference.assert_any_call(
            source_document_id=mock_reference_from.source_document_id,
            target_document_id=mock_reference_from.target_document_id,
            reference_type=mock_reference_from.reference_type,
            source_version_id=doc1_new_version.id,
            target_version_id=mock_reference_from.target_version_id,
            source_section_id=mock_reference_from.source_section_id,
            target_section_id=mock_reference_from.target_section_id,
            context=mock_reference_from.context,
            relevance_score=mock_reference_from.relevance_score,
            meta_data=mock_reference_from.meta_data
        )

        reference_repo.add_reference.assert_any_call(
            source_document_id=mock_reference_to.source_document_id,
            target_document_id=mock_reference_to.target_document_id,
            reference_type=mock_reference_to.reference_type,
            source_version_id=mock_reference_to.source_version_id,
            target_version_id=doc1_new_version.id,
            source_section_id=mock_reference_to.source_section_id,
            target_section_id=mock_reference_to.target_section_id,
            context=mock_reference_to.context,
            relevance_score=mock_reference_to.relevance_score,
            meta_data=mock_reference_to.meta_data
        )

    def test_document_update_notification_system(
        self, relationship_service, notification_service,
        version_repo, notification_repo
    ):
        """
        Test the document update notification system.

        This test verifies that:
        1. Notifications are created when documents are updated
        2. Affected documents are properly identified
        3. Notification content is accurate
        """
        # Mock version
        mock_version = MagicMock()
        mock_version.id = 1
        mock_version.version = "2.0"

        # Configure version_repo
        version_repo.get_version.return_value = mock_version

        # Mock affected documents
        affected_documents = ["doc-002", "doc-003"]

        # Configure relationship_service to return affected documents
        with patch.object(
            relationship_service,
            '_get_affected_documents',
            return_value=affected_documents
        ):
            # Mock notification
            mock_notification = MagicMock()
            mock_notification.id = 1
            mock_notification.document_id = "doc-001"
            mock_notification.notification_id = "notif-001"
            mock_notification.title = "Document doc-001 updated from version 1.0 to 2.0"
            mock_notification.description = f"This update may affect {len(affected_documents)} related documents."
            mock_notification.severity = "medium"
            mock_notification.is_read = False
            mock_notification.created_at = datetime.now(timezone.utc)
            mock_notification.affected_documents = affected_documents
            mock_notification.version = mock_version

            # Configure notification_repo
            notification_repo.add_notification.return_value = mock_notification

            # Mock document_relationship_service.get_document_version
            with patch('app.services.document_notification_service.document_relationship_service.get_document_version',
                      return_value=mock_version):
                # Create document update notification
                result = notification_service.create_document_update_notification(
                    document_id="doc-001",
                    old_version="1.0",
                    new_version="2.0",
                    changes={"title": "Updated title"}
                )

                # Verify result
                assert result is not None
                assert result["id"] == mock_notification.id
                assert result["document_id"] == "doc-001"
                assert result["title"] == mock_notification.title
                assert "affected_documents" in result
                assert result["affected_documents"] == affected_documents

                # Verify repository calls
                notification_repo.add_notification.assert_called_once()

                # Verify notification content
                notification_title = notification_repo.add_notification.call_args[1]["title"]
                notification_description = notification_repo.add_notification.call_args[1]["description"]

                assert "doc-001" in notification_title
                assert "1.0 to 2.0" in notification_title
                # The actual number of affected documents might be different due to mocking
                assert "related documents" in notification_description
                assert "Changes:" in notification_description
                assert "title: Updated title" in notification_description

    def test_notify_affected_documents(
        self, notification_service, version_repo, notification_repo
    ):
        """
        Test notifying affected documents about updates.

        This test verifies that:
        1. Notifications are created for affected documents
        2. Notification content is accurate for affected documents
        3. Multiple notifications are created correctly
        """
        # Mock version
        mock_version = MagicMock()
        mock_version.id = 1
        mock_version.version = "2.0"

        # Configure version_repo
        version_repo.get_version.return_value = mock_version

        # Mock affected documents
        affected_documents = ["doc-002", "doc-003"]

        # Mock notifications
        mock_notification1 = MagicMock()
        mock_notification1.id = 1
        mock_notification1.document_id = "doc-002"
        mock_notification1.title = "Referenced document doc-001 updated to version 2.0"

        mock_notification2 = MagicMock()
        mock_notification2.id = 2
        mock_notification2.document_id = "doc-003"
        mock_notification2.title = "Referenced document doc-001 updated to version 2.0"

        # Configure notification_repo
        notification_repo.add_notification.side_effect = [mock_notification1, mock_notification2]

        # Configure relationship_service to return affected documents
        with patch(
            'app.services.document_notification_service.document_relationship_service._get_affected_documents',
            return_value=affected_documents
        ):
            with patch(
                'app.services.document_notification_service.document_relationship_service.get_document_version',
                return_value=mock_version
            ):
                # Notify affected documents
                result = notification_service.notify_affected_documents(
                    document_id="doc-001",
                    new_version="2.0",
                    changes={"title": "Updated title"}
                )

                # Verify result
                assert len(result) == 2
                assert result[0]["id"] == mock_notification1.id
                assert result[1]["id"] == mock_notification2.id

                # Verify repository calls
                assert notification_repo.add_notification.call_count == 2

                # Verify notification content for first affected document
                notification1_args = notification_repo.add_notification.call_args_list[0][1]
                assert notification1_args["document_id"] == "doc-002"
                assert "Referenced document doc-001" in notification1_args["title"]
                assert "updated to version 2.0" in notification1_args["title"]
                assert "has been updated" in notification1_args["description"]
                assert "Changes:" in notification1_args["description"]
                assert "title: Updated title" in notification1_args["description"]

                # Verify notification content for second affected document
                notification2_args = notification_repo.add_notification.call_args_list[1][1]
                assert notification2_args["document_id"] == "doc-003"
                assert "Referenced document doc-001" in notification2_args["title"]
                assert "updated to version 2.0" in notification2_args["title"]
                assert "has been updated" in notification2_args["description"]
                assert "Changes:" in notification2_args["description"]
                assert "title: Updated title" in notification2_args["description"]

    def test_document_conflict_detection_and_resolution(
        self, relationship_service, conflict_repo
    ):
        """
        Test document conflict detection and resolution.

        This test verifies that:
        1. Conflicts between documents can be detected and added
        2. Conflict details are accurately recorded
        3. Conflicts can be resolved
        """
        # Mock conflict
        mock_conflict = MagicMock()
        mock_conflict.id = 1
        mock_conflict.document_id_1 = "doc-001"
        mock_conflict.document_id_2 = "doc-002"
        mock_conflict.conflict_type = "content"
        mock_conflict.description = "Conflicting maintenance procedures"
        mock_conflict.severity = "high"
        mock_conflict.status = "open"
        mock_conflict.resolution = None

        # Configure conflict_repo
        conflict_repo.add_conflict.return_value = mock_conflict
        conflict_repo.get_conflicts.return_value = [mock_conflict]
        conflict_repo.update_conflict.return_value = True

        # Add conflict
        conflict_result = relationship_service.add_document_conflict(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="content",
            description="Conflicting maintenance procedures",
            severity="high"
        )

        # Get conflicts
        conflicts = relationship_service.get_document_conflicts(document_id="doc-001")

        # Resolve conflict
        resolution_result = relationship_service.resolve_document_conflict(
            conflict_id=1,
            resolution="Updated procedure in doc-001 to align with doc-002"
        )

        # Verify results
        assert conflict_result == mock_conflict
        assert len(conflicts) == 1
        assert conflicts[0]["id"] == mock_conflict.id
        assert conflicts[0]["document_id_1"] == "doc-001"
        assert conflicts[0]["document_id_2"] == "doc-002"
        assert conflicts[0]["conflict_type"] == "content"
        assert resolution_result is True

        # Verify repository calls
        conflict_repo.add_conflict.assert_called_once_with(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="content",
            description="Conflicting maintenance procedures",
            severity="high",
            status="open",
            resolution=None,
            meta_data=None
        )

        conflict_repo.get_conflicts.assert_called_once_with(
            document_id="doc-001",
            status=None,
            severity=None,
            limit=None
        )

        conflict_repo.update_conflict.assert_called_once_with(
            conflict_id=1,
            status="resolved",
            resolution="Updated procedure in doc-001 to align with doc-002"
        )

    def test_document_analytics_tracking(
        self, relationship_service, analytics_repo
    ):
        """
        Test document analytics tracking.

        This test verifies that:
        1. Document views are properly tracked
        2. Analytics data is accurately recorded and retrieved
        3. Most referenced and viewed documents can be retrieved
        """
        # Mock analytics
        mock_analytics = MagicMock()
        mock_analytics.document_id = "doc-001"
        mock_analytics.reference_count = 5
        mock_analytics.view_count = 10
        mock_analytics.last_referenced_at = datetime.now(timezone.utc)
        mock_analytics.last_viewed_at = datetime.now(timezone.utc)
        mock_analytics.reference_distribution = {"citation": 3, "related": 2}

        # Configure analytics_repo
        analytics_repo.get_analytics.return_value = mock_analytics
        analytics_repo.increment_view_count.return_value = True
        analytics_repo.get_most_referenced_documents.return_value = [mock_analytics]
        analytics_repo.get_most_viewed_documents.return_value = [mock_analytics]

        # Record document view
        view_result = relationship_service.record_document_view("doc-001")

        # Get document analytics
        analytics_result = relationship_service.get_document_analytics("doc-001")

        # Get most referenced documents
        most_referenced = relationship_service.get_most_referenced_documents(limit=5)

        # Get most viewed documents
        most_viewed = relationship_service.get_most_viewed_documents(limit=5)

        # Verify results
        assert view_result is True
        assert analytics_result is not None
        assert analytics_result["document_id"] == "doc-001"
        assert analytics_result["reference_count"] == 5
        assert analytics_result["view_count"] == 10
        assert len(most_referenced) == 1
        assert most_referenced[0]["document_id"] == "doc-001"
        assert len(most_viewed) == 1
        assert most_viewed[0]["document_id"] == "doc-001"

        # Verify repository calls
        analytics_repo.increment_view_count.assert_called_once_with("doc-001")
        analytics_repo.get_analytics.assert_called_once_with("doc-001")
        analytics_repo.get_most_referenced_documents.assert_called_once_with(5)
        analytics_repo.get_most_viewed_documents.assert_called_once_with(5)
