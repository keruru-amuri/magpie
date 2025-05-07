"""
Integration tests for the document management system.

These tests verify the functionality of the digital documentation management best practices
implementation, including document format validation, metadata generation, and standards compliance.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from app.services.document_format_service import document_format_service, DocumentFormat, DocumentStandard
from app.core.agents.documentation_agent import DocumentationAgent


@pytest.fixture
def mock_documentation_service():
    """Create a mock documentation service."""
    mock_service = MagicMock()

    # Sample document
    sample_document = {
        "id": "doc-001",
        "title": "Boeing 737-800 Aircraft Maintenance Manual",
        "type": "manual",
        "version": "2.1",
        "last_updated": "2025-02-15",
        "content": "This Aircraft Maintenance Manual (AMM) provides detailed procedures for maintaining the Boeing 737-800 aircraft.",
        "sections": [
            {
                "id": "doc-001-section-1",
                "title": "Introduction",
                "content": "This manual contains essential information for maintenance personnel."
            },
            {
                "id": "doc-001-section-2",
                "title": "Chapter 29: Hydraulic Power",
                "content": "This chapter covers the hydraulic power system of the Boeing 737-800 aircraft."
            }
        ]
    }

    # Configure mock to return the sample document
    mock_service.get_documentation.return_value = sample_document

    return mock_service


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    mock_service = MagicMock()
    mock_service.generate_completion = AsyncMock(return_value={"content": "Generated content"})
    return mock_service


@pytest.fixture
def agent(mock_documentation_service, mock_llm_service):
    """Create a DocumentationAgent instance with mock services."""
    return DocumentationAgent(
        llm_service=mock_llm_service,
        documentation_service=mock_documentation_service
    )


class TestDocumentManagementIntegration:
    """Integration tests for document management features."""

    @pytest.mark.asyncio
    async def test_validate_document_format_integration(self, agent):
        """Test document format validation integration."""
        # Test with valid format
        result = await agent.validate_document_format("doc-001", DocumentFormat.JSON)

        assert result["valid"] is True
        assert "Document 'Boeing 737-800 Aircraft Maintenance Manual' is valid" in result["response"]
        assert "document" in result

        # Test with invalid document ID
        agent.documentation_service.get_documentation.return_value = None
        result = await agent.validate_document_format("invalid-id", DocumentFormat.JSON)

        assert result["valid"] is False
        assert "Document with ID invalid-id not found" in result["response"]

    @pytest.mark.asyncio
    async def test_validate_document_standard_integration(self, agent):
        """Test document standard validation integration."""
        # Test with valid standard
        result = await agent.validate_document_standard("doc-001", DocumentStandard.ATA_SPEC_100)

        assert result["valid"] is True
        assert "Document 'Boeing 737-800 Aircraft Maintenance Manual' is valid" in result["response"]
        assert "document" in result

        # Test with invalid standard
        result = await agent.validate_document_standard("doc-001", "invalid_standard")

        assert result["valid"] is False
        assert "not valid" in result["response"]
        assert "Unsupported standard" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_convert_document_format_integration(self, agent):
        """Test document format conversion integration."""
        # Test JSON to Markdown conversion
        result = await agent.convert_document_format("doc-001", DocumentFormat.MARKDOWN)

        assert result["success"] is True
        assert "was successfully converted to" in result["response"]
        assert "document" in result
        assert "converted_document" in result
        assert "Preview" in result["response"]

        # Test with invalid document ID
        agent.documentation_service.get_documentation.return_value = None
        result = await agent.convert_document_format("invalid-id", DocumentFormat.MARKDOWN)

        assert result["success"] is False
        assert "Document with ID invalid-id not found" in result["response"]

    @pytest.mark.asyncio
    async def test_apply_metadata_schema_integration(self, agent):
        """Test metadata schema application integration."""
        # Test with ATA schema
        result = await agent.apply_metadata_schema("doc-001", "ata")

        assert result["success"] is True
        assert "Successfully applied ata metadata schema" in result["response"]
        assert "document" in result
        assert "Metadata Preview" in result["response"]

        # Test with invalid schema
        result = await agent.apply_metadata_schema("doc-001", "invalid_schema")

        assert result["success"] is False
        assert "Failed to apply" in result["response"]
        assert "Unsupported schema type" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_document_completeness_integration(self, agent):
        """Test document completeness validation integration."""
        # Test with complete document
        result = await agent.validate_document_completeness("doc-001")

        assert result["valid"] is True
        assert "Document 'Boeing 737-800 Aircraft Maintenance Manual' is complete" in result["response"]
        assert "document" in result

        # Test with incomplete document
        incomplete_document = {
            "id": "doc-002",
            "title": "Incomplete Document",
            # Missing required fields
            "sections": []
        }
        agent.documentation_service.get_documentation.return_value = incomplete_document

        result = await agent.validate_document_completeness("doc-002")

        assert result["valid"] is False
        assert "not complete" in result["response"]
        assert "errors" in result
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_generate_document_metadata_integration(self, agent):
        """Test document metadata generation integration."""
        # Test metadata generation
        result = await agent.generate_document_metadata("doc-001")

        assert result["success"] is True
        assert "Successfully generated metadata" in result["response"]
        assert "metadata" in result
        assert "document" in result
        assert "Metadata" in result["response"]

        # Verify metadata content
        metadata = result["metadata"]
        assert metadata["document_id"] == "doc-001"
        assert metadata["title"] == "Boeing 737-800 Aircraft Maintenance Manual"
        assert metadata["document_type"] == "manual"
        assert metadata["version"] == "2.1"
        assert "Boeing 737" in metadata["aircraft_types"]
        assert "29" in metadata["ata_chapters"]

        # Test with invalid document ID
        agent.documentation_service.get_documentation.return_value = None
        result = await agent.generate_document_metadata("invalid-id")

        assert result["success"] is False
        assert "Document with ID invalid-id not found" in result["response"]
