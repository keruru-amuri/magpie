"""
Tools and Parts Service for the MAGPIE platform.

This module provides functionality for managing and querying tools, parts, and equipment
for aircraft maintenance procedures.
"""
import json
import logging
import os
import re
from typing import Dict, List, Optional, Any, Set, Tuple

logger = logging.getLogger(__name__)


class ToolsAndPartsService:
    """
    Service for managing tools, parts, and equipment.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the tools and parts service.

        Args:
            data_dir: Directory containing tools, parts, and equipment data files.
                If None, uses default directory.
        """
        if data_dir is None:
            # Default to the mock data folder
            self.data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "mock", "maintenance"
            )
        else:
            self.data_dir = data_dir

        self.tools: Dict[str, Dict] = {}
        self.parts: Dict[str, Dict] = {}
        self.equipment: Dict[str, Dict] = {}
        self.aircraft_tool_mappings: Dict[str, Dict] = {}
        self.aircraft_part_mappings: Dict[str, Dict] = {}
        self.procedure_resource_mappings: Dict[str, Dict] = {}

        self._load_data()

    def _load_data(self) -> None:
        """
        Load tools, parts, and equipment data from files.
        """
        try:
            # Load tools
            tools_file = os.path.join(self.data_dir, "tools", "common_tools.json")
            if os.path.exists(tools_file):
                with open(tools_file, "r") as f:
                    tools = json.load(f)
                    for tool in tools:
                        self.tools[tool["id"]] = tool

            # Load parts
            parts_file = os.path.join(self.data_dir, "parts", "common_parts.json")
            if os.path.exists(parts_file):
                with open(parts_file, "r") as f:
                    parts = json.load(f)
                    for part in parts:
                        self.parts[part["id"]] = part

            # Load equipment
            equipment_file = os.path.join(self.data_dir, "equipment", "common_equipment.json")
            if os.path.exists(equipment_file):
                with open(equipment_file, "r") as f:
                    equipment = json.load(f)
                    for item in equipment:
                        self.equipment[item["id"]] = item

            # Load aircraft tool mappings
            mappings_file = os.path.join(self.data_dir, "tools", "aircraft_tool_mappings.json")
            if os.path.exists(mappings_file):
                with open(mappings_file, "r") as f:
                    self.aircraft_tool_mappings = json.load(f)

            # Load aircraft part mappings
            mappings_file = os.path.join(self.data_dir, "parts", "aircraft_part_mappings.json")
            if os.path.exists(mappings_file):
                with open(mappings_file, "r") as f:
                    self.aircraft_part_mappings = json.load(f)

            # Load procedure resource mappings
            mappings_file = os.path.join(self.data_dir, "procedure_resource_mappings.json")
            if os.path.exists(mappings_file):
                with open(mappings_file, "r") as f:
                    self.procedure_resource_mappings = json.load(f)

            logger.info(f"Loaded {len(self.tools)} tools, {len(self.parts)} parts, and {len(self.equipment)} equipment items")
        except Exception as e:
            logger.error(f"Error loading tools and parts data: {str(e)}")

    def get_all_tools(self) -> List[Dict]:
        """
        Get all tools.

        Returns:
            List of all tools.
        """
        return list(self.tools.values())

    def get_all_parts(self) -> List[Dict]:
        """
        Get all parts.

        Returns:
            List of all parts.
        """
        return list(self.parts.values())

    def get_all_equipment(self) -> List[Dict]:
        """
        Get all equipment.

        Returns:
            List of all equipment.
        """
        return list(self.equipment.values())

    def get_tool(self, tool_id: str) -> Optional[Dict]:
        """
        Get a specific tool by ID.

        Args:
            tool_id: The ID of the tool to retrieve.

        Returns:
            The tool dictionary or None if not found.
        """
        return self.tools.get(tool_id)

    def get_part(self, part_id: str) -> Optional[Dict]:
        """
        Get a specific part by ID.

        Args:
            part_id: The ID of the part to retrieve.

        Returns:
            The part dictionary or None if not found.
        """
        return self.parts.get(part_id)

    def get_equipment(self, equipment_id: str) -> Optional[Dict]:
        """
        Get a specific equipment item by ID.

        Args:
            equipment_id: The ID of the equipment to retrieve.

        Returns:
            The equipment dictionary or None if not found.
        """
        return self.equipment.get(equipment_id)

    def get_tools_by_category(self, category: str) -> List[Dict]:
        """
        Get tools by category.

        Args:
            category: The category of tools to retrieve.

        Returns:
            List of matching tools.
        """
        return [
            tool for tool in self.tools.values()
            if tool.get("category", "").lower() == category.lower()
        ]

    def get_parts_by_category(self, category: str) -> List[Dict]:
        """
        Get parts by category.

        Args:
            category: The category of parts to retrieve.

        Returns:
            List of matching parts.
        """
        return [
            part for part in self.parts.values()
            if part.get("category", "").lower() == category.lower()
        ]

    def get_equipment_by_category(self, category: str) -> List[Dict]:
        """
        Get equipment by category.

        Args:
            category: The category of equipment to retrieve.

        Returns:
            List of matching equipment.
        """
        return [
            item for item in self.equipment.values()
            if item.get("category", "").lower() == category.lower()
        ]

    def get_tools_for_aircraft_system(
        self,
        aircraft_type: str,
        system: str
    ) -> List[Dict]:
        """
        Get tools for a specific aircraft system.

        Args:
            aircraft_type: The type of aircraft (e.g., "Boeing 737").
            system: The aircraft system (e.g., "hydraulic").

        Returns:
            List of tools for the specified aircraft system.
        """
        tool_ids = []

        # Normalize inputs
        aircraft_type = aircraft_type.strip()
        system = system.lower().strip()

        # Check if we have mappings for this aircraft type
        if aircraft_type in self.aircraft_tool_mappings:
            # Check if we have mappings for this system
            if system in self.aircraft_tool_mappings[aircraft_type]:
                tool_ids.extend(self.aircraft_tool_mappings[aircraft_type][system])

            # Also include specialized tools if available
            if "specialized" in self.aircraft_tool_mappings[aircraft_type]:
                for specialized_tool in self.aircraft_tool_mappings[aircraft_type]["specialized"]:
                    if isinstance(specialized_tool, dict) and "id" in specialized_tool:
                        tool_ids.append(specialized_tool["id"])

        # Get the actual tools
        tools = []
        for tool_id in tool_ids:
            if tool_id in self.tools:
                tools.append(self.tools[tool_id])
            elif tool_id.startswith("spec-"):
                # This is a specialized tool that's not in the common tools list
                # Create a tool object from the specialized tool info
                for aircraft in self.aircraft_tool_mappings:
                    if "specialized" in self.aircraft_tool_mappings[aircraft]:
                        for spec_tool in self.aircraft_tool_mappings[aircraft]["specialized"]:
                            if isinstance(spec_tool, dict) and spec_tool.get("id") == tool_id:
                                tools.append({
                                    "id": spec_tool["id"],
                                    "name": spec_tool["name"],
                                    "category": "Specialized Tool",
                                    "description": spec_tool["description"],
                                    "aircraft_compatibility": [aircraft],
                                    "system_compatibility": [system]
                                })
                                break

        return tools

    def get_parts_for_aircraft_system(
        self,
        aircraft_type: str,
        system: str
    ) -> List[Dict]:
        """
        Get parts for a specific aircraft system.

        Args:
            aircraft_type: The type of aircraft (e.g., "Boeing 737").
            system: The aircraft system (e.g., "hydraulic").

        Returns:
            List of parts for the specified aircraft system.
        """
        part_ids = []

        # Normalize inputs
        aircraft_type = aircraft_type.strip()
        system = system.lower().strip()

        # Check if we have mappings for this aircraft type
        if aircraft_type in self.aircraft_part_mappings:
            # Check if we have mappings for this system
            if system in self.aircraft_part_mappings[aircraft_type]:
                part_ids.extend(self.aircraft_part_mappings[aircraft_type][system])

            # Also include specialized parts if available
            if "specialized" in self.aircraft_part_mappings[aircraft_type]:
                for specialized_part in self.aircraft_part_mappings[aircraft_type]["specialized"]:
                    if isinstance(specialized_part, dict) and "id" in specialized_part:
                        part_ids.append(specialized_part["id"])

        # Get the actual parts
        parts = []
        for part_id in part_ids:
            if part_id in self.parts:
                parts.append(self.parts[part_id])
            elif part_id.startswith("spec-part-"):
                # This is a specialized part that's not in the common parts list
                # Create a part object from the specialized part info
                for aircraft in self.aircraft_part_mappings:
                    if "specialized" in self.aircraft_part_mappings[aircraft]:
                        for spec_part in self.aircraft_part_mappings[aircraft]["specialized"]:
                            if isinstance(spec_part, dict) and spec_part.get("id") == part_id:
                                parts.append({
                                    "id": spec_part["id"],
                                    "name": spec_part["name"],
                                    "category": "Specialized Part",
                                    "part_number": spec_part["part_number"],
                                    "description": spec_part["description"],
                                    "aircraft_compatibility": [aircraft],
                                    "system_compatibility": [system]
                                })
                                break

        return parts

    def get_resources_for_procedure(
        self,
        procedure_type: str,
        system: str,
        aircraft_type: Optional[str] = None,
        specific_procedure: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get resources (tools, parts, equipment) for a specific maintenance procedure.

        Args:
            procedure_type: Type of procedure (e.g., "inspection", "repair").
            system: System being maintained (e.g., "fuel_system", "avionics").
            aircraft_type: Aircraft type (optional).
            specific_procedure: Specific procedure name (optional).

        Returns:
            Dictionary with tools, parts, and equipment for the procedure.
        """
        # Normalize inputs
        procedure_type = procedure_type.lower().strip()
        system = system.lower().strip().replace(" ", "_")

        # Initialize result
        result = {
            "tools": [],
            "parts": [],
            "equipment": []
        }

        # Get resource IDs from procedure mappings
        tool_ids = []
        part_ids = []
        equipment_ids = []

        # Check for specific procedure first
        if specific_procedure and "specific_procedures" in self.procedure_resource_mappings:
            specific_procedure = specific_procedure.lower().strip().replace(" ", "_")
            if specific_procedure in self.procedure_resource_mappings["specific_procedures"]:
                mapping = self.procedure_resource_mappings["specific_procedures"][specific_procedure]
                tool_ids.extend(mapping.get("tools", []))
                part_ids.extend(mapping.get("parts", []))
                equipment_ids.extend(mapping.get("equipment", []))

        # Then check for general procedure type and system
        if procedure_type in self.procedure_resource_mappings:
            if system in self.procedure_resource_mappings[procedure_type]:
                mapping = self.procedure_resource_mappings[procedure_type][system]
                tool_ids.extend(mapping.get("tools", []))
                part_ids.extend(mapping.get("parts", []))
                equipment_ids.extend(mapping.get("equipment", []))

            # Also include general resources for this procedure type
            if "general" in self.procedure_resource_mappings[procedure_type]:
                mapping = self.procedure_resource_mappings[procedure_type]["general"]
                tool_ids.extend(mapping.get("tools", []))
                part_ids.extend(mapping.get("parts", []))
                equipment_ids.extend(mapping.get("equipment", []))

        # If aircraft type is provided, also get aircraft-specific resources
        if aircraft_type:
            aircraft_type = aircraft_type.strip()

            # Get aircraft-specific tools
            if aircraft_type in self.aircraft_tool_mappings:
                if system in self.aircraft_tool_mappings[aircraft_type]:
                    tool_ids.extend(self.aircraft_tool_mappings[aircraft_type][system])

                # Check for specialized tools for this procedure
                if "specialized" in self.aircraft_tool_mappings[aircraft_type]:
                    for spec_tool in self.aircraft_tool_mappings[aircraft_type]["specialized"]:
                        if isinstance(spec_tool, dict) and "procedures" in spec_tool:
                            # Check if this tool is used for the specific procedure
                            if specific_procedure and specific_procedure in spec_tool["procedures"]:
                                tool_ids.append(spec_tool["id"])
                            # Or check if this tool is used for procedures of this type
                            elif any(proc.startswith(f"{procedure_type}_") for proc in spec_tool["procedures"]):
                                tool_ids.append(spec_tool["id"])

            # Get aircraft-specific parts
            if aircraft_type in self.aircraft_part_mappings:
                if system in self.aircraft_part_mappings[aircraft_type]:
                    part_ids.extend(self.aircraft_part_mappings[aircraft_type][system])

                # Check for specialized parts for this procedure
                if "specialized" in self.aircraft_part_mappings[aircraft_type]:
                    for spec_part in self.aircraft_part_mappings[aircraft_type]["specialized"]:
                        if isinstance(spec_part, dict) and "procedures" in spec_part:
                            # Check if this part is used for the specific procedure
                            if specific_procedure and specific_procedure in spec_part["procedures"]:
                                part_ids.append(spec_part["id"])
                            # Or check if this part is used for procedures of this type
                            elif any(proc.startswith(f"{procedure_type}_") for proc in spec_part["procedures"]):
                                part_ids.append(spec_part["id"])

        # Remove duplicates
        tool_ids = list(set(tool_ids))
        part_ids = list(set(part_ids))
        equipment_ids = list(set(equipment_ids))

        # Get the actual resources
        for tool_id in tool_ids:
            if tool_id in self.tools:
                result["tools"].append(self.tools[tool_id])
            elif tool_id.startswith("spec-"):
                # This is a specialized tool
                for aircraft in self.aircraft_tool_mappings:
                    if "specialized" in self.aircraft_tool_mappings[aircraft]:
                        for spec_tool in self.aircraft_tool_mappings[aircraft]["specialized"]:
                            if isinstance(spec_tool, dict) and spec_tool.get("id") == tool_id:
                                result["tools"].append({
                                    "id": spec_tool["id"],
                                    "name": spec_tool["name"],
                                    "category": "Specialized Tool",
                                    "description": spec_tool["description"],
                                    "aircraft_compatibility": [aircraft],
                                    "system_compatibility": [system]
                                })
                                break

        for part_id in part_ids:
            if part_id in self.parts:
                result["parts"].append(self.parts[part_id])
            elif part_id.startswith("spec-part-"):
                # This is a specialized part
                for aircraft in self.aircraft_part_mappings:
                    if "specialized" in self.aircraft_part_mappings[aircraft]:
                        for spec_part in self.aircraft_part_mappings[aircraft]["specialized"]:
                            if isinstance(spec_part, dict) and spec_part.get("id") == part_id:
                                result["parts"].append({
                                    "id": spec_part["id"],
                                    "name": spec_part["name"],
                                    "category": "Specialized Part",
                                    "part_number": spec_part["part_number"],
                                    "description": spec_part["description"],
                                    "aircraft_compatibility": [aircraft],
                                    "system_compatibility": [system]
                                })
                                break

        for equipment_id in equipment_ids:
            if equipment_id in self.equipment:
                result["equipment"].append(self.equipment[equipment_id])

        return result

    def extract_tools_from_text(self, text: str) -> List[Dict]:
        """
        Extract tool references from text.

        Args:
            text: Text to analyze.

        Returns:
            List of tools mentioned in the text.
        """
        mentioned_tools = []

        # Get all tools
        all_tools = self.get_all_tools()

        # Check for each tool name in the text
        for tool in all_tools:
            tool_name = tool["name"].lower()
            if tool_name in text.lower():
                mentioned_tools.append(tool)

            # Also check for category mentions (e.g., "torque wrench")
            if "category" in tool and tool["category"].lower() in text.lower():
                if tool not in mentioned_tools:
                    mentioned_tools.append(tool)

        return mentioned_tools

    def extract_parts_from_text(self, text: str) -> List[Dict]:
        """
        Extract part references from text.

        Args:
            text: Text to analyze.

        Returns:
            List of parts mentioned in the text.
        """
        mentioned_parts = []

        # Get all parts
        all_parts = self.get_all_parts()

        # Check for each part name in the text
        for part in all_parts:
            part_name = part["name"].lower()
            if part_name in text.lower():
                mentioned_parts.append(part)

            # Also check for part number mentions
            if "part_number" in part and part["part_number"].lower() in text.lower():
                if part not in mentioned_parts:
                    mentioned_parts.append(part)

            # Also check for category mentions (e.g., "hydraulic fluid")
            if "category" in part and part["category"].lower() in text.lower():
                if part not in mentioned_parts:
                    mentioned_parts.append(part)

        return mentioned_parts

    def extract_equipment_from_text(self, text: str) -> List[Dict]:
        """
        Extract equipment references from text.

        Args:
            text: Text to analyze.

        Returns:
            List of equipment mentioned in the text.
        """
        mentioned_equipment = []

        # Get all equipment
        all_equipment = self.get_all_equipment()

        # Check for each equipment name in the text
        for equipment in all_equipment:
            equipment_name = equipment["name"].lower()
            if equipment_name in text.lower():
                mentioned_equipment.append(equipment)

            # Also check for model number mentions
            if "model_number" in equipment and equipment["model_number"].lower() in text.lower():
                if equipment not in mentioned_equipment:
                    mentioned_equipment.append(equipment)

            # Also check for category mentions (e.g., "hydraulic mule")
            if "category" in equipment and equipment["category"].lower() in text.lower():
                if equipment not in mentioned_equipment:
                    mentioned_equipment.append(equipment)

        return mentioned_equipment

    def extract_resources_from_procedure(self, procedure: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Extract resources (tools, parts, equipment) from a procedure.

        Args:
            procedure: Procedure to analyze.

        Returns:
            Dictionary with tools, parts, and equipment mentioned in the procedure.
        """
        result = {
            "tools": [],
            "parts": [],
            "equipment": []
        }

        # Extract resources from procedure description
        if "description" in procedure:
            result["tools"].extend(self.extract_tools_from_text(procedure["description"]))
            result["parts"].extend(self.extract_parts_from_text(procedure["description"]))
            result["equipment"].extend(self.extract_equipment_from_text(procedure["description"]))

        # Extract resources from procedure steps
        steps_field = None
        if "procedure_steps" in procedure and isinstance(procedure["procedure_steps"], list):
            steps_field = "procedure_steps"
        elif "steps" in procedure and isinstance(procedure["steps"], list):
            steps_field = "steps"

        if steps_field:
            for step in procedure[steps_field]:
                if isinstance(step, dict):
                    # Extract from step title
                    if "title" in step:
                        result["tools"].extend(self.extract_tools_from_text(step["title"]))
                        result["parts"].extend(self.extract_parts_from_text(step["title"]))
                        result["equipment"].extend(self.extract_equipment_from_text(step["title"]))

                    # Extract from step description
                    if "description" in step:
                        result["tools"].extend(self.extract_tools_from_text(step["description"]))
                        result["parts"].extend(self.extract_parts_from_text(step["description"]))
                        result["equipment"].extend(self.extract_equipment_from_text(step["description"]))

        # Remove duplicates by ID
        unique_tools = {}
        for tool in result["tools"]:
            unique_tools[tool["id"]] = tool
        result["tools"] = list(unique_tools.values())

        unique_parts = {}
        for part in result["parts"]:
            unique_parts[part["id"]] = part
        result["parts"] = list(unique_parts.values())

        unique_equipment = {}
        for equip in result["equipment"]:
            unique_equipment[equip["id"]] = equip
        result["equipment"] = list(unique_equipment.values())

        return result

    def generate_consolidated_resource_list(
        self,
        procedure: Dict[str, Any],
        procedure_type: Optional[str] = None,
        system: Optional[str] = None,
        aircraft_type: Optional[str] = None,
        specific_procedure: Optional[str] = None,
        format: str = "json"
    ) -> Any:
        """
        Generate a consolidated list of resources for a procedure.

        Args:
            procedure: Procedure to analyze.
            procedure_type: Type of procedure (optional).
            system: System being maintained (optional).
            aircraft_type: Aircraft type (optional).
            specific_procedure: Specific procedure name (optional).
            format: Output format ("json" or "markdown").

        Returns:
            Consolidated resource list in the specified format.
        """
        # Extract resources from procedure text
        extracted_resources = self.extract_resources_from_procedure(procedure)

        # Get resources based on procedure type and system
        mapped_resources = {}
        if procedure_type and system:
            mapped_resources = self.get_resources_for_procedure(
                procedure_type=procedure_type,
                system=system,
                aircraft_type=aircraft_type,
                specific_procedure=specific_procedure
            )

        # Combine resources
        combined_resources = {
            "tools": extracted_resources["tools"] + [
                tool for tool in mapped_resources.get("tools", [])
                if tool not in extracted_resources["tools"]
            ],
            "parts": extracted_resources["parts"] + [
                part for part in mapped_resources.get("parts", [])
                if part not in extracted_resources["parts"]
            ],
            "equipment": extracted_resources["equipment"] + [
                equip for equip in mapped_resources.get("equipment", [])
                if equip not in extracted_resources["equipment"]
            ]
        }

        # Format the output
        if format.lower() == "markdown":
            return self._format_resources_as_markdown(combined_resources)
        else:
            return combined_resources

    def _format_resources_as_markdown(self, resources: Dict[str, List[Dict]]) -> str:
        """
        Format resources as Markdown.

        Args:
            resources: Dictionary with tools, parts, and equipment.

        Returns:
            Markdown-formatted resource list.
        """
        markdown = "# Required Resources\n\n"

        # Add tools
        markdown += "## Tools\n\n"
        if resources["tools"]:
            for tool in resources["tools"]:
                markdown += f"### {tool['name']}\n\n"
                markdown += f"- **Category:** {tool.get('category', 'N/A')}\n"
                markdown += f"- **Description:** {tool.get('description', 'N/A')}\n"

                # Add specifications if available
                if "specifications" in tool and isinstance(tool["specifications"], dict):
                    markdown += "- **Specifications:**\n"
                    for key, value in tool["specifications"].items():
                        if key != "additional_specs":
                            markdown += f"  - {key.replace('_', ' ').title()}: {value}\n"

                    # Add additional specifications if available
                    if "additional_specs" in tool["specifications"] and isinstance(tool["specifications"]["additional_specs"], dict):
                        for key, value in tool["specifications"]["additional_specs"].items():
                            markdown += f"  - {key.replace('_', ' ').title()}: {value}\n"

                markdown += "\n"
        else:
            markdown += "No specific tools required.\n\n"

        # Add parts
        markdown += "## Parts\n\n"
        if resources["parts"]:
            for part in resources["parts"]:
                markdown += f"### {part['name']}\n\n"
                markdown += f"- **Category:** {part.get('category', 'N/A')}\n"
                markdown += f"- **Part Number:** {part.get('part_number', 'N/A')}\n"
                markdown += f"- **Description:** {part.get('description', 'N/A')}\n"

                # Add specifications if available
                if "specifications" in part and isinstance(part["specifications"], dict):
                    markdown += "- **Specifications:**\n"
                    for key, value in part["specifications"].items():
                        if key != "additional_specs":
                            markdown += f"  - {key.replace('_', ' ').title()}: {value}\n"

                    # Add additional specifications if available
                    if "additional_specs" in part["specifications"] and isinstance(part["specifications"]["additional_specs"], dict):
                        for key, value in part["specifications"]["additional_specs"].items():
                            markdown += f"  - {key.replace('_', ' ').title()}: {value}\n"

                markdown += "\n"
        else:
            markdown += "No specific parts required.\n\n"

        # Add equipment
        markdown += "## Equipment\n\n"
        if resources["equipment"]:
            for equipment in resources["equipment"]:
                markdown += f"### {equipment['name']}\n\n"
                markdown += f"- **Category:** {equipment.get('category', 'N/A')}\n"
                markdown += f"- **Description:** {equipment.get('description', 'N/A')}\n"

                # Add specifications if available
                if "specifications" in equipment and isinstance(equipment["specifications"], dict):
                    markdown += "- **Specifications:**\n"
                    for key, value in equipment["specifications"].items():
                        if key != "additional_specs":
                            markdown += f"  - {key.replace('_', ' ').title()}: {value}\n"

                    # Add additional specifications if available
                    if "additional_specs" in equipment["specifications"] and isinstance(equipment["specifications"]["additional_specs"], dict):
                        for key, value in equipment["specifications"]["additional_specs"].items():
                            markdown += f"  - {key.replace('_', ' ').title()}: {value}\n"

                markdown += "\n"
        else:
            markdown += "No specific equipment required.\n\n"

        return markdown
