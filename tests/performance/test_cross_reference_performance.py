"""
Performance tests for cross-reference navigation and retrieval.

These tests benchmark the performance of cross-reference navigation and retrieval
operations under various conditions and query patterns.
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.models.document_relationship import ReferenceType
from app.services.document_relationship_service import DocumentRelationshipService


class TestCrossReferencePerformance:
    """
    Performance tests for cross-reference navigation and retrieval.
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
        return DocumentRelationshipService(
            version_repo=version_repo,
            reference_repo=reference_repo
        )

    def test_reference_retrieval_performance(self, relationship_service, reference_repo):
        """
        Test the performance of reference retrieval operations.

        This test benchmarks:
        1. Retrieval of references from a document
        2. Retrieval of references to a document
        3. Performance with different numbers of references
        """
        # Create mock references
        def create_mock_references(count, direction="from"):
            """Create a list of mock references."""
            references = []
            for i in range(1, count + 1):
                ref = MagicMock()
                ref.id = i

                if direction == "from":
                    ref.source_document_id = "doc-001"
                    ref.target_document_id = f"doc-{i+1:03d}"
                else:
                    ref.source_document_id = f"doc-{i+1:03d}"
                    ref.target_document_id = "doc-001"

                ref.reference_type = ReferenceType.CITATION
                ref.source_section_id = f"section-{i:03d}"
                ref.target_section_id = f"section-{i:03d}"
                ref.context = f"Test context {i}"
                ref.relevance_score = 0.8
                ref.created_at = datetime.now(timezone.utc)
                ref.updated_at = datetime.now(timezone.utc)
                ref.source_version = None
                ref.target_version = None

                references.append(ref)

            return references

        # Test with different numbers of references
        reference_counts = [10, 100, 500]

        # Benchmark reference retrieval performance
        for count in reference_counts:
            # Mock references from document
            references_from = create_mock_references(count, direction="from")
            reference_repo.get_references_from.return_value = references_from

            # Benchmark retrieval of references from document
            start_time = time.time()
            result_from = relationship_service.get_document_references_from("doc-001")
            from_time = time.time() - start_time

            # Mock references to document
            references_to = create_mock_references(count, direction="to")
            reference_repo.get_references_to.return_value = references_to

            # Benchmark retrieval of references to document
            start_time = time.time()
            result_to = relationship_service.get_document_references_to("doc-001")
            to_time = time.time() - start_time

            # Verify results
            assert len(result_from) == count
            assert len(result_to) == count

            # Print performance metrics
            print(f"References: {count}")
            print(f"  From retrieval time: {from_time:.6f} seconds")
            print(f"  To retrieval time: {to_time:.6f} seconds")

            # Reset mock
            reference_repo.get_references_from.reset_mock()
            reference_repo.get_references_to.reset_mock()

    def test_reference_filtering_performance(self, relationship_service, reference_repo):
        """
        Test the performance of reference filtering operations.

        This test benchmarks:
        1. Filtering references by type
        2. Performance with different numbers of references
        """
        # Create mock references with different types
        def create_mixed_references(count):
            """Create a list of mock references with different types."""
            references = []
            reference_types = list(ReferenceType)

            for i in range(1, count + 1):
                ref = MagicMock()
                ref.id = i
                ref.source_document_id = "doc-001"
                ref.target_document_id = f"doc-{i+1:03d}"

                # Distribute reference types evenly
                ref.reference_type = reference_types[i % len(reference_types)]

                ref.source_section_id = f"section-{i:03d}"
                ref.target_section_id = f"section-{i:03d}"
                ref.context = f"Test context {i}"
                ref.relevance_score = 0.8
                ref.created_at = datetime.now(timezone.utc)
                ref.updated_at = datetime.now(timezone.utc)
                ref.source_version = None
                ref.target_version = None

                references.append(ref)

            return references

        # Test with different numbers of references
        reference_counts = [100, 500, 1000]

        # Benchmark reference filtering performance
        for count in reference_counts:
            # Mock mixed references
            mixed_references = create_mixed_references(count)

            # Filter references by type
            for ref_type in ReferenceType:
                # Mock filtered references
                filtered_references = [
                    ref for ref in mixed_references if ref.reference_type == ref_type
                ]
                reference_repo.get_references_from.return_value = filtered_references

                # Benchmark retrieval of filtered references
                start_time = time.time()
                result = relationship_service.get_document_references_from(
                    document_id="doc-001",
                    reference_type=ref_type
                )
                filter_time = time.time() - start_time

                # Verify results
                assert len(result) == len(filtered_references)

                # Print performance metrics
                print(f"References: {count}, Type: {ref_type.value}")
                print(f"  Filter time: {filter_time:.6f} seconds")
                print(f"  Filtered count: {len(filtered_references)}")

                # Reset mock
                reference_repo.get_references_from.reset_mock()

    def test_complex_network_navigation_performance(self, relationship_service, reference_repo):
        """
        Test the performance of navigating complex reference networks.

        This test benchmarks:
        1. Navigation through multi-level reference chains
        2. Performance with different network depths
        """
        # Create a chain of references
        def create_reference_chain(depth):
            """Create a chain of references with the specified depth."""
            references = []

            for i in range(1, depth):
                source_id = f"doc-{i:03d}"
                target_id = f"doc-{i+1:03d}"

                ref = MagicMock()
                ref.id = i
                ref.source_document_id = source_id
                ref.target_document_id = target_id
                ref.reference_type = ReferenceType.CITATION
                ref.source_section_id = f"section-{i:03d}"
                ref.target_section_id = f"section-{i+1:03d}"
                ref.context = f"Test context {i}"
                ref.relevance_score = 0.8
                ref.created_at = datetime.now(timezone.utc)
                ref.updated_at = datetime.now(timezone.utc)
                ref.source_version = None
                ref.target_version = None

                references.append(ref)

            return references

        # Test with different chain depths
        chain_depths = [5, 10, 20]

        # Benchmark chain navigation performance
        for depth in chain_depths:
            # Create reference chain
            chain = create_reference_chain(depth)

            # Configure reference_repo to return the next reference in the chain
            def get_references_from_side_effect(document_id, **kwargs):
                doc_num = int(document_id.split('-')[1])
                if doc_num < depth:
                    return [chain[doc_num - 1]]
                else:
                    return []

            reference_repo.get_references_from.side_effect = get_references_from_side_effect

            # Benchmark navigation through the chain
            start_time = time.time()

            # Navigate through the chain
            current_doc_id = "doc-001"
            chain_result = []

            while True:
                refs = relationship_service.get_document_references_from(current_doc_id)
                if not refs:
                    break

                chain_result.append(refs[0])
                current_doc_id = refs[0]["target_document_id"]

            chain_time = time.time() - start_time

            # Verify results
            assert len(chain_result) == depth - 1

            # Print performance metrics
            print(f"Chain depth: {depth}")
            print(f"  Navigation time: {chain_time:.6f} seconds")

            # Reset mock
            reference_repo.get_references_from.reset_mock()

    def test_reference_batch_retrieval_performance(self, relationship_service, reference_repo):
        """
        Test the performance of batch reference retrieval operations.

        This test benchmarks:
        1. Retrieval of references for multiple documents in a batch
        2. Performance with different batch sizes
        """
        # Create mock references for multiple documents
        def create_references_for_documents(doc_count, refs_per_doc):
            """Create references for multiple documents."""
            all_references = {}

            for doc_num in range(1, doc_count + 1):
                doc_id = f"doc-{doc_num:03d}"
                references = []

                for i in range(1, refs_per_doc + 1):
                    ref = MagicMock()
                    ref.id = (doc_num - 1) * refs_per_doc + i
                    ref.source_document_id = doc_id
                    ref.target_document_id = f"ref-{doc_num:03d}-{i:03d}"
                    ref.reference_type = ReferenceType.CITATION
                    ref.source_section_id = f"section-{i:03d}"
                    ref.target_section_id = f"section-{i:03d}"
                    ref.context = f"Test context {i}"
                    ref.relevance_score = 0.8
                    ref.created_at = datetime.now(timezone.utc)
                    ref.updated_at = datetime.now(timezone.utc)
                    ref.source_version = None
                    ref.target_version = None

                    references.append(ref)

                all_references[doc_id] = references

            return all_references

        # Test with different batch sizes
        batch_sizes = [5, 10, 20]
        refs_per_doc = 10

        # Benchmark batch retrieval performance
        for batch_size in batch_sizes:
            # Create references for batch
            all_references = create_references_for_documents(batch_size, refs_per_doc)

            # Configure reference_repo to return references for each document
            def get_references_from_side_effect(document_id, **kwargs):
                return all_references.get(document_id, [])

            reference_repo.get_references_from.side_effect = get_references_from_side_effect

            # Benchmark batch retrieval
            start_time = time.time()

            # Retrieve references for all documents in batch
            batch_results = {}
            for doc_num in range(1, batch_size + 1):
                doc_id = f"doc-{doc_num:03d}"
                batch_results[doc_id] = relationship_service.get_document_references_from(doc_id)

            batch_time = time.time() - start_time

            # Verify results
            assert len(batch_results) == batch_size
            for doc_num in range(1, batch_size + 1):
                doc_id = f"doc-{doc_num:03d}"
                assert len(batch_results[doc_id]) == refs_per_doc

            # Print performance metrics
            print(f"Batch size: {batch_size}, References per document: {refs_per_doc}")
            print(f"  Batch retrieval time: {batch_time:.6f} seconds")
            print(f"  Average time per document: {batch_time / batch_size:.6f} seconds")

            # Reset mock
            reference_repo.get_references_from.reset_mock()
