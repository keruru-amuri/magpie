"""
Tests for document conflict detection and resolution.

These tests verify the system's ability to detect and resolve conflicts
between documents with contradictory information.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.models.document_relationship import ReferenceType
from app.services.document_relationship_service import DocumentRelationshipService


class TestConflictDetectionResolution:
    """
    Tests for document conflict detection and resolution.
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
    def conflict_repo(self):
        """
        Create a mock document conflict repository.
        """
        return MagicMock()

    @pytest.fixture
    def relationship_service(self, version_repo, reference_repo, conflict_repo):
        """
        Create a document relationship service with mock repositories.
        """
        return DocumentRelationshipService(
            version_repo=version_repo,
            reference_repo=reference_repo,
            conflict_repo=conflict_repo
        )

    def test_content_conflict_detection(self, relationship_service, conflict_repo):
        """
        Test detection of content conflicts between documents.

        This test verifies that:
        1. Content conflicts can be detected and added
        2. Conflict details are accurately recorded
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
        mock_conflict.created_at = datetime.now(timezone.utc)
        mock_conflict.updated_at = datetime.now(timezone.utc)

        # Configure conflict_repo
        conflict_repo.add_conflict.return_value = mock_conflict

        # Add content conflict
        result = relationship_service.add_document_conflict(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="content",
            description="Conflicting maintenance procedures",
            severity="high"
        )

        # Verify result
        assert result == mock_conflict

        # Verify repository call
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

    def test_procedure_conflict_detection(self, relationship_service, conflict_repo):
        """
        Test detection of procedure conflicts between documents.

        This test verifies that:
        1. Procedure conflicts can be detected and added
        2. Conflict details are accurately recorded
        """
        # Mock conflict
        mock_conflict = MagicMock()
        mock_conflict.id = 1
        mock_conflict.document_id_1 = "doc-001"
        mock_conflict.document_id_2 = "doc-002"
        mock_conflict.conflict_type = "procedure"
        mock_conflict.description = "Conflicting maintenance steps"
        mock_conflict.severity = "medium"
        mock_conflict.status = "open"
        mock_conflict.resolution = None
        mock_conflict.created_at = datetime.now(timezone.utc)
        mock_conflict.updated_at = datetime.now(timezone.utc)

        # Configure conflict_repo
        conflict_repo.add_conflict.return_value = mock_conflict

        # Add procedure conflict
        result = relationship_service.add_document_conflict(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="procedure",
            description="Conflicting maintenance steps",
            severity="medium"
        )

        # Verify result
        assert result == mock_conflict

        # Verify repository call
        conflict_repo.add_conflict.assert_called_once_with(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="procedure",
            description="Conflicting maintenance steps",
            severity="medium",
            status="open",
            resolution=None,
            meta_data=None
        )

    def test_requirement_conflict_detection(self, relationship_service, conflict_repo):
        """
        Test detection of requirement conflicts between documents.

        This test verifies that:
        1. Requirement conflicts can be detected and added
        2. Conflict details are accurately recorded
        """
        # Mock conflict
        mock_conflict = MagicMock()
        mock_conflict.id = 1
        mock_conflict.document_id_1 = "doc-001"
        mock_conflict.document_id_2 = "doc-002"
        mock_conflict.conflict_type = "requirement"
        mock_conflict.description = "Conflicting safety requirements"
        mock_conflict.severity = "high"
        mock_conflict.status = "open"
        mock_conflict.resolution = None
        mock_conflict.created_at = datetime.now(timezone.utc)
        mock_conflict.updated_at = datetime.now(timezone.utc)

        # Configure conflict_repo
        conflict_repo.add_conflict.return_value = mock_conflict

        # Add requirement conflict
        result = relationship_service.add_document_conflict(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="requirement",
            description="Conflicting safety requirements",
            severity="high"
        )

        # Verify result
        assert result == mock_conflict

        # Verify repository call
        conflict_repo.add_conflict.assert_called_once_with(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="requirement",
            description="Conflicting safety requirements",
            severity="high",
            status="open",
            resolution=None,
            meta_data=None
        )

    def test_conflict_resolution(self, relationship_service, conflict_repo):
        """
        Test resolution of conflicts between documents.

        This test verifies that:
        1. Conflicts can be resolved
        2. Resolution details are accurately recorded
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
        conflict_repo.get_conflicts.return_value = [mock_conflict]
        conflict_repo.update_conflict.return_value = True

        # Get open conflicts
        conflicts = relationship_service.get_document_conflicts(
            document_id="doc-001",
            status="open"
        )

        # Resolve conflict
        resolution_result = relationship_service.resolve_document_conflict(
            conflict_id=1,
            resolution="Updated procedure in doc-001 to align with doc-002",
            status="resolved"
        )

        # Verify results
        assert len(conflicts) == 1
        assert conflicts[0]["id"] == mock_conflict.id
        assert conflicts[0]["document_id_1"] == "doc-001"
        assert conflicts[0]["document_id_2"] == "doc-002"
        assert conflicts[0]["status"] == "open"
        assert resolution_result is True

        # Verify repository calls
        conflict_repo.get_conflicts.assert_called_once_with(
            document_id="doc-001",
            status="open",
            severity=None,
            limit=None
        )

        conflict_repo.update_conflict.assert_called_once_with(
            conflict_id=1,
            status="resolved",
            resolution="Updated procedure in doc-001 to align with doc-002"
        )

    def test_multiple_conflict_types(self, relationship_service, conflict_repo):
        """
        Test handling of multiple conflict types between the same documents.

        This test verifies that:
        1. Multiple conflict types can be detected between the same documents
        2. Each conflict type is tracked separately
        """
        # Mock conflicts
        content_conflict = MagicMock()
        content_conflict.id = 1
        content_conflict.document_id_1 = "doc-001"
        content_conflict.document_id_2 = "doc-002"
        content_conflict.conflict_type = "content"
        content_conflict.severity = "high"

        procedure_conflict = MagicMock()
        procedure_conflict.id = 2
        procedure_conflict.document_id_1 = "doc-001"
        procedure_conflict.document_id_2 = "doc-002"
        procedure_conflict.conflict_type = "procedure"
        procedure_conflict.severity = "medium"

        requirement_conflict = MagicMock()
        requirement_conflict.id = 3
        requirement_conflict.document_id_1 = "doc-001"
        requirement_conflict.document_id_2 = "doc-002"
        requirement_conflict.conflict_type = "requirement"
        requirement_conflict.severity = "high"

        # Configure conflict_repo
        conflict_repo.add_conflict.side_effect = [
            content_conflict, procedure_conflict, requirement_conflict
        ]
        conflict_repo.get_conflicts.return_value = [
            content_conflict, procedure_conflict, requirement_conflict
        ]

        # Add multiple conflict types
        content_result = relationship_service.add_document_conflict(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="content",
            description="Conflicting maintenance procedures",
            severity="high"
        )

        procedure_result = relationship_service.add_document_conflict(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="procedure",
            description="Conflicting maintenance steps",
            severity="medium"
        )

        requirement_result = relationship_service.add_document_conflict(
            document_id_1="doc-001",
            document_id_2="doc-002",
            conflict_type="requirement",
            description="Conflicting safety requirements",
            severity="high"
        )

        # Get all conflicts between the documents
        conflicts = relationship_service.get_document_conflicts(document_id="doc-001")

        # Verify results
        assert content_result == content_conflict
        assert procedure_result == procedure_conflict
        assert requirement_result == requirement_conflict
        assert len(conflicts) == 3

        # Verify conflict types
        conflict_types = [conflict["conflict_type"] for conflict in conflicts]
        assert "content" in conflict_types
        assert "procedure" in conflict_types
        assert "requirement" in conflict_types

        # Verify repository calls
        assert conflict_repo.add_conflict.call_count == 3
        conflict_repo.get_conflicts.assert_called_once_with(
            document_id="doc-001",
            status=None,
            severity=None,
            limit=None
        )

    def test_conflict_filtering_by_severity(self, relationship_service, conflict_repo):
        """
        Test filtering conflicts by severity.

        This test verifies that:
        1. Conflicts can be filtered by severity
        2. Only conflicts with the specified severity are returned
        """
        # Mock conflicts with different severities
        high_conflict = MagicMock()
        high_conflict.id = 1
        high_conflict.document_id_1 = "doc-001"
        high_conflict.document_id_2 = "doc-002"
        high_conflict.conflict_type = "content"
        high_conflict.severity = "high"

        medium_conflict = MagicMock()
        medium_conflict.id = 2
        medium_conflict.document_id_1 = "doc-001"
        medium_conflict.document_id_2 = "doc-003"
        medium_conflict.conflict_type = "procedure"
        medium_conflict.severity = "medium"

        low_conflict = MagicMock()
        low_conflict.id = 3
        low_conflict.document_id_1 = "doc-001"
        low_conflict.document_id_2 = "doc-004"
        low_conflict.conflict_type = "requirement"
        low_conflict.severity = "low"

        # Configure conflict_repo for different severity filters
        conflict_repo.get_conflicts.side_effect = [
            [high_conflict, medium_conflict, low_conflict],  # All conflicts
            [high_conflict],  # High severity
            [medium_conflict],  # Medium severity
            [low_conflict]  # Low severity
        ]

        # Get all conflicts
        all_conflicts = relationship_service.get_document_conflicts(document_id="doc-001")

        # Get conflicts filtered by severity
        high_conflicts = relationship_service.get_document_conflicts(
            document_id="doc-001",
            severity="high"
        )

        medium_conflicts = relationship_service.get_document_conflicts(
            document_id="doc-001",
            severity="medium"
        )

        low_conflicts = relationship_service.get_document_conflicts(
            document_id="doc-001",
            severity="low"
        )

        # Verify results
        assert len(all_conflicts) == 3
        assert len(high_conflicts) == 1
        assert len(medium_conflicts) == 1
        assert len(low_conflicts) == 1

        assert high_conflicts[0]["severity"] == "high"
        assert medium_conflicts[0]["severity"] == "medium"
        assert low_conflicts[0]["severity"] == "low"

        # Verify repository calls
        conflict_repo.get_conflicts.assert_any_call(
            document_id="doc-001",
            status=None,
            severity=None,
            limit=None
        )

        conflict_repo.get_conflicts.assert_any_call(
            document_id="doc-001",
            status=None,
            severity="high",
            limit=None
        )

        conflict_repo.get_conflicts.assert_any_call(
            document_id="doc-001",
            status=None,
            severity="medium",
            limit=None
        )

        conflict_repo.get_conflicts.assert_any_call(
            document_id="doc-001",
            status=None,
            severity="low",
            limit=None
        )
