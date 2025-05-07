"""Utilities for generating mock data."""

import json
import logging
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import yaml conditionally to avoid dependency issues
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from app.core.mock.config import MockDataConfig, MockDataSource, mock_data_config

logger = logging.getLogger(__name__)


class MockDataGenerator:
    """Generator for mock data."""

    def __init__(self, config: MockDataConfig = mock_data_config):
        """
        Initialize the mock data generator.

        Args:
            config: Mock data configuration.
        """
        self.config = config

    def _ensure_directory_exists(self, directory: Path):
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory: Directory path.
        """
        os.makedirs(directory, exist_ok=True)

    def _write_json_file(self, file_path: Path, data: Any):
        """
        Write data to a JSON file.

        Args:
            file_path: Path to the JSON file.
            data: Data to write.
        """
        self._ensure_directory_exists(file_path.parent)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def _write_yaml_file(self, file_path: Path, data: Any):
        """
        Write data to a YAML file.

        Args:
            file_path: Path to the YAML file.
            data: Data to write.

        Raises:
            ImportError: If PyYAML is not available.
        """
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is not installed. Cannot write YAML files.")

        self._ensure_directory_exists(file_path.parent)
        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def _write_text_file(self, file_path: Path, text: str):
        """
        Write text to a file.

        Args:
            file_path: Path to the text file.
            text: Text to write.
        """
        self._ensure_directory_exists(file_path.parent)
        with open(file_path, "w") as f:
            f.write(text)

    def generate_documentation_schemas(self):
        """Generate JSON schemas for documentation data."""
        # Ensure schemas directory exists
        schemas_dir = self.config.paths.schemas_path / MockDataSource.DOCUMENTATION.value
        self._ensure_directory_exists(schemas_dir)

        # Generate documentation schema
        documentation_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Documentation",
            "description": "Schema for technical documentation",
            "type": "object",
            "required": ["id", "title", "type", "version", "last_updated", "content", "sections"],
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique identifier for the documentation"
                },
                "title": {
                    "type": "string",
                    "description": "Title of the documentation"
                },
                "type": {
                    "type": "string",
                    "description": "Type of documentation (manual, bulletin, directive, catalog)",
                    "enum": ["manual", "bulletin", "directive", "catalog"]
                },
                "version": {
                    "type": "string",
                    "description": "Version of the documentation"
                },
                "last_updated": {
                    "type": "string",
                    "description": "Date when the documentation was last updated",
                    "format": "date"
                },
                "content": {
                    "type": "string",
                    "description": "Main content of the documentation"
                },
                "sections": {
                    "type": "array",
                    "description": "Sections of the documentation",
                    "items": {
                        "type": "object",
                        "required": ["id", "title", "content"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique identifier for the section"
                            },
                            "title": {
                                "type": "string",
                                "description": "Title of the section"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content of the section"
                            }
                        }
                    }
                }
            }
        }

        # Write schema to file
        self._write_json_file(schemas_dir / "documentation.json", documentation_schema)

        # Generate documentation list schema
        documentation_list_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Documentation List",
            "description": "Schema for list of technical documentation",
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "type", "version", "last_updated"],
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique identifier for the documentation"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the documentation"
                    },
                    "type": {
                        "type": "string",
                        "description": "Type of documentation (manual, bulletin, directive, catalog)",
                        "enum": ["manual", "bulletin", "directive", "catalog"]
                    },
                    "version": {
                        "type": "string",
                        "description": "Version of the documentation"
                    },
                    "last_updated": {
                        "type": "string",
                        "description": "Date when the documentation was last updated",
                        "format": "date"
                    }
                }
            }
        }

        # Write schema to file
        self._write_json_file(schemas_dir / "documentation_list.json", documentation_list_schema)

        logger.info("Generated documentation schemas")

    def generate_troubleshooting_schemas(self):
        """Generate JSON schemas for troubleshooting data."""
        # Ensure schemas directory exists
        schemas_dir = self.config.paths.schemas_path / MockDataSource.TROUBLESHOOTING.value
        self._ensure_directory_exists(schemas_dir)

        # Generate systems schema
        systems_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Systems",
            "description": "Schema for aircraft systems",
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "description"],
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique identifier for the system"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the system"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the system"
                    }
                }
            }
        }

        # Write schema to file
        self._write_json_file(schemas_dir / "systems.json", systems_schema)

        # Generate troubleshooting schema
        troubleshooting_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Troubleshooting",
            "description": "Schema for troubleshooting data",
            "type": "object",
            "required": ["system_id", "system_name", "symptoms"],
            "properties": {
                "system_id": {
                    "type": "string",
                    "description": "Unique identifier for the system"
                },
                "system_name": {
                    "type": "string",
                    "description": "Name of the system"
                },
                "symptoms": {
                    "type": "array",
                    "description": "Symptoms for the system",
                    "items": {
                        "type": "object",
                        "required": ["id", "description", "severity"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique identifier for the symptom"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the symptom"
                            },
                            "severity": {
                                "type": "string",
                                "description": "Severity of the symptom",
                                "enum": ["low", "medium", "high"]
                            }
                        }
                    }
                }
            }
        }

        # Write schema to file
        self._write_json_file(schemas_dir / "troubleshooting.json", troubleshooting_schema)

        # Generate analysis schema
        analysis_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Analysis",
            "description": "Schema for troubleshooting analysis",
            "type": "object",
            "required": ["request", "analysis"],
            "properties": {
                "request": {
                    "type": "object",
                    "required": ["system", "symptoms"],
                    "properties": {
                        "system": {
                            "type": "string",
                            "description": "System identifier"
                        },
                        "symptoms": {
                            "type": "array",
                            "description": "List of symptoms",
                            "items": {
                                "type": "string"
                            }
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context"
                        }
                    }
                },
                "analysis": {
                    "type": "object",
                    "required": ["potential_causes", "recommended_solutions"],
                    "properties": {
                        "potential_causes": {
                            "type": "array",
                            "description": "Potential causes of the symptoms",
                            "items": {
                                "type": "object",
                                "required": ["id", "description", "probability"],
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "Unique identifier for the cause"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Description of the cause"
                                    },
                                    "probability": {
                                        "type": "number",
                                        "description": "Probability of the cause (0-1)",
                                        "minimum": 0,
                                        "maximum": 1
                                    },
                                    "evidence": {
                                        "type": "string",
                                        "description": "Evidence supporting the cause"
                                    }
                                }
                            }
                        },
                        "recommended_solutions": {
                            "type": "array",
                            "description": "Recommended solutions",
                            "items": {
                                "type": "object",
                                "required": ["id", "description", "difficulty", "estimated_time", "steps"],
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "Unique identifier for the solution"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Description of the solution"
                                    },
                                    "difficulty": {
                                        "type": "string",
                                        "description": "Difficulty of the solution",
                                        "enum": ["low", "medium", "high"]
                                    },
                                    "estimated_time": {
                                        "type": "string",
                                        "description": "Estimated time to implement the solution"
                                    },
                                    "steps": {
                                        "type": "array",
                                        "description": "Steps to implement the solution",
                                        "items": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        },
                        "additional_resources": {
                            "type": "array",
                            "description": "Additional resources",
                            "items": {
                                "type": "object",
                                "required": ["id", "type", "title", "reference"],
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "Unique identifier for the resource"
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "Type of resource"
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "Title of the resource"
                                    },
                                    "reference": {
                                        "type": "string",
                                        "description": "Reference to the resource"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Write schema to file
        self._write_json_file(schemas_dir / "analysis.json", analysis_schema)

        logger.info("Generated troubleshooting schemas")

    def generate_maintenance_schemas(self):
        """Generate JSON schemas for maintenance procedure data."""
        # Ensure schemas directory exists
        schemas_dir = self.config.paths.schemas_path / MockDataSource.MAINTENANCE.value
        self._ensure_directory_exists(schemas_dir)

        # Generate aircraft types schema
        aircraft_types_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Aircraft Types",
            "description": "Schema for aircraft types",
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "variants"],
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique identifier for the aircraft type"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the aircraft type"
                    },
                    "variants": {
                        "type": "array",
                        "description": "Variants of the aircraft type",
                        "items": {
                            "type": "string"
                        }
                    }
                }
            }
        }

        # Write schema to file
        self._write_json_file(schemas_dir / "aircraft_types.json", aircraft_types_schema)

        # Generate maintenance procedure schema
        maintenance_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Maintenance Procedure",
            "description": "Schema for maintenance procedure",
            "type": "object",
            "required": ["id", "title", "description", "estimated_time", "skill_level", "safety_precautions", "tools_required", "parts_required", "steps", "references"],
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique identifier for the procedure"
                },
                "title": {
                    "type": "string",
                    "description": "Title of the procedure"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the procedure"
                },
                "estimated_time": {
                    "type": "string",
                    "description": "Estimated time to complete the procedure"
                },
                "skill_level": {
                    "type": "string",
                    "description": "Required skill level for the procedure"
                },
                "safety_precautions": {
                    "type": "array",
                    "description": "Safety precautions for the procedure",
                    "items": {
                        "type": "string"
                    }
                },
                "tools_required": {
                    "type": "array",
                    "description": "Tools required for the procedure",
                    "items": {
                        "type": "object",
                        "required": ["id", "name", "specification"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique identifier for the tool"
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the tool"
                            },
                            "specification": {
                                "type": "string",
                                "description": "Specification of the tool"
                            }
                        }
                    }
                },
                "parts_required": {
                    "type": "array",
                    "description": "Parts required for the procedure",
                    "items": {
                        "type": "object",
                        "required": ["id", "name", "part_number", "quantity"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique identifier for the part"
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the part"
                            },
                            "part_number": {
                                "type": "string",
                                "description": "Part number"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Quantity of the part required"
                            }
                        }
                    }
                },
                "steps": {
                    "type": "array",
                    "description": "Steps of the procedure",
                    "items": {
                        "type": "object",
                        "required": ["step_number", "title", "description", "cautions"],
                        "properties": {
                            "step_number": {
                                "type": "integer",
                                "description": "Step number"
                            },
                            "title": {
                                "type": "string",
                                "description": "Title of the step"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the step"
                            },
                            "cautions": {
                                "type": "array",
                                "description": "Cautions for the step",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "images": {
                                "type": "array",
                                "description": "Images for the step",
                                "items": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                },
                "references": {
                    "type": "array",
                    "description": "References for the procedure",
                    "items": {
                        "type": "object",
                        "required": ["id", "type", "title"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique identifier for the reference"
                            },
                            "type": {
                                "type": "string",
                                "description": "Type of reference"
                            },
                            "title": {
                                "type": "string",
                                "description": "Title of the reference"
                            },
                            "section": {
                                "type": "string",
                                "description": "Section of the reference"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date of the reference",
                                "format": "date"
                            }
                        }
                    }
                }
            }
        }

        # Write schema to file
        self._write_json_file(schemas_dir / "maintenance.json", maintenance_schema)

        logger.info("Generated maintenance schemas")

    def generate_all_schemas(self):
        """Generate all JSON schemas for mock data."""
        self.generate_documentation_schemas()
        self.generate_troubleshooting_schemas()
        self.generate_maintenance_schemas()

        logger.info("Generated all schemas")

    def generate_documentation_data(self):
        """Generate mock data for documentation."""
        # Ensure documentation directory exists
        doc_dir = self.config.paths.documentation_path
        self._ensure_directory_exists(doc_dir)

        # Generate documentation list
        documentation_list = [
            {
                "id": "doc-001",
                "title": "Aircraft Maintenance Manual",
                "type": "manual",
                "version": "1.0",
                "last_updated": "2025-01-15",
            },
            {
                "id": "doc-002",
                "title": "Component Maintenance Manual",
                "type": "manual",
                "version": "2.1",
                "last_updated": "2025-02-20",
            },
            {
                "id": "doc-003",
                "title": "Illustrated Parts Catalog",
                "type": "catalog",
                "version": "1.5",
                "last_updated": "2025-03-10",
            },
            {
                "id": "doc-004",
                "title": "Service Bulletin SB-2025-01",
                "type": "bulletin",
                "version": "1.0",
                "last_updated": "2025-04-05",
            },
            {
                "id": "doc-005",
                "title": "Airworthiness Directive AD-2025-02",
                "type": "directive",
                "version": "1.0",
                "last_updated": "2025-04-10",
            },
        ]

        # Write documentation list to file
        self._write_json_file(doc_dir / "index.json", documentation_list)

        # Generate individual documentation files
        for doc in documentation_list:
            doc_id = doc["id"]
            doc_title = doc["title"]
            doc_type = doc["type"]

            # Create documentation content
            documentation = {
                "id": doc_id,
                "title": doc_title,
                "type": doc_type,
                "version": doc["version"],
                "last_updated": doc["last_updated"],
                "content": f"This is the main content for {doc_title}. It provides an overview of the document.",
                "sections": []
            }

            # Add sections based on document type
            if doc_type == "manual":
                documentation["sections"] = [
                    {
                        "id": f"{doc_id}-section-1",
                        "title": "Introduction",
                        "content": "This section provides an introduction to the manual and its purpose."
                    },
                    {
                        "id": f"{doc_id}-section-2",
                        "title": "Safety Precautions",
                        "content": "This section outlines important safety precautions that must be followed when performing maintenance."
                    },
                    {
                        "id": f"{doc_id}-section-3",
                        "title": "System Description",
                        "content": "This section provides a detailed description of the system, including components and operation."
                    },
                    {
                        "id": f"{doc_id}-section-4",
                        "title": "Maintenance Procedures",
                        "content": "This section contains step-by-step procedures for maintaining the system."
                    },
                    {
                        "id": f"{doc_id}-section-5",
                        "title": "Troubleshooting",
                        "content": "This section provides guidance for identifying and resolving common issues."
                    }
                ]
            elif doc_type == "catalog":
                documentation["sections"] = [
                    {
                        "id": f"{doc_id}-section-1",
                        "title": "Introduction",
                        "content": "This section provides an introduction to the parts catalog."
                    },
                    {
                        "id": f"{doc_id}-section-2",
                        "title": "How to Use This Catalog",
                        "content": "This section explains how to use the parts catalog effectively."
                    },
                    {
                        "id": f"{doc_id}-section-3",
                        "title": "Parts Listing",
                        "content": "This section contains a comprehensive listing of all parts."
                    },
                    {
                        "id": f"{doc_id}-section-4",
                        "title": "Diagrams and Illustrations",
                        "content": "This section contains diagrams and illustrations of parts and assemblies."
                    },
                    {
                        "id": f"{doc_id}-section-5",
                        "title": "Ordering Information",
                        "content": "This section provides information on how to order parts."
                    }
                ]
            elif doc_type == "bulletin":
                documentation["sections"] = [
                    {
                        "id": f"{doc_id}-section-1",
                        "title": "Purpose",
                        "content": "This section explains the purpose of the service bulletin."
                    },
                    {
                        "id": f"{doc_id}-section-2",
                        "title": "Affected Aircraft",
                        "content": "This section identifies the aircraft affected by the service bulletin."
                    },
                    {
                        "id": f"{doc_id}-section-3",
                        "title": "Description",
                        "content": "This section provides a detailed description of the issue addressed by the service bulletin."
                    },
                    {
                        "id": f"{doc_id}-section-4",
                        "title": "Corrective Action",
                        "content": "This section outlines the corrective action to be taken."
                    },
                    {
                        "id": f"{doc_id}-section-5",
                        "title": "Compliance",
                        "content": "This section specifies the compliance requirements and timeline."
                    }
                ]
            elif doc_type == "directive":
                documentation["sections"] = [
                    {
                        "id": f"{doc_id}-section-1",
                        "title": "Summary",
                        "content": "This section provides a summary of the airworthiness directive."
                    },
                    {
                        "id": f"{doc_id}-section-2",
                        "title": "Affected Products",
                        "content": "This section identifies the products affected by the airworthiness directive."
                    },
                    {
                        "id": f"{doc_id}-section-3",
                        "title": "Unsafe Condition",
                        "content": "This section describes the unsafe condition that prompted the airworthiness directive."
                    },
                    {
                        "id": f"{doc_id}-section-4",
                        "title": "Required Actions",
                        "content": "This section specifies the actions required to address the unsafe condition."
                    },
                    {
                        "id": f"{doc_id}-section-5",
                        "title": "Compliance Timeline",
                        "content": "This section outlines the timeline for compliance with the airworthiness directive."
                    }
                ]

            # Write documentation to file
            self._write_json_file(doc_dir / f"{doc_id}.json", documentation)

        logger.info("Generated documentation data")

    def generate_troubleshooting_data(self):
        """Generate mock data for troubleshooting."""
        # Ensure troubleshooting directory exists
        ts_dir = self.config.paths.troubleshooting_path
        self._ensure_directory_exists(ts_dir)

        # Generate systems list
        systems = [
            {
                "id": "sys-001",
                "name": "Hydraulic System",
                "description": "Aircraft hydraulic system components and functions",
            },
            {
                "id": "sys-002",
                "name": "Electrical System",
                "description": "Aircraft electrical system components and functions",
            },
            {
                "id": "sys-003",
                "name": "Avionics System",
                "description": "Aircraft avionics system components and functions",
            },
            {
                "id": "sys-004",
                "name": "Landing Gear System",
                "description": "Aircraft landing gear system components and functions",
            },
            {
                "id": "sys-005",
                "name": "Fuel System",
                "description": "Aircraft fuel system components and functions",
            },
        ]

        # Write systems list to file
        self._write_json_file(ts_dir / "systems.json", systems)

        # Generate troubleshooting data for each system
        for system in systems:
            system_id = system["id"]
            system_name = system["name"]

            # Create symptoms based on system
            symptoms = []

            if system_id == "sys-001":  # Hydraulic System
                symptoms = [
                    {
                        "id": "sym-001",
                        "description": "Pressure fluctuation",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-002",
                        "description": "Fluid leakage",
                        "severity": "high",
                    },
                    {
                        "id": "sym-003",
                        "description": "Slow actuator response",
                        "severity": "low",
                    },
                    {
                        "id": "sym-004",
                        "description": "Unusual noise from hydraulic pump",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-005",
                        "description": "Overheating of hydraulic fluid",
                        "severity": "high",
                    },
                ]
            elif system_id == "sys-002":  # Electrical System
                symptoms = [
                    {
                        "id": "sym-006",
                        "description": "Circuit breaker tripping",
                        "severity": "high",
                    },
                    {
                        "id": "sym-007",
                        "description": "Intermittent power loss",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-008",
                        "description": "Unusual noise from electrical components",
                        "severity": "low",
                    },
                    {
                        "id": "sym-009",
                        "description": "Dimming lights",
                        "severity": "low",
                    },
                    {
                        "id": "sym-010",
                        "description": "Burning smell from electrical panel",
                        "severity": "high",
                    },
                ]
            elif system_id == "sys-003":  # Avionics System
                symptoms = [
                    {
                        "id": "sym-011",
                        "description": "Display flickering",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-012",
                        "description": "Navigation system errors",
                        "severity": "high",
                    },
                    {
                        "id": "sym-013",
                        "description": "Communication system static",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-014",
                        "description": "Incorrect sensor readings",
                        "severity": "high",
                    },
                    {
                        "id": "sym-015",
                        "description": "System reboot during operation",
                        "severity": "high",
                    },
                ]
            elif system_id == "sys-004":  # Landing Gear System
                symptoms = [
                    {
                        "id": "sym-016",
                        "description": "Gear extension/retraction delay",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-017",
                        "description": "Unusual noise during operation",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-018",
                        "description": "Gear position indicator discrepancy",
                        "severity": "high",
                    },
                    {
                        "id": "sym-019",
                        "description": "Gear door not fully closed",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-020",
                        "description": "Gear locking mechanism failure",
                        "severity": "high",
                    },
                ]
            elif system_id == "sys-005":  # Fuel System
                symptoms = [
                    {
                        "id": "sym-021",
                        "description": "Fuel gauge reading discrepancy",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-022",
                        "description": "Fuel leak",
                        "severity": "high",
                    },
                    {
                        "id": "sym-023",
                        "description": "Uneven fuel consumption between tanks",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-024",
                        "description": "Fuel pump pressure fluctuation",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-025",
                        "description": "Water contamination in fuel",
                        "severity": "high",
                    },
                ]

            # Create troubleshooting data
            troubleshooting_data = {
                "system_id": system_id,
                "system_name": system_name,
                "symptoms": symptoms
            }

            # Write troubleshooting data to file
            self._write_json_file(ts_dir / f"{system_id}.json", troubleshooting_data)

            # Create analysis data for each system
            analysis_data = {
                "request": {
                    "system": system_id,
                    "symptoms": [symptom["id"] for symptom in symptoms[:2]],
                    "context": "Routine maintenance inspection"
                },
                "analysis": {
                    "potential_causes": [
                        {
                            "id": f"cause-{system_id}-001",
                            "description": "Component wear and tear",
                            "probability": 0.75,
                            "evidence": "Based on the symptoms provided, this is likely caused by normal wear and tear of components."
                        },
                        {
                            "id": f"cause-{system_id}-002",
                            "description": "Improper maintenance",
                            "probability": 0.45,
                            "evidence": "The symptoms may also indicate improper maintenance procedures during the last service."
                        },
                        {
                            "id": f"cause-{system_id}-003",
                            "description": "Manufacturing defect",
                            "probability": 0.25,
                            "evidence": "In rare cases, these symptoms could be caused by a manufacturing defect in the components."
                        }
                    ],
                    "recommended_solutions": [
                        {
                            "id": f"sol-{system_id}-001",
                            "description": "Replace component",
                            "difficulty": "medium",
                            "estimated_time": "2 hours",
                            "steps": [
                                "Step 1: Prepare necessary tools and replacement parts",
                                "Step 2: Remove access panels",
                                "Step 3: Disconnect electrical connections",
                                "Step 4: Remove faulty component",
                                "Step 5: Install new component",
                                "Step 6: Reconnect electrical connections",
                                "Step 7: Perform functional test"
                            ]
                        },
                        {
                            "id": f"sol-{system_id}-002",
                            "description": "Perform maintenance procedure",
                            "difficulty": "low",
                            "estimated_time": "1 hour",
                            "steps": [
                                "Step 1: Prepare necessary tools",
                                "Step 2: Inspect component for damage",
                                "Step 3: Clean component",
                                "Step 4: Adjust settings as needed",
                                "Step 5: Perform functional test"
                            ]
                        }
                    ],
                    "additional_resources": [
                        {
                            "id": f"res-{system_id}-001",
                            "type": "documentation",
                            "title": "Component Maintenance Manual",
                            "reference": "CMM-123-456"
                        },
                        {
                            "id": f"res-{system_id}-002",
                            "type": "video",
                            "title": "Troubleshooting Tutorial",
                            "reference": "VID-789-012"
                        }
                    ]
                }
            }

            # Write analysis data to file
            self._write_json_file(ts_dir / f"{system_id}-analysis.json", analysis_data)

        logger.info("Generated troubleshooting data")

    def generate_maintenance_data(self):
        """Generate mock data for maintenance procedures."""
        # Ensure maintenance directory exists
        maint_dir = self.config.paths.maintenance_path
        self._ensure_directory_exists(maint_dir)

        # Generate aircraft types list
        aircraft_types = [
            {
                "id": "ac-001",
                "name": "Boeing 737",
                "variants": ["737-700", "737-800", "737-900"],
            },
            {
                "id": "ac-002",
                "name": "Airbus A320",
                "variants": ["A320-200", "A320neo"],
            },
            {
                "id": "ac-003",
                "name": "Embraer E190",
                "variants": ["E190-E2"],
            },
            {
                "id": "ac-004",
                "name": "Bombardier CRJ",
                "variants": ["CRJ-700", "CRJ-900"],
            },
            {
                "id": "ac-005",
                "name": "ATR 72",
                "variants": ["ATR 72-500", "ATR 72-600"],
            },
        ]

        # Write aircraft types list to file
        self._write_json_file(maint_dir / "aircraft_types.json", aircraft_types)

        # Define systems for each aircraft type
        systems = [
            {
                "id": "sys-001",
                "name": "Hydraulic System",
                "description": "Aircraft hydraulic system components and functions",
            },
            {
                "id": "sys-002",
                "name": "Electrical System",
                "description": "Aircraft electrical system components and functions",
            },
            {
                "id": "sys-003",
                "name": "Avionics System",
                "description": "Aircraft avionics system components and functions",
            },
            {
                "id": "sys-004",
                "name": "Landing Gear System",
                "description": "Aircraft landing gear system components and functions",
            },
            {
                "id": "sys-005",
                "name": "Fuel System",
                "description": "Aircraft fuel system components and functions",
            },
        ]

        # Define procedure types
        procedure_types = [
            {
                "id": "proc-001",
                "name": "Inspection",
                "description": "Visual inspection of components",
                "interval": "Daily",
            },
            {
                "id": "proc-002",
                "name": "Functional Test",
                "description": "Testing system functionality",
                "interval": "Weekly",
            },
            {
                "id": "proc-003",
                "name": "Replacement",
                "description": "Component replacement procedure",
                "interval": "As needed",
            },
            {
                "id": "proc-004",
                "name": "Adjustment",
                "description": "Adjusting system parameters",
                "interval": "Monthly",
            },
            {
                "id": "proc-005",
                "name": "Overhaul",
                "description": "Complete system overhaul",
                "interval": "Yearly",
            },
        ]

        # Generate maintenance data for each aircraft type and system
        for aircraft in aircraft_types:
            aircraft_id = aircraft["id"]
            aircraft_name = aircraft["name"]

            # Create aircraft directory
            aircraft_dir = maint_dir / aircraft_id
            self._ensure_directory_exists(aircraft_dir)

            # Write systems for this aircraft
            self._write_json_file(aircraft_dir / "systems.json", systems)

            for system in systems:
                system_id = system["id"]
                system_name = system["name"]

                # Create system directory
                system_dir = aircraft_dir / system_id
                self._ensure_directory_exists(system_dir)

                # Write procedure types for this system
                self._write_json_file(system_dir / "procedure_types.json", procedure_types)

                for procedure in procedure_types:
                    procedure_id = procedure["id"]
                    procedure_name = procedure["name"]

                    # Create maintenance procedure
                    maintenance_procedure = {
                        "id": f"maint-{aircraft_id}-{system_id}-{procedure_id}",
                        "title": f"{procedure_name} Procedure for {system_name} on {aircraft_name}",
                        "description": f"This procedure provides instructions for performing {procedure_name.lower()} on the {system_name.lower()} of {aircraft_name} aircraft.",
                        "estimated_time": "2 hours" if procedure_id in ["proc-003", "proc-005"] else "1 hour",
                        "skill_level": "Technician Level 3" if procedure_id == "proc-005" else "Technician Level 2",
                        "safety_precautions": [
                            "Ensure aircraft is properly grounded",
                            "Wear appropriate personal protective equipment",
                            "Follow all safety protocols in the maintenance manual",
                            "Ensure all power is disconnected before working on electrical components" if system_id == "sys-002" else "Use proper lifting techniques when handling heavy components",
                        ],
                        "tools_required": [
                            {
                                "id": "tool-001",
                                "name": "Socket Set",
                                "specification": "Standard, 10-19mm",
                            },
                            {
                                "id": "tool-002",
                                "name": "Torque Wrench",
                                "specification": "Calibrated, 5-50 Nm",
                            },
                            {
                                "id": "tool-003",
                                "name": "Multimeter" if system_id == "sys-002" else "Pressure Gauge" if system_id == "sys-001" else "Inspection Mirror",
                                "specification": "Digital, CAT III 600V" if system_id == "sys-002" else "0-3000 PSI" if system_id == "sys-001" else "Telescoping",
                            },
                        ],
                        "parts_required": [
                            {
                                "id": "part-001",
                                "name": "O-ring" if system_id in ["sys-001", "sys-005"] else "Connector" if system_id == "sys-002" else "Sensor",
                                "part_number": f"OR-{aircraft_id}-{system_id}" if system_id in ["sys-001", "sys-005"] else f"CN-{aircraft_id}-{system_id}" if system_id == "sys-002" else f"SN-{aircraft_id}-{system_id}",
                                "quantity": 2 if procedure_id in ["proc-003", "proc-005"] else 1,
                            },
                            {
                                "id": "part-002",
                                "name": "Hydraulic Fluid" if system_id == "sys-001" else "Electrical Tape" if system_id == "sys-002" else "Lubricant",
                                "part_number": f"HF-{aircraft_id}" if system_id == "sys-001" else f"ET-{aircraft_id}" if system_id == "sys-002" else f"LB-{aircraft_id}",
                                "quantity": 1,
                            },
                        ] if procedure_id in ["proc-003", "proc-004", "proc-005"] else [],
                        "steps": [
                            {
                                "step_number": 1,
                                "title": "Preparation",
                                "description": "Gather all necessary tools and parts. Ensure aircraft is in a safe state for maintenance.",
                                "cautions": ["Verify aircraft power is off" if system_id == "sys-002" else "Verify system pressure is relieved" if system_id == "sys-001" else "Verify aircraft is properly secured"],
                                "images": [],
                            },
                            {
                                "step_number": 2,
                                "title": "Access Panel Removal",
                                "description": "Remove access panel to gain access to the system components.",
                                "cautions": ["Support panel during removal"],
                                "images": [],
                            },
                            {
                                "step_number": 3,
                                "title": "Component Inspection" if procedure_id == "proc-001" else "Component Testing" if procedure_id == "proc-002" else "Component Removal" if procedure_id == "proc-003" else "Component Adjustment" if procedure_id == "proc-004" else "Component Disassembly",
                                "description": "Inspect components for damage, wear, or leakage." if procedure_id == "proc-001" else "Test component functionality using appropriate equipment." if procedure_id == "proc-002" else "Remove component from the system." if procedure_id == "proc-003" else "Adjust component settings as specified." if procedure_id == "proc-004" else "Disassemble component for overhaul.",
                                "cautions": ["Document any findings" if procedure_id == "proc-001" else "Follow test procedures exactly" if procedure_id == "proc-002" else "Use proper tools for removal" if procedure_id == "proc-003" else "Do not exceed specified adjustment limits" if procedure_id == "proc-004" else "Label all parts during disassembly"],
                                "images": [],
                            },
                            {
                                "step_number": 4,
                                "title": "Detailed Inspection" if procedure_id == "proc-001" else "System Verification" if procedure_id == "proc-002" else "New Component Installation" if procedure_id == "proc-003" else "Testing After Adjustment" if procedure_id == "proc-004" else "Component Cleaning",
                                "description": "Perform detailed inspection of all subcomponents." if procedure_id == "proc-001" else "Verify system operation after testing." if procedure_id == "proc-002" else "Install new component into the system." if procedure_id == "proc-003" else "Test the system after making adjustments." if procedure_id == "proc-004" else "Clean all component parts thoroughly.",
                                "cautions": ["Use proper inspection techniques" if procedure_id == "proc-001" else "Record all test results" if procedure_id == "proc-002" else "Ensure proper alignment during installation" if procedure_id == "proc-003" else "Verify adjustments are within specifications" if procedure_id == "proc-004" else "Use only approved cleaning agents"],
                                "images": [],
                            },
                            {
                                "step_number": 5,
                                "title": "Reassembly",
                                "description": "Reinstall access panel and secure all fasteners.",
                                "cautions": ["Torque fasteners to specified values"],
                                "images": [],
                            },
                            {
                                "step_number": 6,
                                "title": "Documentation",
                                "description": "Complete maintenance records and documentation.",
                                "cautions": ["Ensure all work is properly documented"],
                                "images": [],
                            },
                        ],
                        "references": [
                            {
                                "id": "ref-001",
                                "type": "manual",
                                "title": "Aircraft Maintenance Manual",
                                "section": f"Chapter {29 if system_id == 'sys-001' else 24 if system_id == 'sys-002' else 34 if system_id == 'sys-003' else 32 if system_id == 'sys-004' else 28} - {system_name}",
                            },
                            {
                                "id": "ref-002",
                                "type": "service_bulletin" if random.random() > 0.5 else "technical_order",
                                "title": f"Service Bulletin SB-{aircraft_id}-{system_id}" if random.random() > 0.5 else f"Technical Order TO-{aircraft_id}-{system_id}",
                                "date": "2025-01-15",
                            },
                        ],
                    }

                    # Write maintenance procedure to file
                    self._write_json_file(system_dir / f"{procedure_id}.json", maintenance_procedure)

        logger.info("Generated maintenance data")

    def generate_all_data(self):
        """Generate all mock data."""
        # Generate schemas first
        self.generate_all_schemas()

        # Generate data
        self.generate_documentation_data()
        self.generate_troubleshooting_data()
        self.generate_maintenance_data()

        logger.info("Generated all mock data")
