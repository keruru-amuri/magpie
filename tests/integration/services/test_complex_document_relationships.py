"""
Tests for complex document relationship networks.

These tests verify the system's ability to handle complex document relationship
networks, including circular references, multi-level dependencies, and
various reference types.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.models.document_relationship import ReferenceType
from app.services.document_relationship_service import DocumentRelationshipService


class TestComplexDocumentRelationships:
    """
    Tests for complex document relationship networks.
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
    def relationship_service(self, version_repo, reference_repo):
        """
        Create a document relationship service with mock repositories.
        """
        service = DocumentRelationshipService(
            version_repo=version_repo,
            reference_repo=reference_repo
        )

        # Mock the _get_affected_documents method to return empty list by default
        patch.object(service, '_get_affected_documents', return_value=[]).start()

        return service

    def test_circular_reference_handling(self, relationship_service, version_repo, reference_repo):
        """
        Test handling of circular references between documents.

        This test verifies that:
        1. Circular references can be created and retrieved
        2. The system can navigate circular references without infinite loops
        """
        # Mock document versions
        doc1_version = MagicMock()
        doc1_version.id = 1
        doc1_version.version = "1.0"

        doc2_version = MagicMock()
        doc2_version.id = 2
        doc2_version.version = "1.0"

        doc3_version = MagicMock()
        doc3_version.id = 3
        doc3_version.version = "1.0"

        # Configure version_repo
        version_repo.get_version.side_effect = [
            doc1_version, doc2_version,  # First reference
            doc2_version, doc3_version,  # Second reference
            doc3_version, doc1_version   # Third reference (creates circle)
        ]

        # Mock references
        ref1 = MagicMock()
        ref1.id = 1
        ref1.source_document_id = "doc-001"
        ref1.target_document_id = "doc-002"
        ref1.reference_type = ReferenceType.CITATION

        ref2 = MagicMock()
        ref2.id = 2
        ref2.source_document_id = "doc-002"
        ref2.target_document_id = "doc-003"
        ref2.reference_type = ReferenceType.RELATED

        ref3 = MagicMock()
        ref3.id = 3
        ref3.source_document_id = "doc-003"
        ref3.target_document_id = "doc-001"
        ref3.reference_type = ReferenceType.IMPLEMENTS

        # Configure reference_repo
        reference_repo.add_reference.side_effect = [ref1, ref2, ref3]

        # Create circular references
        ref1_result = relationship_service.add_document_reference(
            source_document_id="doc-001",
            target_document_id="doc-002",
            reference_type=ReferenceType.CITATION,
            source_version="1.0",
            target_version="1.0"
        )

        ref2_result = relationship_service.add_document_reference(
            source_document_id="doc-002",
            target_document_id="doc-003",
            reference_type=ReferenceType.RELATED,
            source_version="1.0",
            target_version="1.0"
        )

        ref3_result = relationship_service.add_document_reference(
            source_document_id="doc-003",
            target_document_id="doc-001",
            reference_type=ReferenceType.IMPLEMENTS,
            source_version="1.0",
            target_version="1.0"
        )

        # Mock references for retrieval
        reference_repo.get_references_from.side_effect = [
            [ref1],  # References from doc-001
            [ref2],  # References from doc-002
            [ref3]   # References from doc-003
        ]

        # Get references from each document
        refs_from_doc1 = relationship_service.get_document_references_from("doc-001")
        refs_from_doc2 = relationship_service.get_document_references_from("doc-002")
        refs_from_doc3 = relationship_service.get_document_references_from("doc-003")

        # Verify results
        assert ref1_result == ref1
        assert ref2_result == ref2
        assert ref3_result == ref3

        assert len(refs_from_doc1) == 1
        assert refs_from_doc1[0]["target_document_id"] == "doc-002"

        assert len(refs_from_doc2) == 1
        assert refs_from_doc2[0]["target_document_id"] == "doc-003"

        assert len(refs_from_doc3) == 1
        assert refs_from_doc3[0]["target_document_id"] == "doc-001"

        # Verify repository calls
        assert reference_repo.add_reference.call_count == 3
        assert reference_repo.get_references_from.call_count == 3

    def test_multi_level_dependency_chain(self, relationship_service, version_repo, reference_repo):
        """
        Test handling of multi-level dependency chains.

        This test verifies that:
        1. Multi-level dependency chains can be created and retrieved
        2. The system can navigate through dependency chains
        """
        # Create a chain of 5 documents with dependencies:
        # doc-001 -> doc-002 -> doc-003 -> doc-004 -> doc-005

        # Mock document versions
        versions = {}
        for i in range(1, 6):
            doc_id = f"doc-00{i}"
            version = MagicMock()
            version.id = i
            version.version = "1.0"
            versions[doc_id] = version

        # Configure version_repo
        version_repo.get_version.side_effect = lambda doc_id, _: versions.get(doc_id)

        # Mock references
        references = []
        for i in range(1, 5):
            source_id = f"doc-00{i}"
            target_id = f"doc-00{i+1}"

            ref = MagicMock()
            ref.id = i
            ref.source_document_id = source_id
            ref.target_document_id = target_id
            ref.reference_type = ReferenceType.CITATION
            ref.source_version_id = versions[source_id].id
            ref.target_version_id = versions[target_id].id

            references.append(ref)

        # Configure reference_repo
        reference_repo.add_reference.side_effect = references

        # Create dependency chain
        ref_results = []
        for i in range(1, 5):
            source_id = f"doc-00{i}"
            target_id = f"doc-00{i+1}"

            result = relationship_service.add_document_reference(
                source_document_id=source_id,
                target_document_id=target_id,
                reference_type=ReferenceType.CITATION,
                source_version="1.0",
                target_version="1.0"
            )

            ref_results.append(result)

        # Configure reference_repo for retrieval
        reference_repo.get_references_from.side_effect = [
            [references[0]],  # References from doc-001
            [references[1]],  # References from doc-002
            [references[2]],  # References from doc-003
            [references[3]]   # References from doc-004
        ]

        # Get references from each document
        refs_from_docs = []
        for i in range(1, 5):
            source_id = f"doc-00{i}"
            refs = relationship_service.get_document_references_from(source_id)
            refs_from_docs.append(refs)

        # Verify results
        for i in range(4):
            assert ref_results[i] == references[i]
            assert len(refs_from_docs[i]) == 1
            assert refs_from_docs[i][0]["source_document_id"] == f"doc-00{i+1}"
            assert refs_from_docs[i][0]["target_document_id"] == f"doc-00{i+2}"

        # Verify repository calls
        assert reference_repo.add_reference.call_count == 4
        assert reference_repo.get_references_from.call_count == 4

    def test_multiple_reference_types(self, relationship_service, version_repo, reference_repo):
        """
        Test handling of multiple reference types between documents.

        This test verifies that:
        1. Multiple reference types can be created between the same documents
        2. References can be filtered by type
        """
        # Mock document versions
        doc1_version = MagicMock()
        doc1_version.id = 1
        doc1_version.version = "1.0"

        doc2_version = MagicMock()
        doc2_version.id = 2
        doc2_version.version = "1.0"

        # Configure version_repo
        version_repo.get_version.return_value = doc1_version

        # Mock references with different types
        ref_citation = MagicMock()
        ref_citation.id = 1
        ref_citation.source_document_id = "doc-001"
        ref_citation.target_document_id = "doc-002"
        ref_citation.reference_type = ReferenceType.CITATION

        ref_supersedes = MagicMock()
        ref_supersedes.id = 2
        ref_supersedes.source_document_id = "doc-001"
        ref_supersedes.target_document_id = "doc-002"
        ref_supersedes.reference_type = ReferenceType.SUPERSEDES

        ref_supplements = MagicMock()
        ref_supplements.id = 3
        ref_supplements.source_document_id = "doc-001"
        ref_supplements.target_document_id = "doc-002"
        ref_supplements.reference_type = ReferenceType.SUPPLEMENTS

        # Configure reference_repo
        reference_repo.add_reference.side_effect = [ref_citation, ref_supersedes, ref_supplements]

        # Create references with different types
        ref_citation_result = relationship_service.add_document_reference(
            source_document_id="doc-001",
            target_document_id="doc-002",
            reference_type=ReferenceType.CITATION,
            source_version="1.0",
            target_version="1.0"
        )

        ref_supersedes_result = relationship_service.add_document_reference(
            source_document_id="doc-001",
            target_document_id="doc-002",
            reference_type=ReferenceType.SUPERSEDES,
            source_version="1.0",
            target_version="1.0"
        )

        ref_supplements_result = relationship_service.add_document_reference(
            source_document_id="doc-001",
            target_document_id="doc-002",
            reference_type=ReferenceType.SUPPLEMENTS,
            source_version="1.0",
            target_version="1.0"
        )

        # Configure reference_repo for retrieval
        reference_repo.get_references_from.side_effect = [
            [ref_citation, ref_supersedes, ref_supplements],  # All references
            [ref_citation],  # Citation references
            [ref_supersedes],  # Supersedes references
            [ref_supplements]  # Supplements references
        ]

        # Get all references
        all_refs = relationship_service.get_document_references_from("doc-001")

        # Get references filtered by type
        citation_refs = relationship_service.get_document_references_from(
            document_id="doc-001",
            reference_type=ReferenceType.CITATION
        )

        supersedes_refs = relationship_service.get_document_references_from(
            document_id="doc-001",
            reference_type=ReferenceType.SUPERSEDES
        )

        supplements_refs = relationship_service.get_document_references_from(
            document_id="doc-001",
            reference_type=ReferenceType.SUPPLEMENTS
        )

        # Verify results
        assert ref_citation_result == ref_citation
        assert ref_supersedes_result == ref_supersedes
        assert ref_supplements_result == ref_supplements

        assert len(all_refs) == 3
        assert len(citation_refs) == 1
        assert len(supersedes_refs) == 1
        assert len(supplements_refs) == 1

        assert citation_refs[0]["reference_type"] == ReferenceType.CITATION.value
        assert supersedes_refs[0]["reference_type"] == ReferenceType.SUPERSEDES.value
        assert supplements_refs[0]["reference_type"] == ReferenceType.SUPPLEMENTS.value

        # Verify repository calls
        assert reference_repo.add_reference.call_count == 3
        assert reference_repo.get_references_from.call_count == 4

    def test_complex_reference_network(self, relationship_service, version_repo, reference_repo):
        """
        Test handling of a complex reference network with multiple documents and reference types.

        This test verifies that:
        1. Complex reference networks can be created and navigated
        2. References can be retrieved in both directions
        """
        # Create a complex network with 5 documents and various reference types
        # doc-001 -> doc-002 (CITATION)
        # doc-001 -> doc-003 (RELATED)
        # doc-002 -> doc-004 (IMPLEMENTS)
        # doc-003 -> doc-005 (SUPPLEMENTS)
        # doc-004 -> doc-001 (RELATED)
        # doc-005 -> doc-002 (CITATION)

        # Mock document versions
        versions = {}
        for i in range(1, 6):
            doc_id = f"doc-00{i}"
            version = MagicMock()
            version.id = i
            version.version = "1.0"
            versions[doc_id] = version

        # Configure version_repo
        version_repo.get_version.side_effect = lambda doc_id, _: versions.get(doc_id)

        # Define reference structure
        reference_structure = [
            ("doc-001", "doc-002", ReferenceType.CITATION),
            ("doc-001", "doc-003", ReferenceType.RELATED),
            ("doc-002", "doc-004", ReferenceType.IMPLEMENTS),
            ("doc-003", "doc-005", ReferenceType.SUPPLEMENTS),
            ("doc-004", "doc-001", ReferenceType.RELATED),
            ("doc-005", "doc-002", ReferenceType.CITATION)
        ]

        # Mock references
        references = []
        for i, (source_id, target_id, ref_type) in enumerate(reference_structure, 1):
            ref = MagicMock()
            ref.id = i
            ref.source_document_id = source_id
            ref.target_document_id = target_id
            ref.reference_type = ref_type
            ref.source_version_id = versions[source_id].id
            ref.target_version_id = versions[target_id].id

            references.append(ref)

        # Configure reference_repo
        reference_repo.add_reference.side_effect = references

        # Create reference network
        ref_results = []
        for source_id, target_id, ref_type in reference_structure:
            result = relationship_service.add_document_reference(
                source_document_id=source_id,
                target_document_id=target_id,
                reference_type=ref_type,
                source_version="1.0",
                target_version="1.0"
            )

            ref_results.append(result)

        # Configure reference_repo for retrieval
        # References from each document
        reference_repo.get_references_from.side_effect = [
            [references[0], references[1]],  # From doc-001
            [references[2]],                 # From doc-002
            [references[3]],                 # From doc-003
            [references[4]],                 # From doc-004
            [references[5]]                  # From doc-005
        ]

        # References to each document
        reference_repo.get_references_to.side_effect = [
            [references[4]],                 # To doc-001
            [references[0], references[5]],  # To doc-002
            [references[1]],                 # To doc-003
            [references[2]],                 # To doc-004
            [references[3]]                  # To doc-005
        ]

        # Get references from each document
        refs_from_docs = []
        for i in range(1, 6):
            doc_id = f"doc-00{i}"
            refs = relationship_service.get_document_references_from(doc_id)
            refs_from_docs.append(refs)

        # Get references to each document
        refs_to_docs = []
        for i in range(1, 6):
            doc_id = f"doc-00{i}"
            refs = relationship_service.get_document_references_to(doc_id)
            refs_to_docs.append(refs)

        # Verify results
        # Check references from documents
        assert len(refs_from_docs[0]) == 2  # doc-001 references 2 documents
        assert len(refs_from_docs[1]) == 1  # doc-002 references 1 document
        assert len(refs_from_docs[2]) == 1  # doc-003 references 1 document
        assert len(refs_from_docs[3]) == 1  # doc-004 references 1 document
        assert len(refs_from_docs[4]) == 1  # doc-005 references 1 document

        # Check references to documents
        assert len(refs_to_docs[0]) == 1  # doc-001 is referenced by 1 document
        assert len(refs_to_docs[1]) == 2  # doc-002 is referenced by 2 documents
        assert len(refs_to_docs[2]) == 1  # doc-003 is referenced by 1 document
        assert len(refs_to_docs[3]) == 1  # doc-004 is referenced by 1 document
        assert len(refs_to_docs[4]) == 1  # doc-005 is referenced by 1 document

        # Verify specific references
        assert refs_from_docs[0][0]["target_document_id"] == "doc-002"
        assert refs_from_docs[0][1]["target_document_id"] == "doc-003"
        assert refs_from_docs[1][0]["target_document_id"] == "doc-004"
        assert refs_from_docs[3][0]["target_document_id"] == "doc-001"

        assert refs_to_docs[0][0]["source_document_id"] == "doc-004"
        assert refs_to_docs[1][0]["source_document_id"] == "doc-001"
        assert refs_to_docs[1][1]["source_document_id"] == "doc-005"

        # Verify repository calls
        assert reference_repo.add_reference.call_count == 6
        assert reference_repo.get_references_from.call_count == 5
        assert reference_repo.get_references_to.call_count == 5
