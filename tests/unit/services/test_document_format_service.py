"""
Unit tests for the document format service.
"""
import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from app.services.document_format_service import document_format_service, DocumentFormat, DocumentStandard


class TestDocumentFormatService:
    """Test cases for the document format service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_document = {
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

    def test_validate_document_format_json_valid(self):
        """Test validating a document in JSON format."""
        # Test with valid JSON document
        result = document_format_service.validate_document_format(self.sample_document, DocumentFormat.JSON)

        assert result["valid"] is True
        assert "errors" in result
        assert len(result["errors"]) == 0

    def test_validate_document_format_json_invalid(self):
        """Test validating an invalid JSON document."""
        # Create a document with a circular reference (not JSON serializable)
        invalid_document = self.sample_document.copy()
        invalid_document["circular_ref"] = invalid_document

        result = document_format_service.validate_document_format(invalid_document, DocumentFormat.JSON)

        assert result["valid"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0

    def test_validate_document_format_unsupported(self):
        """Test validating a document with an unsupported format."""
        result = document_format_service.validate_document_format(self.sample_document, "unsupported_format")

        assert result["valid"] is False
        assert "errors" in result
        assert "Unsupported format" in result["errors"][0]

    def test_validate_document_standard_ata_spec_100_valid(self):
        """Test validating a document against ATA Spec 100 standard."""
        # Test with valid ATA Spec 100 document
        result = document_format_service.validate_document_standard(self.sample_document, DocumentStandard.ATA_SPEC_100)

        assert result["valid"] is True
        assert "errors" in result
        assert len(result["errors"]) == 0

    def test_validate_document_standard_unsupported(self):
        """Test validating a document against an unsupported standard."""
        result = document_format_service.validate_document_standard(self.sample_document, "unsupported_standard")

        assert result["valid"] is False
        assert "errors" in result
        assert "Unsupported standard" in result["errors"][0]

    def test_convert_document_format_json_to_markdown(self):
        """Test converting a document from JSON to Markdown."""
        result = document_format_service.convert_document_format(
            self.sample_document,
            DocumentFormat.JSON,
            DocumentFormat.MARKDOWN
        )

        assert result["success"] is True
        assert "document" in result
        assert "content" in result["document"]
        assert "# Boeing 737-800 Aircraft Maintenance Manual" in result["document"]["content"]
        assert "## Introduction" in result["document"]["content"]
        assert "## Chapter 29: Hydraulic Power" in result["document"]["content"]

    def test_convert_document_format_same_format(self):
        """Test converting a document to the same format."""
        result = document_format_service.convert_document_format(
            self.sample_document,
            DocumentFormat.JSON,
            DocumentFormat.JSON
        )

        assert result["success"] is True
        assert "document" in result
        assert result["document"] == self.sample_document

    def test_convert_document_format_unsupported_conversion(self):
        """Test converting a document with an unsupported conversion."""
        result = document_format_service.convert_document_format(
            self.sample_document,
            DocumentFormat.JSON,
            DocumentFormat.PDF_A
        )

        assert result["success"] is False
        assert "error" in result
        assert "Conversion from" in result["error"]
        assert "not implemented" in result["error"]

    def test_apply_metadata_schema_ata(self):
        """Test applying ATA metadata schema to a document."""
        result = document_format_service.apply_metadata_schema(self.sample_document, "ata")

        assert result["success"] is True
        assert "document" in result
        assert "metadata" in result["document"]
        assert "ata_chapter" in result["document"]["metadata"]
        assert "document_type" in result["document"]["metadata"]
        assert "effectivity" in result["document"]["metadata"]

    def test_apply_metadata_schema_unsupported(self):
        """Test applying an unsupported metadata schema."""
        result = document_format_service.apply_metadata_schema(self.sample_document, "unsupported_schema")

        assert result["success"] is False
        assert "error" in result
        assert "Unsupported schema type" in result["error"]

    def test_validate_document_completeness_valid(self):
        """Test validating a complete document."""
        result = document_format_service.validate_document_completeness(self.sample_document)

        assert result["valid"] is True
        assert "errors" in result
        assert len(result["errors"]) == 0

    def test_validate_document_completeness_invalid(self):
        """Test validating an incomplete document."""
        # Create an incomplete document
        incomplete_document = {
            "id": "doc-001",
            "title": "Boeing 737-800 Aircraft Maintenance Manual",
            # Missing required fields: type, version, last_updated, content
            "sections": []  # Empty sections
        }

        result = document_format_service.validate_document_completeness(incomplete_document)

        assert result["valid"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "Missing required field: type" in result["errors"]
        assert "Missing required field: version" in result["errors"]
        assert "Missing required field: last_updated" in result["errors"]
        assert "Missing required field: content" in result["errors"]
        assert "Document must have at least one section" in result["errors"]

    def test_generate_document_metadata(self):
        """Test generating metadata for a document."""
        result = document_format_service.generate_document_metadata(self.sample_document)

        assert result["success"] is True
        assert "metadata" in result
        assert result["metadata"]["document_id"] == "doc-001"
        assert result["metadata"]["title"] == "Boeing 737-800 Aircraft Maintenance Manual"
        assert result["metadata"]["document_type"] == "manual"
        assert result["metadata"]["version"] == "2.1"
        assert result["metadata"]["section_count"] == 2
        assert "Boeing 737" in result["metadata"]["aircraft_types"]
        assert "29" in result["metadata"]["ata_chapters"]

    def test_is_valid_version_format(self):
        """Test version format validation."""
        assert document_format_service._is_valid_version_format("1.0") is True
        assert document_format_service._is_valid_version_format("2.1.3") is True
        assert document_format_service._is_valid_version_format("3") is True
        assert document_format_service._is_valid_version_format("1.0-alpha") is False
        assert document_format_service._is_valid_version_format("invalid") is False

    def test_is_valid_date_format(self):
        """Test date format validation."""
        assert document_format_service._is_valid_date_format("2025-02-15") is True
        assert document_format_service._is_valid_date_format("2025-2-15") is False
        assert document_format_service._is_valid_date_format("02/15/2025") is False
        assert document_format_service._is_valid_date_format("invalid") is False

    def test_is_valid_ata_chapter_title(self):
        """Test ATA chapter title validation."""
        assert document_format_service._is_valid_ata_chapter_title("Chapter 29: Hydraulic Power") is True
        assert document_format_service._is_valid_ata_chapter_title("29 - Hydraulic Power") is True
        assert document_format_service._is_valid_ata_chapter_title("29") is True
        assert document_format_service._is_valid_ata_chapter_title("Hydraulic Power") is False
        assert document_format_service._is_valid_ata_chapter_title("Chapter: Hydraulic Power") is False

    def test_contains_safety_information(self):
        """Test safety information detection."""
        # Create a document with safety information
        safety_document = self.sample_document.copy()
        safety_document["content"] = "This manual contains important safety warnings."

        assert document_format_service._contains_safety_information(safety_document) is True
        assert document_format_service._contains_safety_information(self.sample_document) is False

    def test_extract_aircraft_types(self):
        """Test aircraft type extraction."""
        aircraft_types = document_format_service._extract_aircraft_types(self.sample_document)

        assert "Boeing 737" in aircraft_types
        assert len(aircraft_types) >= 1
