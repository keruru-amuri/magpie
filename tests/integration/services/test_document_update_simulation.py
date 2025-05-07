"""
Tests for document update simulation.

These tests simulate document updates and verify reference integrity,
notification delivery, and system behavior during document changes.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.models.document_relationship import ReferenceType
from app.services.document_relationship_service import DocumentRelationshipService
from app.services.document_notification_service import DocumentNotificationService


class TestDocumentUpdateSimulation:
    """
    Tests for document update simulation.
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
    def relationship_service(self, version_repo, reference_repo, notification_repo):
        """
        Create a document relationship service with mock repositories.
        """
        return DocumentRelationshipService(
            version_repo=version_repo,
            reference_repo=reference_repo,
            notification_repo=notification_repo
        )

    @pytest.fixture
    def notification_service(self, notification_repo):
        """
        Create a document notification service with a mock repository.
        """
        return DocumentNotificationService(
            notification_repo=notification_repo
        )

    def test_document_update_with_reference_integrity(
        self, relationship_service, version_repo, reference_repo
    ):
        """
        Test document update with reference integrity.

        This test simulates a document update and verifies that:
        1. New document version is created
        2. References are updated to point to the new version
        3. Reference integrity is maintained
        """
        # Mock document versions
        doc1_v1 = MagicMock()
        doc1_v1.id = 1
        doc1_v1.version = "1.0"

        doc2_v1 = MagicMock()
        doc2_v1.id = 2
        doc2_v1.version = "1.0"

        doc1_v2 = MagicMock()
        doc1_v2.id = 3
        doc1_v2.version = "2.0"

        # Configure version_repo
        version_repo.add_version.side_effect = [doc1_v1, doc2_v1, doc1_v2]
        version_repo.get_version.side_effect = [
            doc1_v1, doc2_v1,  # For initial reference
            doc1_v1, doc1_v2   # For update_document_references
        ]

        # Mock references
        ref_v1 = MagicMock()
        ref_v1.id = 1
        ref_v1.source_document_id = "doc-001"
        ref_v1.target_document_id = "doc-002"
        ref_v1.reference_type = ReferenceType.CITATION
        ref_v1.source_version_id = doc1_v1.id
        ref_v1.target_version_id = doc2_v1.id
        ref_v1.source_section_id = "section-001"
        ref_v1.target_section_id = "section-002"
        ref_v1.context = "Test context"
        ref_v1.relevance_score = 0.8
        ref_v1.meta_data = None

        ref_v2 = MagicMock()
        ref_v2.id = 2
        ref_v2.source_document_id = "doc-001"
        ref_v2.target_document_id = "doc-002"
        ref_v2.reference_type = ReferenceType.CITATION
        ref_v2.source_version_id = doc1_v2.id
        ref_v2.target_version_id = doc2_v1.id
        ref_v2.source_section_id = "section-001"
        ref_v2.target_section_id = "section-002"
        ref_v2.context = "Test context"
        ref_v2.relevance_score = 0.8
        ref_v2.meta_data = None

        # Configure reference_repo
        reference_repo.add_reference.side_effect = [ref_v1, ref_v2]
        reference_repo.get_references_from.return_value = [ref_v1]
        reference_repo.get_references_to.return_value = []

        # Mock _get_affected_documents to return empty list
        with patch.object(relationship_service, '_get_affected_documents', return_value=[]):
            # Step 1: Create initial document versions
            doc1_content_v1 = {"title": "Document 1", "content": "Initial content"}
            doc2_content = {"title": "Document 2", "content": "Referenced content"}

            doc1_v1_result = relationship_service.add_document_version(
                document_id="doc-001",
                version="1.0",
                content=doc1_content_v1
            )

            doc2_v1_result = relationship_service.add_document_version(
                document_id="doc-002",
                version="1.0",
                content=doc2_content
            )

            # Step 2: Create reference from doc1 to doc2
            ref_v1_result = relationship_service.add_document_reference(
                source_document_id="doc-001",
                target_document_id="doc-002",
                reference_type=ReferenceType.CITATION,
                source_version="1.0",
                target_version="1.0",
                source_section_id="section-001",
                target_section_id="section-002",
                context="Test context",
                relevance_score=0.8
            )

            # Step 3: Update doc1 to version 2.0
            doc1_content_v2 = {"title": "Document 1 (Updated)", "content": "Updated content"}

            doc1_v2_result = relationship_service.add_document_version(
                document_id="doc-001",
                version="2.0",
                content=doc1_content_v2,
                changes={"title": "Updated title", "content": "Updated content"}
            )

            # Step 4: Update references to point to new version
            update_result = relationship_service.update_document_references(
                document_id="doc-001",
                old_version="1.0",
                new_version="2.0"
            )

            # Verify results
            assert doc1_v1_result == doc1_v1
            assert doc2_v1_result == doc2_v1
            assert ref_v1_result == ref_v1
            assert doc1_v2_result == doc1_v2
            assert update_result is True

            # Verify repository calls
            version_repo.add_version.assert_any_call(
                document_id="doc-001",
                version="1.0",
                content_hash=relationship_service._generate_content_hash(doc1_content_v1),
                changes=None,
                meta_data=None
            )

            version_repo.add_version.assert_any_call(
                document_id="doc-001",
                version="2.0",
                content_hash=relationship_service._generate_content_hash(doc1_content_v2),
                changes={"title": "Updated title", "content": "Updated content"},
                meta_data=None
            )

            reference_repo.add_reference.assert_any_call(
                source_document_id="doc-001",
                target_document_id="doc-002",
                reference_type=ReferenceType.CITATION,
                source_version_id=doc1_v1.id,
                target_version_id=doc2_v1.id,
                source_section_id="section-001",
                target_section_id="section-002",
                context="Test context",
                relevance_score=0.8,
                meta_data=None
            )

            # Verify that a new reference was created with the new version
            reference_repo.add_reference.assert_any_call(
                source_document_id="doc-001",
                target_document_id="doc-002",
                reference_type=ReferenceType.CITATION,
                source_version_id=doc1_v2.id,
                target_version_id=doc2_v1.id,
                source_section_id="section-001",
                target_section_id="section-002",
                context="Test context",
                relevance_score=0.8,
                meta_data=None
            )

    def test_document_update_with_notification_delivery(
        self, notification_service
    ):
        """
        Test document update with notification delivery.

        This test simulates a document update and verifies that:
        1. Notifications are created for the updated document
        2. Notifications are delivered to affected documents
        3. Notification content is accurate
        """
        # Mock document versions
        doc1_v1 = MagicMock()
        doc1_v1.id = 1
        doc1_v1.version = "1.0"

        doc2_v1 = MagicMock()
        doc2_v1.id = 2
        doc2_v1.version = "1.0"

        doc3_v1 = MagicMock()
        doc3_v1.id = 3
        doc3_v1.version = "1.0"

        doc1_v2 = MagicMock()
        doc1_v2.id = 4
        doc1_v2.version = "2.0"

        # Mock notifications
        update_notification = {
            "id": 1,
            "document_id": "doc-001",
            "notification_id": "notif-001",
            "title": "Document doc-001 updated from version 1.0 to 2.0",
            "description": "This update may affect 1 related documents.",
            "severity": "medium",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "affected_documents": ["doc-003"]
        }

        affected_notification = {
            "id": 2,
            "document_id": "doc-003",
            "notification_id": "notif-002",
            "title": "Referenced document doc-001 updated to version 2.0",
            "description": "A document referenced by doc-003 has been updated.",
            "severity": "medium",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "affected_documents": ["doc-001"]
        }

        # Mock notification service methods
        notification_service.create_document_update_notification = MagicMock(return_value=update_notification)
        notification_service.notify_affected_documents = MagicMock(return_value=[affected_notification])

        # Test document update notification
        changes = {"title": "Updated title", "content": "Updated content"}

        # Step 1: Create update notification
        update_notification_result = notification_service.create_document_update_notification(
            document_id="doc-001",
            old_version="1.0",
            new_version="2.0",
            changes=changes
        )

        # Step 2: Notify affected documents
        affected_notification_result = notification_service.notify_affected_documents(
            document_id="doc-001",
            new_version="2.0",
            changes=changes
        )

        # Verify results
        assert update_notification_result is not None
        assert update_notification_result["id"] == 1
        assert update_notification_result["document_id"] == "doc-001"
        assert update_notification_result["title"] == "Document doc-001 updated from version 1.0 to 2.0"
        assert "affected_documents" in update_notification_result
        assert update_notification_result["affected_documents"] == ["doc-003"]

        assert len(affected_notification_result) == 1
        assert affected_notification_result[0]["id"] == 2
        assert affected_notification_result[0]["document_id"] == "doc-003"
        assert affected_notification_result[0]["title"] == "Referenced document doc-001 updated to version 2.0"

        # Verify notification service calls
        notification_service.create_document_update_notification.assert_called_once_with(
            document_id="doc-001",
            old_version="1.0",
            new_version="2.0",
            changes=changes
        )

        notification_service.notify_affected_documents.assert_called_once_with(
            document_id="doc-001",
            new_version="2.0",
            changes=changes
        )



    def test_document_update_with_multiple_versions(
        self, relationship_service, version_repo
    ):
        """
        Test document update with multiple versions.

        This test simulates multiple document updates and verifies that:
        1. Multiple versions can be created for a document
        2. References are properly maintained across versions
        3. Version history can be retrieved
        """
        # Mock document versions
        doc_versions = []
        for i in range(1, 4):
            version = MagicMock()
            version.id = i
            version.version = f"1.{i-1}"
            version.created_at = datetime.now(timezone.utc)
            version.is_active = True
            version.changes = {"version": f"1.{i-1}"}
            doc_versions.append(version)

        # Configure version_repo
        version_repo.add_version.side_effect = doc_versions
        version_repo.get_versions.return_value = doc_versions

        # Create multiple document versions
        doc_content_v1 = {"title": "Document 1", "content": "Initial content"}
        doc_content_v2 = {"title": "Document 1", "content": "Updated content"}
        doc_content_v3 = {"title": "Document 1", "content": "Final content"}

        # Add versions
        v1_result = relationship_service.add_document_version(
            document_id="doc-001",
            version="1.0",
            content=doc_content_v1
        )

        v2_result = relationship_service.add_document_version(
            document_id="doc-001",
            version="1.1",
            content=doc_content_v2,
            changes={"content": "Updated content"}
        )

        v3_result = relationship_service.add_document_version(
            document_id="doc-001",
            version="1.2",
            content=doc_content_v3,
            changes={"content": "Final content"}
        )

        # Get document versions
        versions_result = relationship_service.get_document_versions("doc-001")

        # Verify results
        assert v1_result == doc_versions[0]
        assert v2_result == doc_versions[1]
        assert v3_result == doc_versions[2]
        assert len(versions_result) == 3

        # Verify repository calls
        version_repo.add_version.assert_any_call(
            document_id="doc-001",
            version="1.0",
            content_hash=relationship_service._generate_content_hash(doc_content_v1),
            changes=None,
            meta_data=None
        )

        version_repo.add_version.assert_any_call(
            document_id="doc-001",
            version="1.1",
            content_hash=relationship_service._generate_content_hash(doc_content_v2),
            changes={"content": "Updated content"},
            meta_data=None
        )

        version_repo.add_version.assert_any_call(
            document_id="doc-001",
            version="1.2",
            content_hash=relationship_service._generate_content_hash(doc_content_v3),
            changes={"content": "Final content"},
            meta_data=None
        )

        version_repo.get_versions.assert_called_once_with("doc-001", None)

    def test_document_integrity_verification(self, relationship_service, version_repo):
        """
        Test document integrity verification.

        This test verifies that:
        1. Document integrity can be verified using content hash
        2. Tampered documents are detected
        """
        # Mock document version
        doc_version = MagicMock()
        doc_version.id = 1
        doc_version.version = "1.0"

        # Original content and hash
        doc_content = {"title": "Document 1", "content": "Original content"}
        content_hash = relationship_service._generate_content_hash(doc_content)

        # Set the content hash on the mock version
        doc_version.content_hash = content_hash

        # Configure version_repo
        version_repo.get_version.return_value = doc_version

        # Verify document with original content
        valid_result = relationship_service.verify_document_integrity(
            document_id="doc-001",
            version="1.0",
            content=doc_content
        )

        # Verify document with tampered content
        tampered_content = {"title": "Document 1", "content": "Tampered content"}
        invalid_result = relationship_service.verify_document_integrity(
            document_id="doc-001",
            version="1.0",
            content=tampered_content
        )

        # Verify results
        assert valid_result is True
        assert invalid_result is False

        # Verify repository calls
        version_repo.get_version.assert_any_call("doc-001", "1.0")
        assert version_repo.get_version.call_count == 2
