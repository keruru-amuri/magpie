"""
Safety Precautions Service for the MAGPIE platform.

This module provides functionality for managing and querying safety precautions,
warnings, and cautions for aircraft maintenance procedures.
"""
import json
import logging
import os
from typing import Dict, List, Optional, Any, Set, Tuple

logger = logging.getLogger(__name__)


class SafetyPrecautionsService:
    """
    Service for managing safety precautions, warnings, and cautions.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the safety precautions service.

        Args:
            data_dir: Directory containing safety precautions data files.
                If None, uses default directory.
        """
        if data_dir is None:
            # Default to the mock data folder
            self.data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "mock", "maintenance", "safety_precautions"
            )
        else:
            self.data_dir = data_dir
        
        self.safety_precautions: Dict[str, Dict] = {}
        self.procedure_safety_mappings: Dict[str, Dict] = {}
        
        self._load_data()

    def _load_data(self) -> None:
        """
        Load safety precautions data from files.
        """
        try:
            # Load safety precautions
            precautions_file = os.path.join(self.data_dir, "common_precautions.json")
            if os.path.exists(precautions_file):
                with open(precautions_file, "r") as f:
                    precautions = json.load(f)
                    for precaution in precautions:
                        self.safety_precautions[precaution["id"]] = precaution
            
            # Load procedure safety mappings
            mappings_file = os.path.join(self.data_dir, "procedure_safety_mappings.json")
            if os.path.exists(mappings_file):
                with open(mappings_file, "r") as f:
                    self.procedure_safety_mappings = json.load(f)
            
            logger.info(f"Loaded {len(self.safety_precautions)} safety precautions")
        except Exception as e:
            logger.error(f"Error loading safety precautions data: {str(e)}")

    def get_all_safety_precautions(self) -> List[Dict]:
        """
        Get all safety precautions.

        Returns:
            List of all safety precautions.
        """
        return list(self.safety_precautions.values())

    def get_safety_precaution(self, precaution_id: str) -> Optional[Dict]:
        """
        Get a specific safety precaution by ID.

        Args:
            precaution_id: The ID of the safety precaution to retrieve.

        Returns:
            The safety precaution dictionary or None if not found.
        """
        return self.safety_precautions.get(precaution_id)

    def get_safety_precautions_by_type(self, precaution_type: str) -> List[Dict]:
        """
        Get safety precautions by type.

        Args:
            precaution_type: The type of safety precautions to retrieve.

        Returns:
            List of matching safety precautions.
        """
        return [
            precaution for precaution in self.safety_precautions.values()
            if precaution.get("type", "").lower() == precaution_type.lower()
        ]

    def get_safety_precautions_by_severity(self, severity: str) -> List[Dict]:
        """
        Get safety precautions by severity.

        Args:
            severity: The severity of safety precautions to retrieve.

        Returns:
            List of matching safety precautions.
        """
        return [
            precaution for precaution in self.safety_precautions.values()
            if precaution.get("severity", "").lower() == severity.lower()
        ]

    def get_safety_precautions_by_hazard_level(self, hazard_level: str) -> List[Dict]:
        """
        Get safety precautions by hazard level.

        Args:
            hazard_level: The hazard level of safety precautions to retrieve.

        Returns:
            List of matching safety precautions.
        """
        return [
            precaution for precaution in self.safety_precautions.values()
            if precaution.get("hazard_level", "").lower() == hazard_level.lower()
        ]

    def get_safety_precautions_for_procedure(
        self,
        procedure_type: str,
        system: str,
        display_location: Optional[str] = None
    ) -> List[Dict]:
        """
        Get safety precautions for a specific procedure type and system.

        Args:
            procedure_type: Type of procedure (e.g., "inspection", "repair").
            system: System being maintained (e.g., "hydraulic", "electrical").
            display_location: Optional location to filter by (e.g., "before_procedure").

        Returns:
            List of safety precautions for the specified procedure and system.
        """
        # Normalize inputs
        procedure_type = procedure_type.lower().strip()
        system = system.lower().strip()
        
        # Initialize result
        result = []
        
        # Check if we have mappings for this procedure type
        if procedure_type in self.procedure_safety_mappings:
            # Check if we have mappings for this system
            if system in self.procedure_safety_mappings[procedure_type]:
                system_mappings = self.procedure_safety_mappings[procedure_type][system]
                
                # If display_location is specified, only get precautions for that location
                if display_location:
                    display_location = display_location.lower().strip()
                    if display_location in system_mappings:
                        precaution_ids = system_mappings[display_location]
                        for precaution_id in precaution_ids:
                            if precaution_id in self.safety_precautions:
                                result.append(self.safety_precautions[precaution_id])
                else:
                    # Get all precautions for all locations
                    for location, precaution_ids in system_mappings.items():
                        if location != "specific_steps":
                            for precaution_id in precaution_ids:
                                if precaution_id in self.safety_precautions:
                                    result.append(self.safety_precautions[precaution_id])
            
            # Also include general precautions for this procedure type
            if "general" in self.procedure_safety_mappings[procedure_type]:
                general_mappings = self.procedure_safety_mappings[procedure_type]["general"]
                
                # If display_location is specified, only get precautions for that location
                if display_location:
                    display_location = display_location.lower().strip()
                    if display_location in general_mappings:
                        precaution_ids = general_mappings[display_location]
                        for precaution_id in precaution_ids:
                            if precaution_id in self.safety_precautions:
                                # Check if this precaution is already in the result
                                if not any(p["id"] == precaution_id for p in result):
                                    result.append(self.safety_precautions[precaution_id])
                else:
                    # Get all precautions for all locations
                    for location, precaution_ids in general_mappings.items():
                        if location != "specific_steps":
                            for precaution_id in precaution_ids:
                                if precaution_id in self.safety_precautions:
                                    # Check if this precaution is already in the result
                                    if not any(p["id"] == precaution_id for p in result):
                                        result.append(self.safety_precautions[precaution_id])
        
        return result

    def get_safety_precautions_for_step(
        self,
        procedure_type: str,
        system: str,
        step_reference: str
    ) -> List[Dict]:
        """
        Get safety precautions for a specific procedure step.

        Args:
            procedure_type: Type of procedure (e.g., "inspection", "repair").
            system: System being maintained (e.g., "hydraulic", "electrical").
            step_reference: Reference to the step (e.g., "preparation").

        Returns:
            List of safety precautions for the specified step.
        """
        # Normalize inputs
        procedure_type = procedure_type.lower().strip()
        system = system.lower().strip()
        step_reference = step_reference.lower().strip()
        
        # Initialize result
        result = []
        
        # Check if we have mappings for this procedure type
        if procedure_type in self.procedure_safety_mappings:
            # Check if we have mappings for this system
            if system in self.procedure_safety_mappings[procedure_type]:
                system_mappings = self.procedure_safety_mappings[procedure_type][system]
                
                # Check if we have specific step mappings
                if "specific_steps" in system_mappings and step_reference in system_mappings["specific_steps"]:
                    precaution_ids = system_mappings["specific_steps"][step_reference]
                    for precaution_id in precaution_ids:
                        if precaution_id in self.safety_precautions:
                            result.append(self.safety_precautions[precaution_id])
            
            # Also check general precautions for this procedure type
            if "general" in self.procedure_safety_mappings[procedure_type]:
                general_mappings = self.procedure_safety_mappings[procedure_type]["general"]
                
                # Check if we have specific step mappings
                if "specific_steps" in general_mappings and step_reference in general_mappings["specific_steps"]:
                    precaution_ids = general_mappings["specific_steps"][step_reference]
                    for precaution_id in precaution_ids:
                        if precaution_id in self.safety_precautions:
                            # Check if this precaution is already in the result
                            if not any(p["id"] == precaution_id for p in result):
                                result.append(self.safety_precautions[precaution_id])
        
        return result

    def extract_safety_precautions_from_text(self, text: str) -> List[Dict]:
        """
        Extract safety precaution references from text.

        Args:
            text: Text to analyze.

        Returns:
            List of safety precautions mentioned in the text.
        """
        mentioned_precautions = []
        
        # Get all safety precautions
        all_precautions = self.get_all_safety_precautions()
        
        # Check for each safety precaution description in the text
        for precaution in all_precautions:
            description = precaution["description"].lower()
            if description in text.lower():
                mentioned_precautions.append(precaution)
        
        return mentioned_precautions

    def extract_safety_precautions_from_procedure(self, procedure: Dict[str, Any]) -> List[Dict]:
        """
        Extract safety precautions from a procedure.

        Args:
            procedure: Procedure to analyze.

        Returns:
            List of safety precautions mentioned in the procedure.
        """
        result = []
        
        # Extract safety precautions from procedure description
        if "description" in procedure:
            result.extend(self.extract_safety_precautions_from_text(procedure["description"]))
        
        # Extract safety precautions from procedure steps
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
                        result.extend(self.extract_safety_precautions_from_text(step["title"]))
                    
                    # Extract from step description
                    if "description" in step:
                        result.extend(self.extract_safety_precautions_from_text(step["description"]))
                    
                    # Extract from step cautions
                    if "cautions" in step and isinstance(step["cautions"], list):
                        for caution in step["cautions"]:
                            if isinstance(caution, str):
                                result.extend(self.extract_safety_precautions_from_text(caution))
        
        # Remove duplicates by ID
        unique_precautions = {}
        for precaution in result:
            unique_precautions[precaution["id"]] = precaution
        
        return list(unique_precautions.values())

    def enrich_procedure_with_safety_precautions(
        self,
        procedure: Dict[str, Any],
        procedure_type: Optional[str] = None,
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enrich a procedure with safety precautions.

        Args:
            procedure: Procedure to enrich.
            procedure_type: Type of procedure (optional).
            system: System being maintained (optional).

        Returns:
            Enriched procedure.
        """
        # Create a copy of the procedure to avoid modifying the original
        enriched = procedure.copy()
        
        # Initialize safety_precautions if not present
        if "safety_precautions" not in enriched:
            enriched["safety_precautions"] = []
        
        # Get safety precautions for the procedure type and system
        if procedure_type and system:
            # Get safety precautions for before the procedure
            before_precautions = self.get_safety_precautions_for_procedure(
                procedure_type=procedure_type,
                system=system,
                display_location="before_procedure"
            )
            
            # Add before_procedure precautions to the procedure
            for precaution in before_precautions:
                # Check if this precaution is already in the list
                if not any(p == precaution["description"] for p in enriched["safety_precautions"]):
                    enriched["safety_precautions"].append(precaution["description"])
            
            # Get safety precautions for during the procedure
            during_precautions = self.get_safety_precautions_for_procedure(
                procedure_type=procedure_type,
                system=system,
                display_location="during_procedure"
            )
            
            # Add during_procedure precautions to the procedure
            for precaution in during_precautions:
                # Check if this precaution is already in the list
                if not any(p == precaution["description"] for p in enriched["safety_precautions"]):
                    enriched["safety_precautions"].append(precaution["description"])
            
            # Get safety precautions for after the procedure
            after_precautions = self.get_safety_precautions_for_procedure(
                procedure_type=procedure_type,
                system=system,
                display_location="after_procedure"
            )
            
            # Add after_procedure precautions to the procedure
            for precaution in after_precautions:
                # Check if this precaution is already in the list
                if not any(p == precaution["description"] for p in enriched["safety_precautions"]):
                    enriched["safety_precautions"].append(precaution["description"])
        
        # Enrich procedure steps with cautions
        steps_field = None
        if "procedure_steps" in enriched and isinstance(enriched["procedure_steps"], list):
            steps_field = "procedure_steps"
        elif "steps" in enriched and isinstance(enriched["steps"], list):
            steps_field = "steps"
        
        if steps_field and procedure_type and system:
            for step in enriched[steps_field]:
                if isinstance(step, dict):
                    # Initialize cautions if not present
                    if "cautions" not in step:
                        step["cautions"] = []
                    
                    # Try to determine the step reference from the title
                    step_reference = None
                    if "title" in step:
                        step_title = step["title"].lower()
                        if "preparation" in step_title:
                            step_reference = "preparation"
                        elif "access panel" in step_title:
                            step_reference = "access_panel_removal"
                        elif "component removal" in step_title:
                            step_reference = "component_removal"
                        elif "component inspection" in step_title:
                            step_reference = "component_inspection"
                    
                    # If we have a step reference, get safety precautions for this step
                    if step_reference:
                        step_precautions = self.get_safety_precautions_for_step(
                            procedure_type=procedure_type,
                            system=system,
                            step_reference=step_reference
                        )
                        
                        # Add step precautions to the step cautions
                        for precaution in step_precautions:
                            # Check if this precaution is already in the list
                            if not any(c == precaution["description"] for c in step["cautions"]):
                                step["cautions"].append(precaution["description"])
        
        return enriched

    def validate_procedure_safety_precautions(
        self,
        procedure: Dict[str, Any],
        procedure_type: Optional[str] = None,
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate safety precautions in a procedure.

        Args:
            procedure: Procedure to validate.
            procedure_type: Type of procedure (optional).
            system: System being maintained (optional).

        Returns:
            Dictionary with validation results.
        """
        # Initialize validation results
        validation_results = {
            "valid": True,
            "missing_precautions": [],
            "recommendations": []
        }
        
        # Check if safety_precautions is present and is a non-empty list
        if "safety_precautions" not in procedure or not isinstance(procedure["safety_precautions"], list) or len(procedure["safety_precautions"]) == 0:
            validation_results["valid"] = False
            validation_results["missing_precautions"].append("No safety precautions found in the procedure")
        
        # If procedure_type and system are provided, check for required safety precautions
        if procedure_type and system:
            # Get required safety precautions for this procedure type and system
            required_precautions = self.get_safety_precautions_for_procedure(
                procedure_type=procedure_type,
                system=system
            )
            
            # Check if all required precautions are present
            for precaution in required_precautions:
                if precaution["severity"] in ["high", "critical"]:
                    # For high and critical severity precautions, check if they are present
                    if "safety_precautions" in procedure and isinstance(procedure["safety_precautions"], list):
                        if not any(p == precaution["description"] for p in procedure["safety_precautions"]):
                            validation_results["valid"] = False
                            validation_results["missing_precautions"].append(precaution["description"])
            
            # Check if steps have cautions
            steps_field = None
            if "procedure_steps" in procedure and isinstance(procedure["procedure_steps"], list):
                steps_field = "procedure_steps"
            elif "steps" in procedure and isinstance(procedure["steps"], list):
                steps_field = "steps"
            
            if steps_field:
                for i, step in enumerate(procedure[steps_field]):
                    if isinstance(step, dict):
                        # Check if cautions is present and is a non-empty list
                        if "cautions" not in step or not isinstance(step["cautions"], list) or len(step["cautions"]) == 0:
                            validation_results["recommendations"].append(f"Step {i+1} ({step.get('title', 'Untitled')}) has no cautions")
        
        return validation_results

    def format_safety_precautions_as_markdown(self, safety_precautions: List[Dict]) -> str:
        """
        Format safety precautions as Markdown.

        Args:
            safety_precautions: List of safety precautions.

        Returns:
            Markdown-formatted safety precautions.
        """
        markdown = "# Safety Precautions\n\n"
        
        # Group safety precautions by hazard level
        hazard_levels = {
            "danger": [],
            "warning": [],
            "caution": [],
            "information": []
        }
        
        for precaution in safety_precautions:
            hazard_level = precaution.get("hazard_level", "information")
            hazard_levels[hazard_level].append(precaution)
        
        # Add danger precautions
        if hazard_levels["danger"]:
            markdown += "## Danger\n\n"
            for precaution in hazard_levels["danger"]:
                markdown += f"- **{precaution['description']}**\n"
            markdown += "\n"
        
        # Add warning precautions
        if hazard_levels["warning"]:
            markdown += "## Warning\n\n"
            for precaution in hazard_levels["warning"]:
                markdown += f"- **{precaution['description']}**\n"
            markdown += "\n"
        
        # Add caution precautions
        if hazard_levels["caution"]:
            markdown += "## Caution\n\n"
            for precaution in hazard_levels["caution"]:
                markdown += f"- {precaution['description']}\n"
            markdown += "\n"
        
        # Add information precautions
        if hazard_levels["information"]:
            markdown += "## Information\n\n"
            for precaution in hazard_levels["information"]:
                markdown += f"- {precaution['description']}\n"
            markdown += "\n"
        
        return markdown
