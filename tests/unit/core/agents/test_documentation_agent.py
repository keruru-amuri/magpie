"""
Unit tests for the DocumentationAgent.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.core.agents.documentation_agent import DocumentationAgent


class TestDocumentationAgent:
    """
    Test the DocumentationAgent class.
    """

    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        service = MagicMock()
        service.generate_completion = AsyncMock(return_value={"content": "This is a mock response"})
        service.generate_completion_raw = AsyncMock(return_value={"content": "This is a mock raw response"})
        return service

    @pytest.fixture
    def mock_documentation_service(self):
        """
        Create a mock documentation service.
        """
        service = MagicMock()
        # Mock search_documentation method
        service.search_documentation = MagicMock(return_value={
            "query": {"text": "test query"},
            "results_count": 2,
            "results": [
                {
                    "doc_id": "doc-001",
                    "section_id": "section-1",
                    "title": "Introduction",
                    "relevance_score": 0.95,
                    "snippet": "This is a test snippet from document 1",
                    "document_title": "Test Document 1",
                    "document_type": "manual"
                },
                {
                    "doc_id": "doc-002",
                    "section_id": "section-2",
                    "title": "Safety Precautions",
                    "relevance_score": 0.85,
                    "snippet": "This is a test snippet from document 2",
                    "document_title": "Test Document 2",
                    "document_type": "bulletin"
                }
            ]
        })

        # Mock get_documentation method
        service.get_documentation = MagicMock(return_value={
            "id": "doc-001",
            "title": "Test Document 1",
            "type": "manual",
            "version": "1.0",
            "last_updated": "2025-01-15",
            "content": "This is test content for document 1",
            "sections": [
                {
                    "id": "section-1",
                    "title": "Introduction",
                    "content": "This is the introduction section content."
                },
                {
                    "id": "section-2",
                    "title": "Safety Precautions",
                    "content": "This is the safety precautions section content."
                }
            ]
        })

        # Legacy method for backward compatibility with existing tests
        service.search_documents = AsyncMock(return_value=[
            {
                "id": "doc-001",
                "title": "Test Document 1",
                "content": "This is test content for document 1",
                "relevance": 0.9,
                "source": "Test Source",
                "url": "https://example.com/doc1",
                "document_type": "manual"
            },
            {
                "id": "doc-002",
                "title": "Test Document 2",
                "content": "This is test content for document 2",
                "relevance": 0.8,
                "source": "Test Source",
                "url": "https://example.com/doc2",
                "document_type": "bulletin"
            }
        ])

        # Legacy method for backward compatibility with existing tests
        service.get_document = AsyncMock(return_value={
            "id": "doc-001",
            "title": "Test Document 1",
            "content": "This is test content for document 1",
            "source": "Test Source",
            "url": "https://example.com/doc1",
            "metadata": {
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic",
                "document_type": "Manual"
            }
        })

        return service

    @pytest.fixture
    def agent(self, mock_llm_service, mock_documentation_service):
        """
        Create a DocumentationAgent instance.
        """
        return DocumentationAgent(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service
        )

    @pytest.mark.asyncio
    async def test_process_query(self, agent, mock_llm_service):
        """
        Test processing a query.
        """
        # Mock the search_documentation method to return test data
        agent.search_documentation = AsyncMock(return_value=[
            {
                "id": "doc-001",
                "title": "Test Document 1",
                "content": "This is test content for document 1",
                "relevance": 0.9,
                "source": "Test Source",
                "document_type": "manual"
            },
            {
                "id": "doc-002",
                "title": "Test Document 2",
                "content": "This is test content for document 2",
                "relevance": 0.8,
                "source": "Test Source",
                "document_type": "bulletin"
            }
        ])

        # Call process_query
        result = await agent.process_query(
            query="Where can I find information about landing gear maintenance?",
            context={"aircraft_type": "Boeing 737"}
        )

        # Verify result
        assert "response" in result
        assert "sources" in result
        assert result["response"] == "This is a mock response"
        assert len(result["sources"]) == 2

        # Verify search_documentation was called
        agent.search_documentation.assert_called_once()

        # Verify generate_response was called
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_documentation(self, agent, mock_documentation_service):
        """
        Test searching documentation.
        """
        # Call search_documentation
        result = await agent.search_documentation(
            query="landing gear maintenance",
            context={"aircraft_type": "Boeing 737", "system": "Landing Gear"}
        )

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "doc-001"
        assert result[1]["id"] == "doc-002"

        # Verify search_documentation was called with correct parameters
        expected_params = {
            "text": "landing gear maintenance",
            "aircraft_type": "Boeing 737",
            "system": "Landing Gear",
            "max_results": 5
        }
        mock_documentation_service.search_documentation.assert_called_once()
        call_args = mock_documentation_service.search_documentation.call_args[0][0]
        for key, value in expected_params.items():
            assert key in call_args
            assert call_args[key] == value

    @pytest.mark.asyncio
    async def test_search_documentation_new(self, agent, mock_documentation_service):
        """
        Test the updated search_documentation method that uses the new search_documentation service method.
        """
        # Reset the mock to clear previous calls
        mock_documentation_service.search_documentation.reset_mock()

        # Call search_documentation
        result = await agent.search_documentation(
            query="hydraulic system maintenance",
            context={
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic",
                "keywords": ["maintenance", "hydraulic"]
            }
        )

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "doc-001"
        assert result[0]["title"] == "Test Document 1 - Introduction"
        assert result[0]["relevance"] == 0.95
        assert result[0]["document_type"] == "manual"

        # Verify search_documentation was called with correct parameters
        expected_params = {
            "text": "hydraulic system maintenance",
            "aircraft_type": "Boeing 737",
            "system": "Hydraulic",
            "keywords": ["maintenance", "hydraulic"],
            "max_results": 5
        }
        mock_documentation_service.search_documentation.assert_called_once()
        call_args = mock_documentation_service.search_documentation.call_args[0][0]
        for key, value in expected_params.items():
            assert key in call_args
            assert call_args[key] == value

    @pytest.mark.asyncio
    async def test_generate_response(self, agent, mock_llm_service):
        """
        Test generating a response.
        """
        # Create search results
        search_results = [
            {
                "id": "doc-001",
                "title": "Test Document 1",
                "content": "This is test content for document 1",
                "relevance": 0.9,
                "source": "Test Source",
                "document_type": "manual"
            },
            {
                "id": "doc-002",
                "title": "Test Document 2",
                "content": "This is test content for document 2",
                "relevance": 0.8,
                "source": "Test Source",
                "document_type": "bulletin"
            }
        ]

        # Call generate_response
        result = await agent.generate_response(
            query="landing gear maintenance",
            search_results=search_results,
            context={"aircraft_type": "Boeing 737"}
        )

        # Verify result
        assert result == "This is a mock response"

        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize_document(self, agent, mock_llm_service, mock_documentation_service):
        """
        Test summarizing a document.
        """
        # Call summarize_document
        result = await agent.summarize_document(
            document_id="doc-001",
            context={"aircraft_type": "Boeing 737"}
        )

        # Verify result
        assert "response" in result
        assert "document" in result
        assert result["response"] == "This is a mock response"
        assert result["document"]["id"] == "doc-001"

        # Verify get_documentation was called
        mock_documentation_service.get_documentation.assert_called_once_with("doc-001")

        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_query_no_results(self, agent):
        """
        Test processing a query with no search results.
        """
        # Mock search_documentation to return empty list
        agent.search_documentation = AsyncMock(return_value=[])

        # Call process_query
        result = await agent.process_query(
            query="Where can I find information about landing gear maintenance?"
        )

        # Verify result
        assert "response" in result
        assert "sources" in result
        assert "I couldn't find any relevant documentation" in result["response"]
        assert len(result["sources"]) == 0

        # Verify search_documentation was called
        agent.search_documentation.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_query_error(self, agent):
        """
        Test processing a query with an error.
        """
        # Mock search_documentation to raise an exception
        agent.search_documentation = AsyncMock(side_effect=Exception("Test error"))

        # Call process_query
        result = await agent.process_query(
            query="Where can I find information about landing gear maintenance?"
        )

        # Verify result
        assert "response" in result
        assert "sources" in result
        assert "error" in result["response"].lower()
        assert len(result["sources"]) == 0

        # Verify search_documentation was called
        agent.search_documentation.assert_called_once()

    @pytest.mark.asyncio
    async def test_compare_documents(self, agent, mock_llm_service, mock_documentation_service):
        """
        Test comparing documents.
        """
        # Call compare_documents
        result = await agent.compare_documents(
            document_ids=["doc-001", "doc-002"],
            comparison_aspect="safety precautions",
            context={"aircraft_type": "Boeing 737"}
        )

        # Verify result
        assert "response" in result
        assert "documents" in result
        assert result["response"] == "This is a mock response"
        assert len(result["documents"]) == 2

        # Verify get_documentation was called twice (once for each document)
        assert mock_documentation_service.get_documentation.call_count == 2

        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_section(self, agent, mock_documentation_service):
        """
        Test extracting a section from a document.
        """
        # Call extract_section with section_id
        result = await agent.extract_section(
            document_id="doc-001",
            section_id="section-2"
        )

        # Verify result
        assert "response" in result
        assert "section" in result
        assert "document" in result
        assert result["section"]["id"] == "section-2"
        assert result["section"]["title"] == "Safety Precautions"
        assert result["document"]["id"] == "doc-001"

        # Reset mock and test with section_title
        mock_documentation_service.get_documentation.reset_mock()

        # Call extract_section with section_title
        result = await agent.extract_section(
            document_id="doc-001",
            section_title="Safety"
        )

        # Verify result
        assert "response" in result
        assert "section" in result
        assert "document" in result
        assert result["section"]["id"] == "section-2"
        assert result["section"]["title"] == "Safety Precautions"
        assert result["document"]["id"] == "doc-001"

        # Verify get_documentation was called
        mock_documentation_service.get_documentation.assert_called_once_with("doc-001")

    @pytest.mark.asyncio
    async def test_extract_section_not_found(self, agent):
        """
        Test extracting a section that doesn't exist.
        """
        # Call extract_section with non-existent section
        result = await agent.extract_section(
            document_id="doc-001",
            section_id="non-existent-section"
        )

        # Verify result
        assert "response" in result
        assert "section" in result
        assert "document" in result
        assert result["section"] is None
        assert "couldn't find" in result["response"]
        assert result["document"]["id"] == "doc-001"

    @pytest.mark.asyncio
    async def test_compare_documents_not_enough_docs(self, agent):
        """
        Test comparing documents with not enough valid documents.
        """
        # Call compare_documents with only one document
        result = await agent.compare_documents(
            document_ids=["doc-001"]
        )

        # Verify result
        assert "response" in result
        assert "documents" in result
        assert "need at least two documents" in result["response"]
        assert len(result["documents"]) == 0
