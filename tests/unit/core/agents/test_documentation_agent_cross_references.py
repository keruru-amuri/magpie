"""
Unit tests for the documentation agent's cross-referencing functionality.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from app.core.agents.documentation_agent import DocumentationAgent
from app.models.document_relationship import ReferenceType


class TestDocumentationAgentCrossReferences:
    """
    Test suite for the DocumentationAgent class cross-referencing functionality.
    """

    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        mock_service = MagicMock()
        mock_service.generate_completion = AsyncMock()
        return mock_service

    @pytest.fixture
    def mock_documentation_service(self):
        """
        Create a mock documentation service.
        """
        mock_service = MagicMock()
        mock_service.get_documentation = MagicMock()
        mock_service.search_documentation = MagicMock()
        return mock_service

    @pytest.fixture
    def agent(self, mock_llm_service, mock_documentation_service):
        """
        Create a documentation agent with mock services.
        """
        return DocumentationAgent(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service
        )

    @pytest.mark.asyncio
    async def test_get_document_references_to(self, agent, mock_documentation_service):
        """
        Test getting references to a document.
        """
        # Setup
        document_id = "doc-001"
        mock_document = {
            "id": document_id,
            "title": "Test Document",
            "content": "Test content"
        }
        mock_documentation_service.get_documentation.return_value = mock_document
        
        # Mock document_relationship_service.get_document_references_to
        mock_references = [
            {
                "id": 1,
                "source_document_id": "doc-002",
                "target_document_id": document_id,
                "reference_type": "citation",
                "source_section_id": "section-001",
                "target_section_id": "section-002",
                "context": "Test context",
                "relevance_score": 0.8,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
        
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_references_to', return_value=mock_references):
            # Execute
            result = await agent.get_document_references(
                document_id=document_id,
                direction="to"
            )

            # Verify
            assert result["document"] == mock_document
            assert result["references"] == mock_references
            assert "The document 'Test Document' is referenced by the following documents" in result["response"]
            mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_references_from(self, agent, mock_documentation_service):
        """
        Test getting references from a document.
        """
        # Setup
        document_id = "doc-001"
        mock_document = {
            "id": document_id,
            "title": "Test Document",
            "content": "Test content"
        }
        mock_documentation_service.get_documentation.return_value = mock_document
        
        # Mock document_relationship_service.get_document_references_from
        mock_references = [
            {
                "id": 1,
                "source_document_id": document_id,
                "target_document_id": "doc-002",
                "reference_type": "citation",
                "source_section_id": "section-001",
                "target_section_id": "section-002",
                "context": "Test context",
                "relevance_score": 0.8,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
        
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_references_from', return_value=mock_references):
            # Execute
            result = await agent.get_document_references(
                document_id=document_id,
                direction="from"
            )

            # Verify
            assert result["document"] == mock_document
            assert result["references"] == mock_references
            assert "The document 'Test Document' references the following documents" in result["response"]
            mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_references_no_references(self, agent, mock_documentation_service):
        """
        Test getting references with no references found.
        """
        # Setup
        document_id = "doc-001"
        mock_document = {
            "id": document_id,
            "title": "Test Document",
            "content": "Test content"
        }
        mock_documentation_service.get_documentation.return_value = mock_document
        
        # Mock document_relationship_service.get_document_references_to
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_references_to', return_value=[]):
            # Execute
            result = await agent.get_document_references(
                document_id=document_id,
                direction="to"
            )

            # Verify
            assert result["document"] == mock_document
            assert result["references"] == []
            assert "The document 'Test Document' is not referenced by any other documents" in result["response"]
            mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_references_document_not_found(self, agent, mock_documentation_service):
        """
        Test getting references with document not found.
        """
        # Setup
        document_id = "doc-001"
        mock_documentation_service.get_documentation.return_value = None

        # Execute
        result = await agent.get_document_references(
            document_id=document_id,
            direction="to"
        )

        # Verify
        assert result["document"] is None
        assert result["references"] == []
        assert f"I couldn't find the document with ID {document_id}" in result["response"]
        mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_add_document_reference(self, agent, mock_documentation_service):
        """
        Test adding a document reference.
        """
        # Setup
        source_document_id = "doc-001"
        target_document_id = "doc-002"
        reference_type = "citation"
        source_section_id = "section-001"
        target_section_id = "section-002"
        context = "Test context"
        relevance_score = 0.8
        
        # Mock documentation service
        mock_source_document = {
            "id": source_document_id,
            "title": "Source Document",
            "content": "Source content",
            "sections": [{"id": source_section_id, "title": "Source Section", "content": "Source section content"}]
        }
        mock_target_document = {
            "id": target_document_id,
            "title": "Target Document",
            "content": "Target content",
            "sections": [{"id": target_section_id, "title": "Target Section", "content": "Target section content"}]
        }
        mock_documentation_service.get_documentation.side_effect = [mock_source_document, mock_target_document]
        
        # Mock document_relationship_service.add_document_reference
        mock_reference = {
            "id": 1,
            "source_document_id": source_document_id,
            "target_document_id": target_document_id,
            "reference_type": reference_type,
            "source_section_id": source_section_id,
            "target_section_id": target_section_id,
            "context": context,
            "relevance_score": relevance_score
        }
        
        with patch('app.core.agents.documentation_agent.document_relationship_service.add_document_reference', return_value=mock_reference):
            # Execute
            result = await agent.add_document_reference(
                source_document_id=source_document_id,
                target_document_id=target_document_id,
                reference_type=reference_type,
                source_section_id=source_section_id,
                target_section_id=target_section_id,
                context=context,
                relevance_score=relevance_score
            )

            # Verify
            assert result["success"] is True
            assert result["reference"] == mock_reference
            assert f"Successfully added reference from document {source_document_id} to document {target_document_id}" in result["response"]
            mock_documentation_service.get_documentation.assert_any_call(source_document_id)
            mock_documentation_service.get_documentation.assert_any_call(target_document_id)

    @pytest.mark.asyncio
    async def test_add_document_reference_source_not_found(self, agent, mock_documentation_service):
        """
        Test adding a document reference with source document not found.
        """
        # Setup
        source_document_id = "doc-001"
        target_document_id = "doc-002"
        reference_type = "citation"
        
        # Mock documentation service
        mock_documentation_service.get_documentation.return_value = None

        # Execute
        result = await agent.add_document_reference(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            reference_type=reference_type
        )

        # Verify
        assert result["success"] is False
        assert f"Source document with ID {source_document_id} not found" in result["response"]
        mock_documentation_service.get_documentation.assert_called_once_with(source_document_id)

    @pytest.mark.asyncio
    async def test_add_document_reference_target_not_found(self, agent, mock_documentation_service):
        """
        Test adding a document reference with target document not found.
        """
        # Setup
        source_document_id = "doc-001"
        target_document_id = "doc-002"
        reference_type = "citation"
        
        # Mock documentation service
        mock_source_document = {
            "id": source_document_id,
            "title": "Source Document",
            "content": "Source content"
        }
        mock_documentation_service.get_documentation.side_effect = [mock_source_document, None]

        # Execute
        result = await agent.add_document_reference(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            reference_type=reference_type
        )

        # Verify
        assert result["success"] is False
        assert f"Target document with ID {target_document_id} not found" in result["response"]
        mock_documentation_service.get_documentation.assert_any_call(source_document_id)
        mock_documentation_service.get_documentation.assert_any_call(target_document_id)

    @pytest.mark.asyncio
    async def test_add_document_reference_invalid_source_section(self, agent, mock_documentation_service):
        """
        Test adding a document reference with invalid source section.
        """
        # Setup
        source_document_id = "doc-001"
        target_document_id = "doc-002"
        reference_type = "citation"
        source_section_id = "invalid-section"
        
        # Mock documentation service
        mock_source_document = {
            "id": source_document_id,
            "title": "Source Document",
            "content": "Source content",
            "sections": [{"id": "section-001", "title": "Source Section", "content": "Source section content"}]
        }
        mock_target_document = {
            "id": target_document_id,
            "title": "Target Document",
            "content": "Target content"
        }
        mock_documentation_service.get_documentation.side_effect = [mock_source_document, mock_target_document]

        # Execute
        result = await agent.add_document_reference(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            reference_type=reference_type,
            source_section_id=source_section_id
        )

        # Verify
        assert result["success"] is False
        assert f"Source section with ID {source_section_id} not found in document {source_document_id}" in result["response"]
        mock_documentation_service.get_documentation.assert_any_call(source_document_id)
        mock_documentation_service.get_documentation.assert_any_call(target_document_id)

    @pytest.mark.asyncio
    async def test_add_document_reference_invalid_reference_type(self, agent, mock_documentation_service):
        """
        Test adding a document reference with invalid reference type.
        """
        # Setup
        source_document_id = "doc-001"
        target_document_id = "doc-002"
        reference_type = "invalid-type"
        
        # Mock documentation service
        mock_source_document = {
            "id": source_document_id,
            "title": "Source Document",
            "content": "Source content"
        }
        mock_target_document = {
            "id": target_document_id,
            "title": "Target Document",
            "content": "Target content"
        }
        mock_documentation_service.get_documentation.side_effect = [mock_source_document, mock_target_document]

        # Execute
        result = await agent.add_document_reference(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            reference_type=reference_type
        )

        # Verify
        assert result["success"] is False
        assert f"Invalid reference type: {reference_type}" in result["response"]
        mock_documentation_service.get_documentation.assert_any_call(source_document_id)
        mock_documentation_service.get_documentation.assert_any_call(target_document_id)

    @pytest.mark.asyncio
    async def test_get_document_versions(self, agent, mock_documentation_service):
        """
        Test getting document versions.
        """
        # Setup
        document_id = "doc-001"
        limit = 5
        
        # Mock documentation service
        mock_document = {
            "id": document_id,
            "title": "Test Document",
            "content": "Test content"
        }
        mock_documentation_service.get_documentation.return_value = mock_document
        
        # Mock document_relationship_service.get_document_versions
        mock_versions = [
            {
                "version": "2.0",
                "created_at": "2023-02-01T00:00:00",
                "changes": {"title": "Updated title"},
                "is_active": True
            },
            {
                "version": "1.0",
                "created_at": "2023-01-01T00:00:00",
                "changes": None,
                "is_active": False
            }
        ]
        
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_versions', return_value=mock_versions):
            # Execute
            result = await agent.get_document_versions(
                document_id=document_id,
                limit=limit
            )

            # Verify
            assert result["document"] == mock_document
            assert result["versions"] == mock_versions
            assert f"Version history for document 'Test Document'" in result["response"]
            mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_versions_no_versions(self, agent, mock_documentation_service):
        """
        Test getting document versions with no versions found.
        """
        # Setup
        document_id = "doc-001"
        
        # Mock documentation service
        mock_document = {
            "id": document_id,
            "title": "Test Document",
            "content": "Test content"
        }
        mock_documentation_service.get_documentation.return_value = mock_document
        
        # Mock document_relationship_service.get_document_versions
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_versions', return_value=[]):
            # Execute
            result = await agent.get_document_versions(
                document_id=document_id
            )

            # Verify
            assert result["document"] == mock_document
            assert result["versions"] == []
            assert f"No version history found for document 'Test Document'" in result["response"]
            mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_versions_document_not_found(self, agent, mock_documentation_service):
        """
        Test getting document versions with document not found.
        """
        # Setup
        document_id = "doc-001"
        mock_documentation_service.get_documentation.return_value = None

        # Execute
        result = await agent.get_document_versions(
            document_id=document_id
        )

        # Verify
        assert result["document"] is None
        assert result["versions"] == []
        assert f"Document with ID {document_id} not found" in result["response"]
        mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_notifications(self, agent):
        """
        Test getting document notifications.
        """
        # Setup
        document_id = "doc-001"
        is_read = False
        limit = 5
        
        # Mock document_notification_service.get_notifications
        mock_notifications = [
            {
                "id": 1,
                "document_id": document_id,
                "notification_id": "notif-001",
                "title": "Test notification",
                "description": "Test description",
                "severity": "medium",
                "is_read": is_read,
                "created_at": "2023-01-01T00:00:00",
                "affected_documents": ["doc-002"]
            }
        ]
        
        with patch('app.core.agents.documentation_agent.document_notification_service.get_notifications', return_value=mock_notifications):
            # Execute
            result = await agent.get_document_notifications(
                document_id=document_id,
                is_read=is_read,
                limit=limit
            )

            # Verify
            assert result["notifications"] == mock_notifications
            assert f"Notifications for document {document_id}" in result["response"]

    @pytest.mark.asyncio
    async def test_get_document_notifications_no_notifications(self, agent):
        """
        Test getting document notifications with no notifications found.
        """
        # Setup
        document_id = "doc-001"
        
        # Mock document_notification_service.get_notifications
        with patch('app.core.agents.documentation_agent.document_notification_service.get_notifications', return_value=[]):
            # Execute
            result = await agent.get_document_notifications(
                document_id=document_id
            )

            # Verify
            assert result["notifications"] == []
            assert f"No notifications found for document {document_id}" in result["response"]

    @pytest.mark.asyncio
    async def test_get_document_analytics(self, agent, mock_documentation_service):
        """
        Test getting document analytics.
        """
        # Setup
        document_id = "doc-001"
        
        # Mock documentation service
        mock_document = {
            "id": document_id,
            "title": "Test Document",
            "content": "Test content"
        }
        mock_documentation_service.get_documentation.return_value = mock_document
        
        # Mock document_relationship_service.get_document_analytics
        mock_analytics = {
            "document_id": document_id,
            "reference_count": 5,
            "view_count": 10,
            "last_referenced_at": "2023-01-01T00:00:00",
            "last_viewed_at": "2023-01-02T00:00:00",
            "reference_distribution": {"citation": 3, "related": 2}
        }
        
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_analytics', return_value=mock_analytics):
            # Execute
            result = await agent.get_document_analytics(
                document_id=document_id
            )

            # Verify
            assert result["document"] == mock_document
            assert result["analytics"] == mock_analytics
            assert f"Analytics for document 'Test Document'" in result["response"]
            mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_analytics_no_analytics(self, agent, mock_documentation_service):
        """
        Test getting document analytics with no analytics found.
        """
        # Setup
        document_id = "doc-001"
        
        # Mock documentation service
        mock_document = {
            "id": document_id,
            "title": "Test Document",
            "content": "Test content"
        }
        mock_documentation_service.get_documentation.return_value = mock_document
        
        # Mock document_relationship_service.get_document_analytics
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_document_analytics', return_value=None):
            # Execute
            result = await agent.get_document_analytics(
                document_id=document_id
            )

            # Verify
            assert result["document"] == mock_document
            assert result["analytics"] is None
            assert f"No analytics found for document 'Test Document'" in result["response"]
            mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_analytics_document_not_found(self, agent, mock_documentation_service):
        """
        Test getting document analytics with document not found.
        """
        # Setup
        document_id = "doc-001"
        mock_documentation_service.get_documentation.return_value = None

        # Execute
        result = await agent.get_document_analytics(
            document_id=document_id
        )

        # Verify
        assert result["document"] is None
        assert result["analytics"] is None
        assert f"Document with ID {document_id} not found" in result["response"]
        mock_documentation_service.get_documentation.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_most_referenced_documents(self, agent, mock_documentation_service):
        """
        Test getting most referenced documents.
        """
        # Setup
        limit = 5
        
        # Mock document_relationship_service.get_most_referenced_documents
        mock_documents = [
            {
                "document_id": "doc-001",
                "reference_count": 10,
                "view_count": 20,
                "reference_distribution": {"citation": 5, "related": 5}
            },
            {
                "document_id": "doc-002",
                "reference_count": 5,
                "view_count": 10,
                "reference_distribution": {"citation": 3, "related": 2}
            }
        ]
        
        with patch('app.core.agents.documentation_agent.document_relationship_service.get_most_referenced_documents', return_value=mock_documents):
            # Mock documentation service to return document titles
            mock_documentation_service.get_documentation.side_effect = [
                {"id": "doc-001", "title": "Document 1"},
                {"id": "doc-002", "title": "Document 2"}
            ]
            
            # Execute
            result = await agent.get_most_referenced_documents(limit=limit)

            # Verify
            assert result["documents"] == mock_documents
            assert f"Top {len(mock_documents)} most referenced documents" in result["response"]
            assert "Document 1" in result["response"]
            assert "Document 2" in result["response"]
