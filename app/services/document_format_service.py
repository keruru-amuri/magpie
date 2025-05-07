"""
Document Format Service for the MAGPIE platform.

This service implements industry best practices for aircraft documentation management,
including standardized formats, metadata tagging, and data schema standardization.
"""
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class DocumentFormat(str, Enum):
    """Document format types supported by the system."""
    PDF_A = "pdf/a"  # PDF/A for long-term archiving
    XML = "xml"      # XML for structured data
    JSON = "json"    # JSON for API interchange
    SGML = "sgml"    # SGML for legacy documentation
    HTML = "html"    # HTML for web viewing
    MARKDOWN = "markdown"  # Markdown for simple documentation


class DocumentStandard(str, Enum):
    """Industry standards for aircraft documentation."""
    ATA_SPEC_100 = "ata-spec-100"  # ATA Spec 100 for technical manuals
    ATA_SPEC_2000 = "ata-spec-2000"  # ATA Spec 2000 for materials management
    ATA_SPEC_2300 = "ata-spec-2300"  # ATA Spec 2300 for digital data
    S1000D = "s1000d"  # S1000D for technical publications
    DITA = "dita"  # DITA for technical content


class DocumentFormatService:
    """Service for managing document formats and standards."""

    def __init__(self):
        """Initialize the document format service."""
        self.supported_formats = [format.value for format in DocumentFormat]
        self.supported_standards = [standard.value for standard in DocumentStandard]

    def validate_document_format(self, document: Dict[str, Any], format_type: str) -> Dict[str, Any]:
        """
        Validate that a document conforms to the specified format.

        Args:
            document: Document to validate
            format_type: Format type to validate against

        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            if format_type not in self.supported_formats:
                return {
                    "valid": False,
                    "errors": [f"Unsupported format: {format_type}"]
                }

            # Validate based on format type
            if format_type == DocumentFormat.PDF_A:
                return self._validate_pdf_a(document)
            elif format_type == DocumentFormat.XML:
                return self._validate_xml(document)
            elif format_type == DocumentFormat.JSON:
                return self._validate_json(document)
            elif format_type == DocumentFormat.SGML:
                return self._validate_sgml(document)
            elif format_type == DocumentFormat.HTML:
                return self._validate_html(document)
            elif format_type == DocumentFormat.MARKDOWN:
                return self._validate_markdown(document)
            else:
                return {
                    "valid": False,
                    "errors": [f"Validation not implemented for format: {format_type}"]
                }
        except Exception as e:
            logger.error(f"Error validating document format: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }

    def validate_document_standard(self, document: Dict[str, Any], standard: str) -> Dict[str, Any]:
        """
        Validate that a document conforms to the specified industry standard.

        Args:
            document: Document to validate
            standard: Industry standard to validate against

        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            if standard not in self.supported_standards:
                return {
                    "valid": False,
                    "errors": [f"Unsupported standard: {standard}"]
                }

            # Validate based on standard
            if standard == DocumentStandard.ATA_SPEC_100:
                return self._validate_ata_spec_100(document)
            elif standard == DocumentStandard.ATA_SPEC_2000:
                return self._validate_ata_spec_2000(document)
            elif standard == DocumentStandard.ATA_SPEC_2300:
                return self._validate_ata_spec_2300(document)
            elif standard == DocumentStandard.S1000D:
                return self._validate_s1000d(document)
            elif standard == DocumentStandard.DITA:
                return self._validate_dita(document)
            else:
                return {
                    "valid": False,
                    "errors": [f"Validation not implemented for standard: {standard}"]
                }
        except Exception as e:
            logger.error(f"Error validating document standard: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }

    def convert_document_format(
        self,
        document: Dict[str, Any],
        source_format: str,
        target_format: str
    ) -> Dict[str, Any]:
        """
        Convert a document from one format to another.

        Args:
            document: Document to convert
            source_format: Source format
            target_format: Target format

        Returns:
            Dict[str, Any]: Converted document or error information
        """
        try:
            if source_format not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"Unsupported source format: {source_format}"
                }

            if target_format not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"Unsupported target format: {target_format}"
                }

            # If source and target are the same, return the document
            if source_format == target_format:
                return {
                    "success": True,
                    "document": document
                }

            # Implement conversion logic based on source and target formats
            # For now, we'll implement a simple JSON to Markdown conversion as an example
            if source_format == DocumentFormat.JSON and target_format == DocumentFormat.MARKDOWN:
                converted = self._convert_json_to_markdown(document)
                return {
                    "success": True,
                    "document": converted
                }
            else:
                return {
                    "success": False,
                    "error": f"Conversion from {source_format} to {target_format} not implemented"
                }
        except Exception as e:
            logger.error(f"Error converting document format: {str(e)}")
            return {
                "success": False,
                "error": f"Conversion error: {str(e)}"
            }

    def apply_metadata_schema(self, document: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
        """
        Apply a metadata schema to a document.

        Args:
            document: Document to apply schema to
            schema_type: Type of schema to apply

        Returns:
            Dict[str, Any]: Document with applied schema
        """
        try:
            # Apply schema based on type
            if schema_type == "ata":
                return self._apply_ata_metadata_schema(document)
            elif schema_type == "s1000d":
                return self._apply_s1000d_metadata_schema(document)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported schema type: {schema_type}"
                }
        except Exception as e:
            logger.error(f"Error applying metadata schema: {str(e)}")
            return {
                "success": False,
                "error": f"Schema application error: {str(e)}"
            }

    def validate_document_completeness(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a document is complete according to industry standards.

        Args:
            document: Document to validate

        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            errors = []
            warnings = []

            # Check for required fields
            required_fields = ["id", "title", "type", "version", "last_updated", "content"]
            for field in required_fields:
                if field not in document:
                    errors.append(f"Missing required field: {field}")

            # Check for sections
            if "sections" not in document or not document["sections"]:
                errors.append("Document must have at least one section")
            else:
                # Check section structure
                for i, section in enumerate(document["sections"]):
                    if "id" not in section:
                        errors.append(f"Section {i+1} is missing an ID")
                    if "title" not in section:
                        errors.append(f"Section {i+1} is missing a title")
                    if "content" not in section:
                        errors.append(f"Section {i+1} is missing content")

            # Check for recommended fields
            recommended_fields = ["author", "approval_status", "applicable_aircraft"]
            for field in recommended_fields:
                if field not in document:
                    warnings.append(f"Recommended field missing: {field}")

            # Check version format (should be semantic versioning)
            if "version" in document:
                version = document["version"]
                if not self._is_valid_version_format(version):
                    warnings.append(f"Version format '{version}' does not follow semantic versioning (e.g., 1.0.0)")

            # Check date format
            if "last_updated" in document:
                date = document["last_updated"]
                if not self._is_valid_date_format(date):
                    warnings.append(f"Date format '{date}' is not in YYYY-MM-DD format")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
        except Exception as e:
            logger.error(f"Error validating document completeness: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }

    def generate_document_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate standardized metadata for a document.

        Args:
            document: Document to generate metadata for

        Returns:
            Dict[str, Any]: Generated metadata
        """
        try:
            metadata = {
                "document_id": document.get("id", ""),
                "title": document.get("title", ""),
                "document_type": document.get("type", ""),
                "version": document.get("version", ""),
                "last_updated": document.get("last_updated", ""),
                "generated_at": datetime.now().isoformat(),
                "section_count": len(document.get("sections", [])),
                "content_length": len(document.get("content", "")),
                "has_safety_information": self._contains_safety_information(document),
                "ata_chapters": self._extract_ata_chapters(document),
                "aircraft_types": self._extract_aircraft_types(document),
                "components": self._extract_components(document),
                "keywords": self._extract_keywords(document)
            }

            return {
                "success": True,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error generating document metadata: {str(e)}")
            return {
                "success": False,
                "error": f"Metadata generation error: {str(e)}"
            }

    # Private validation methods
    def _validate_pdf_a(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PDF/A format."""
        # Mock implementation - in a real system, this would use a PDF/A validation library
        return {"valid": True, "errors": []}

    def _validate_xml(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate XML format."""
        # Mock implementation
        return {"valid": True, "errors": []}

    def _validate_json(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON format."""
        try:
            # Check if document can be serialized to JSON
            json.dumps(document)
            return {"valid": True, "errors": []}
        except Exception as e:
            return {"valid": False, "errors": [f"Invalid JSON: {str(e)}"]}

    def _validate_sgml(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SGML format."""
        # Mock implementation
        return {"valid": True, "errors": []}

    def _validate_html(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate HTML format."""
        # Mock implementation
        return {"valid": True, "errors": []}

    def _validate_markdown(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Markdown format."""
        # Mock implementation
        return {"valid": True, "errors": []}

    # Private standard validation methods
    def _validate_ata_spec_100(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ATA Spec 100 standard."""
        errors = []

        # Check for ATA chapter structure
        if "sections" in document:
            has_valid_ata_chapter = False
            for section in document["sections"]:
                if "title" in section and self._is_valid_ata_chapter_title(section["title"]):
                    has_valid_ata_chapter = True
                    break

            if not has_valid_ata_chapter:
                errors.append("Document does not contain any sections with valid ATA chapter format")

        return {"valid": len(errors) == 0, "errors": errors}

    def _validate_ata_spec_2000(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ATA Spec 2000 standard."""
        # Mock implementation
        return {"valid": True, "errors": []}

    def _validate_ata_spec_2300(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ATA Spec 2300 standard."""
        # Mock implementation
        return {"valid": True, "errors": []}

    def _validate_s1000d(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate S1000D standard."""
        # Mock implementation
        return {"valid": True, "errors": []}

    def _validate_dita(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DITA standard."""
        # Mock implementation
        return {"valid": True, "errors": []}

    # Private conversion methods
    def _convert_json_to_markdown(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON to Markdown."""
        try:
            markdown = f"# {document.get('title', 'Untitled Document')}\n\n"
            markdown += f"**Document ID:** {document.get('id', 'Unknown')}\n"
            markdown += f"**Version:** {document.get('version', 'Unknown')}\n"
            markdown += f"**Last Updated:** {document.get('last_updated', 'Unknown')}\n\n"
            markdown += f"## Overview\n\n{document.get('content', '')}\n\n"

            # Add sections
            if "sections" in document and document["sections"]:
                for section in document["sections"]:
                    markdown += f"## {section.get('title', 'Untitled Section')}\n\n"
                    markdown += f"{section.get('content', '')}\n\n"

            return {
                "content": markdown,
                "format": "markdown"
            }
        except Exception as e:
            logger.error(f"Error converting JSON to Markdown: {str(e)}")
            raise

    # Private schema application methods
    def _apply_ata_metadata_schema(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Apply ATA metadata schema."""
        try:
            # Extract ATA chapter from document title or content
            ata_chapter = self._extract_ata_chapter(document)

            # Apply ATA schema
            metadata = {
                "ata_chapter": ata_chapter,
                "document_type": document.get("type", ""),
                "effectivity": self._extract_aircraft_types(document),
                "revision": document.get("version", ""),
                "date": document.get("last_updated", ""),
                "security_classification": "Unclassified",  # Default
                "export_control": "No restrictions",  # Default
                "proprietary_information": True,  # Default
                "distribution_restriction": "Restricted",  # Default
            }

            # Add metadata to document
            document["metadata"] = metadata
            return {
                "success": True,
                "document": document
            }
        except Exception as e:
            logger.error(f"Error applying ATA metadata schema: {str(e)}")
            return {
                "success": False,
                "error": f"Schema application error: {str(e)}"
            }

    def _apply_s1000d_metadata_schema(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Apply S1000D metadata schema."""
        try:
            # Apply S1000D schema
            metadata = {
                "data_module_code": f"DMC-{document.get('id', 'UNKNOWN')}",
                "issue_number": document.get("version", ""),
                "issue_date": document.get("last_updated", ""),
                "language": "en",
                "security_classification": "01",  # Unclassified
                "responsible_partner_company": "MAGPIE",
                "originator": "MAGPIE",
                "applicability": self._extract_aircraft_types(document),
                "technical_name": document.get("title", ""),
                "info_code": "000",  # Default
                "info_name": "Description",  # Default
            }

            # Add metadata to document
            document["metadata"] = metadata
            return {
                "success": True,
                "document": document
            }
        except Exception as e:
            logger.error(f"Error applying S1000D metadata schema: {str(e)}")
            return {
                "success": False,
                "error": f"Schema application error: {str(e)}"
            }

    # Helper methods
    def _is_valid_version_format(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        import re
        pattern = r'^\d+(\.\d+){0,2}$'
        return bool(re.match(pattern, version))

    def _is_valid_date_format(self, date: str) -> bool:
        """Check if date is in YYYY-MM-DD format."""
        import re
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, date))

    def _is_valid_ata_chapter_title(self, title: str) -> bool:
        """Check if title follows ATA chapter format."""
        import re
        # Look for patterns like "Chapter 29: Hydraulic Power" or "29 - Hydraulic Power"
        pattern = r'^(Chapter\s+)?\d{2}(\s*[-:]\s*.+)?$'
        return bool(re.match(pattern, title))

    def _contains_safety_information(self, document: Dict[str, Any]) -> bool:
        """Check if document contains safety information."""
        safety_keywords = ["warning", "caution", "danger", "safety", "hazard"]

        # Check document content
        content = document.get("content", "").lower()
        if any(keyword in content for keyword in safety_keywords):
            return True

        # Check section content
        for section in document.get("sections", []):
            section_content = section.get("content", "").lower()
            if any(keyword in section_content for keyword in safety_keywords):
                return True

        return False

    def _extract_ata_chapter(self, document: Dict[str, Any]) -> str:
        """Extract ATA chapter from document."""
        import re

        # Try to extract from title
        title = document.get("title", "")
        chapter_match = re.search(r'Chapter\s+(\d{2})', title)
        if chapter_match:
            return chapter_match.group(1)

        # Try to extract from content
        content = document.get("content", "")
        chapter_match = re.search(r'Chapter\s+(\d{2})', content)
        if chapter_match:
            return chapter_match.group(1)

        # Default to unknown
        return "XX"

    def _extract_ata_chapters(self, document: Dict[str, Any]) -> List[str]:
        """Extract all ATA chapters mentioned in document."""
        import re

        chapters = set()

        # Extract from title and content
        text = document.get("title", "") + " " + document.get("content", "")
        chapter_matches = re.findall(r'Chapter\s+(\d{2})', text)
        chapters.update(chapter_matches)

        # Extract from sections
        for section in document.get("sections", []):
            section_text = section.get("title", "") + " " + section.get("content", "")
            section_matches = re.findall(r'Chapter\s+(\d{2})', section_text)
            chapters.update(section_matches)

        return list(chapters)

    def _extract_aircraft_types(self, document: Dict[str, Any]) -> List[str]:
        """Extract aircraft types mentioned in document."""
        aircraft_types = []

        # Common aircraft types to look for
        common_types = [
            "Boeing 737", "Boeing 747", "Boeing 777", "Boeing 787",
            "Airbus A320", "Airbus A330", "Airbus A350", "Airbus A380",
            "Embraer E190", "Bombardier CRJ"
        ]

        # Check title and content
        text = document.get("title", "") + " " + document.get("content", "")
        for aircraft in common_types:
            if aircraft in text:
                aircraft_types.append(aircraft)

        # Check sections
        for section in document.get("sections", []):
            section_text = section.get("title", "") + " " + section.get("content", "")
            for aircraft in common_types:
                if aircraft in section_text and aircraft not in aircraft_types:
                    aircraft_types.append(aircraft)

        return aircraft_types

    def _extract_components(self, document: Dict[str, Any]) -> List[str]:
        """Extract aircraft components mentioned in document."""
        components = []

        # Common components to look for
        common_components = [
            "hydraulic pump", "generator", "battery", "engine", "landing gear",
            "flap", "slat", "rudder", "elevator", "aileron", "APU", "fuel pump"
        ]

        # Check title and content
        text = document.get("title", "").lower() + " " + document.get("content", "").lower()
        for component in common_components:
            if component in text:
                components.append(component)

        # Check sections
        for section in document.get("sections", []):
            section_text = section.get("title", "").lower() + " " + section.get("content", "").lower()
            for component in common_components:
                if component in section_text and component not in components:
                    components.append(component)

        return components

    def _extract_keywords(self, document: Dict[str, Any]) -> List[str]:
        """Extract keywords from document."""
        # This is a simplified implementation
        # In a real system, this would use NLP techniques for keyword extraction

        keywords = set()

        # Add document type as keyword
        doc_type = document.get("type", "")
        if doc_type:
            keywords.add(doc_type)

        # Add aircraft types as keywords
        aircraft_types = self._extract_aircraft_types(document)
        keywords.update(aircraft_types)

        # Add components as keywords
        components = self._extract_components(document)
        keywords.update(components)

        # Add ATA chapters as keywords
        ata_chapters = self._extract_ata_chapters(document)
        keywords.update([f"ATA{chapter}" for chapter in ata_chapters])

        return list(keywords)


# Create singleton instance
document_format_service = DocumentFormatService()
