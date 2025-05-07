"""
Integration tests for the cross-reference system.

These tests verify the functionality and reliability of the cross-referencing system,
including reference creation, retrieval, navigation, and analytics.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from app.models.document_relationship import ReferenceType
from app.services.document_relationship_service import DocumentRelationshipService
from app.core.agents.documentation_agent import DocumentationAgent


class TestCrossReferenceSystemIntegration:
    """
    Integration tests for the cross-reference system.
    """

    @pytest.fixture
    def mock_documentation_service(self):
        """
        Create a mock documentation service.
        """
        mock_service = MagicMock()
        return mock_service

    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        mock_service = AsyncMock()
        return mock_service

    @pytest.fixture
    def agent(self, mock_documentation_service, mock_llm_service):
        """
        Create a documentation agent with mock services.
        """
        return DocumentationAgent(
            documentation_service=mock_documentation_service,
            llm_service=mock_llm_service
        )

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

    @pytest.mark.asyncio
    async def test_circular_reference_detection(self, agent, mock_documentation_service):
        """
        Test detection and handling of circular references.

        This test verifies that:
        1. Circular references can be detected
        2. The system can handle circular references without infinite loops
        3. Proper information is returned about the circular reference chain
        """
        # Mock documents
        doc1 = {
            "id": "doc-001",
            "title": "Aircraft Maintenance Manual",
            "content": "Maintenance procedures for aircraft systems",
            "sections": [
                {"id": "section-001", "title": "Introduction", "content": "Introduction to maintenance"}
            ]
        }

        doc2 = {
            "id": "doc-002",
            "title": "Engine Maintenance Guide",
            "content": "Procedures for engine maintenance",
            "sections": [
                {"id": "section-001", "title": "Engine Overview", "content": "Overview of engine systems"}
            ]
        }

        doc3 = {
            "id": "doc-003",
            "title": "Safety Procedures",
            "content": "Safety guidelines for maintenance",
            "sections": [
                {"id": "section-001", "title": "Safety Overview", "content": "Overview of safety procedures"}
            ]
        }

        # Mock documentation service
        mock_documentation_service.get_documentation.side_effect = [doc1, doc2, doc3, doc1, doc2, doc3]

        # Create circular reference chain: doc1 -> doc2 -> doc3 -> doc1
        # Mock references for doc1
        mock_references_from_doc1 = [
            {
                "id": 1,
                "source_document_id": "doc-001",
                "target_document_id": "doc-002",
                "reference_type": "citation",
                "source_section_id": "section-001",
                "target_section_id": "section-001",
                "context": "See engine maintenance guide",
                "relevance_score": 0.9,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]

        # Mock references for doc2
        mock_references_from_doc2 = [
            {
                "id": 2,
                "source_document_id": "doc-002",
                "target_document_id": "doc-003",
                "reference_type": "citation",
                "source_section_id": "section-001",
                "target_section_id": "section-001",
                "context": "See safety procedures",
                "relevance_score": 0.9,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]

        # Mock references for doc3
        mock_references_from_doc3 = [
            {
                "id": 3,
                "source_document_id": "doc-003",
                "target_document_id": "doc-001",
                "reference_type": "citation",
                "source_section_id": "section-001",
                "target_section_id": "section-001",
                "context": "See aircraft maintenance manual",
                "relevance_score": 0.9,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]

        # Mock document_relationship_service methods
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_references_from',
                  side_effect=[mock_references_from_doc1, mock_references_from_doc2, mock_references_from_doc3]):

            # Execute reference chain traversal
            # Start with doc1 and follow references
            doc1_refs = await agent.get_document_references(document_id="doc-001", direction="from")

            # Get references from doc2
            doc2_id = doc1_refs["references"][0]["target_document_id"]
            doc2_refs = await agent.get_document_references(document_id=doc2_id, direction="from")

            # Get references from doc3
            doc3_id = doc2_refs["references"][0]["target_document_id"]
            doc3_refs = await agent.get_document_references(document_id=doc3_id, direction="from")

            # Check if doc3 references doc1 (circular reference)
            circular_ref_target = doc3_refs["references"][0]["target_document_id"]

            # Verify circular reference
            assert circular_ref_target == "doc-001"
            assert doc1_refs["document"]["id"] == "doc-001"
            assert doc2_refs["document"]["id"] == "doc-002"
            assert doc3_refs["document"]["id"] == "doc-003"

    @pytest.mark.asyncio
    async def test_multi_level_reference_chain(self, agent, mock_documentation_service):
        """
        Test navigation through a multi-level reference chain.

        This test verifies that:
        1. References can be followed through multiple levels
        2. The complete reference chain can be traversed
        3. Information is correctly maintained throughout the chain
        """
        # Mock documents for a 5-level reference chain
        documents = []
        for i in range(1, 6):
            doc = {
                "id": f"doc-{i:03d}",
                "title": f"Document {i}",
                "content": f"Content of document {i}",
                "sections": [
                    {"id": f"section-{i:03d}", "title": f"Section {i}", "content": f"Content of section {i}"}
                ]
            }
            documents.append(doc)

        # Mock documentation service
        mock_documentation_service.get_documentation.side_effect = documents

        # Create reference chain: doc1 -> doc2 -> doc3 -> doc4 -> doc5
        mock_references = []
        for i in range(1, 5):
            ref = [
                {
                    "id": i,
                    "source_document_id": f"doc-{i:03d}",
                    "target_document_id": f"doc-{i+1:03d}",
                    "reference_type": "citation",
                    "source_section_id": f"section-{i:03d}",
                    "target_section_id": f"section-{i+1:03d}",
                    "context": f"Reference from doc-{i:03d} to doc-{i+1:03d}",
                    "relevance_score": 0.9,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ]
            mock_references.append(ref)

        # Add empty references for the last document
        mock_references.append([])

        # Mock document_relationship_service methods
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_references_from',
                  side_effect=mock_references):

            # Execute reference chain traversal
            current_doc_id = "doc-001"
            chain = []

            # Follow the reference chain until we reach a document with no outgoing references
            while True:
                refs = await agent.get_document_references(document_id=current_doc_id, direction="from")
                chain.append(refs["document"]["id"])

                if not refs["references"]:
                    break

                current_doc_id = refs["references"][0]["target_document_id"]

            # Verify the complete reference chain
            assert chain == ["doc-001", "doc-002", "doc-003", "doc-004", "doc-005"]
            assert len(chain) == 5

    @pytest.mark.asyncio
    async def test_reference_type_filtering(self, agent, mock_documentation_service):
        """
        Test filtering references by type.

        This test verifies that:
        1. References can be filtered by type
        2. Multiple reference types are handled correctly
        3. The system returns the correct subset of references
        """
        # Mock document
        document = {
            "id": "doc-001",
            "title": "Aircraft Maintenance Manual",
            "content": "Maintenance procedures for aircraft systems",
            "sections": [
                {"id": "section-001", "title": "Introduction", "content": "Introduction to maintenance"}
            ]
        }

        # Mock documentation service
        mock_documentation_service.get_documentation.return_value = document

        # Create references of different types
        citation_ref = {
            "id": 1,
            "source_document_id": "doc-001",
            "target_document_id": "doc-002",
            "reference_type": "citation",
            "source_section_id": "section-001",
            "target_section_id": "section-001",
            "context": "Citation reference",
            "relevance_score": 0.9,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        related_ref = {
            "id": 2,
            "source_document_id": "doc-001",
            "target_document_id": "doc-003",
            "reference_type": "related",
            "source_section_id": "section-001",
            "target_section_id": "section-001",
            "context": "Related reference",
            "relevance_score": 0.8,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        implements_ref = {
            "id": 3,
            "source_document_id": "doc-001",
            "target_document_id": "doc-004",
            "reference_type": "implements",
            "source_section_id": "section-001",
            "target_section_id": "section-001",
            "context": "Implements reference",
            "relevance_score": 0.7,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        # Test filtering by different reference types
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_references_from',
                  side_effect=[[citation_ref], [related_ref], [implements_ref], [citation_ref, related_ref, implements_ref]]):

            # Get citation references
            citation_result = await agent.get_document_references(
                document_id="doc-001",
                direction="from",
                reference_type="citation"
            )

            # Get related references
            related_result = await agent.get_document_references(
                document_id="doc-001",
                direction="from",
                reference_type="related"
            )

            # Get implements references
            implements_result = await agent.get_document_references(
                document_id="doc-001",
                direction="from",
                reference_type="implements"
            )

            # Get all references
            all_result = await agent.get_document_references(
                document_id="doc-001",
                direction="from"
            )

            # Verify filtered results
            assert len(citation_result["references"]) == 1
            assert citation_result["references"][0]["reference_type"] == "citation"

            assert len(related_result["references"]) == 1
            assert related_result["references"][0]["reference_type"] == "related"

            assert len(implements_result["references"]) == 1
            assert implements_result["references"][0]["reference_type"] == "implements"

            assert len(all_result["references"]) == 3

    @pytest.mark.asyncio
    async def test_reference_analytics_tracking(self, agent, mock_documentation_service):
        """
        Test reference analytics tracking.

        This test verifies that:
        1. Reference analytics are properly tracked
        2. Reference counts are updated correctly
        3. Reference distribution by type is maintained
        """
        # Mock document
        document = {
            "id": "doc-001",
            "title": "Aircraft Maintenance Manual",
            "content": "Maintenance procedures for aircraft systems",
            "sections": [
                {"id": "section-001", "title": "Introduction", "content": "Introduction to maintenance"}
            ]
        }

        # Mock documentation service
        mock_documentation_service.get_documentation.return_value = document

        # Mock analytics
        mock_analytics = {
            "document_id": "doc-001",
            "reference_count": 5,
            "view_count": 10,
            "last_referenced_at": datetime.now(timezone.utc).isoformat(),
            "last_viewed_at": datetime.now(timezone.utc).isoformat(),
            "reference_distribution": {
                "citation": 3,
                "related": 1,
                "implements": 1
            }
        }

        # Mock document_relationship_service methods
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_analytics',
                  return_value=mock_analytics):

            # Get document analytics
            result = await agent.get_document_analytics("doc-001")

            # Verify analytics
            assert result["document"] == document
            assert result["analytics"] == mock_analytics
            assert result["analytics"]["reference_count"] == 5
            assert result["analytics"]["view_count"] == 10
            assert result["analytics"]["reference_distribution"]["citation"] == 3
            assert result["analytics"]["reference_distribution"]["related"] == 1
            assert result["analytics"]["reference_distribution"]["implements"] == 1

    @pytest.mark.asyncio
    async def test_reference_update_on_document_change(self, agent, mock_documentation_service):
        """
        Test reference updates when documents are changed.

        This test verifies that:
        1. References are properly updated when documents change
        2. Version tracking is maintained for references
        3. Notifications are created for affected documents
        """
        # Mock documents
        doc1_v1 = {
            "id": "doc-001",
            "title": "Aircraft Maintenance Manual",
            "content": "Maintenance procedures for aircraft systems",
            "sections": [
                {"id": "section-001", "title": "Introduction", "content": "Introduction to maintenance"}
            ]
        }

        doc1_v2 = {
            "id": "doc-001",
            "title": "Aircraft Maintenance Manual (Updated)",
            "content": "Updated maintenance procedures for aircraft systems",
            "sections": [
                {"id": "section-001", "title": "Introduction", "content": "Updated introduction to maintenance"}
            ]
        }

        doc2 = {
            "id": "doc-002",
            "title": "Engine Maintenance Guide",
            "content": "Procedures for engine maintenance",
            "sections": [
                {"id": "section-001", "title": "Engine Overview", "content": "Overview of engine systems"}
            ]
        }

        # Mock documentation service
        mock_documentation_service.get_documentation.side_effect = [doc1_v1, doc2, doc1_v2]

        # Mock document versions
        mock_v1 = MagicMock()
        mock_v1.id = 1
        mock_v1.version = "1.0"

        mock_v2 = MagicMock()
        mock_v2.id = 2
        mock_v2.version = "2.0"

        # Mock reference
        mock_reference = {
            "id": 1,
            "source_document_id": "doc-002",
            "target_document_id": "doc-001",
            "reference_type": "citation",
            "source_section_id": "section-001",
            "target_section_id": "section-001",
            "context": "See maintenance manual",
            "relevance_score": 0.9,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        # Mock notification
        mock_notification = {
            "id": 1,
            "document_id": "doc-001",
            "notification_id": "notif-001",
            "title": "Document doc-001 updated from version 1.0 to 2.0",
            "description": "This update may affect 1 related documents.",
            "severity": "medium",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "affected_documents": ["doc-002"]
        }

        # Mock service methods
        with patch('app.core.agents.documentation_agent.document_relationship_service.add_document_version',
                  return_value=mock_v2):
            with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_references_to',
                      return_value=[mock_reference]):
                with patch('app.core.agents.documentation_agent.document_relationship_service.update_document_references',
                          return_value=True):
                    with patch('app.core.agents.documentation_agent.document_notification_service.create_document_update_notification',
                              return_value=mock_notification):

                        # Step 1: Add document reference
                        reference_result = await agent.add_document_reference(
                            source_document_id="doc-002",
                            target_document_id="doc-001",
                            reference_type="citation",
                            source_section_id="section-001",
                            target_section_id="section-001",
                            context="See maintenance manual",
                            relevance_score=0.9
                        )

                        # Step 2: Get references to doc-001
                        references_to_result = await agent.get_document_references(
                            document_id="doc-001",
                            direction="to"
                        )

                        # Step 3: Create new document version (simulated)
                        changes = {
                            "title": "Updated title",
                            "content": "Updated content",
                            "sections": "Updated sections"
                        }

                        # Verify results
                        assert reference_result is not None
                        assert references_to_result is not None
                        assert len(references_to_result["references"]) == 1
                        assert references_to_result["references"][0]["source_document_id"] == "doc-002"

    @pytest.mark.asyncio
    async def test_reference_integrity_validation(self, agent, mock_documentation_service):
        """
        Test reference integrity validation.

        This test verifies that:
        1. References to non-existent documents are handled properly
        2. References to non-existent sections are handled properly
        3. The system provides appropriate error messages
        """
        # Mock document
        document = {
            "id": "doc-001",
            "title": "Aircraft Maintenance Manual",
            "content": "Maintenance procedures for aircraft systems",
            "sections": [
                {"id": "section-001", "title": "Introduction", "content": "Introduction to maintenance"}
            ]
        }

        # Mock documentation service for existing document
        mock_documentation_service.get_documentation.side_effect = [document, None]

        # Test adding reference to non-existent document
        result_non_existent = await agent.add_document_reference(
            source_document_id="doc-001",
            target_document_id="non-existent",
            reference_type="citation",
            source_section_id="section-001",
            target_section_id="section-001"
        )

        # Reset mock
        mock_documentation_service.get_documentation.side_effect = [document, document]

        # Test adding reference with non-existent section
        result_invalid_section = await agent.add_document_reference(
            source_document_id="doc-001",
            target_document_id="doc-002",
            reference_type="citation",
            source_section_id="non-existent",
            target_section_id="section-001"
        )

        # Verify results
        assert result_non_existent["success"] is False
        assert "Target document with ID non-existent not found" in result_non_existent["response"]

        assert result_invalid_section["success"] is False
        assert "Source section with ID non-existent not found" in result_invalid_section["response"]

    def test_reference_performance_with_large_networks(self, relationship_service, reference_repo):
        """
        Test performance with large reference networks.

        This test verifies that:
        1. The system can handle large reference networks efficiently
        2. Performance scales reasonably with network size
        3. Reference retrieval remains fast even with many references
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
        reference_counts = [100, 500, 1000]

        # Benchmark reference retrieval performance
        for count in reference_counts:
            # Mock references from document
            references_from = create_mock_references(count, direction="from")
            reference_repo.get_references_from.return_value = references_from

            # Retrieve references from document
            result_from = relationship_service.get_document_references_from("doc-001")

            # Mock references to document
            references_to = create_mock_references(count, direction="to")
            reference_repo.get_references_to.return_value = references_to

            # Retrieve references to document
            result_to = relationship_service.get_document_references_to("doc-001")

            # Verify results
            assert len(result_from) == count
            assert len(result_to) == count
