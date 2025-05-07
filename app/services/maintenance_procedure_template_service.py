"""
Maintenance Procedure Template Service

This service provides functionality for managing maintenance procedure templates,
including loading, retrieving, and customizing templates based on aircraft configuration.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class MaintenanceProcedureTemplateService:
    """
    Service for managing maintenance procedure templates.
    """

    def __init__(self, templates_dir: str = None):
        """
        Initialize the maintenance procedure template service.

        Args:
            templates_dir: Directory containing template files. If None, uses default directory.
        """
        if templates_dir is None:
            # Default to the templates directory in the mock data folder
            self.templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "core", "mock", "data", "maintenance_procedures", "templates"
            )
        else:
            self.templates_dir = templates_dir
        
        self.templates: Dict[str, Dict] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """
        Load all template files from the templates directory.
        """
        try:
            if not os.path.exists(self.templates_dir):
                logger.warning(f"Templates directory not found: {self.templates_dir}")
                return

            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.templates_dir, filename)
                    try:
                        with open(file_path, 'r') as file:
                            template = json.load(file)
                            template_id = template.get('template_id')
                            if template_id:
                                self.templates[template_id] = template
                                logger.debug(f"Loaded template: {template_id}")
                            else:
                                logger.warning(f"Template file missing template_id: {filename}")
                    except Exception as e:
                        logger.error(f"Error loading template file {filename}: {str(e)}")
            
            logger.info(f"Loaded {len(self.templates)} maintenance procedure templates")
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")

    def get_all_templates(self) -> List[Dict]:
        """
        Get all available templates.

        Returns:
            List of all template metadata (without full procedure details).
        """
        return [
            {
                'template_id': template['template_id'],
                'title': template['title'],
                'description': template['description'],
                'applicability': template['applicability'],
                'estimated_duration': template['estimated_duration']
            }
            for template in self.templates.values()
        ]

    def get_template(self, template_id: str) -> Optional[Dict]:
        """
        Get a specific template by ID.

        Args:
            template_id: The ID of the template to retrieve.

        Returns:
            The template dictionary or None if not found.
        """
        return self.templates.get(template_id)

    def get_templates_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict]:
        """
        Get templates that match the specified criteria.

        Args:
            criteria: Dictionary of criteria to match against templates.
                Example: {'applicability.aircraft_categories': 'commercial'}

        Returns:
            List of matching templates.
        """
        matching_templates = []

        for template in self.templates.values():
            matches = True
            for key, value in criteria.items():
                # Handle nested keys like 'applicability.aircraft_categories'
                if '.' in key:
                    parts = key.split('.')
                    current = template
                    for part in parts:
                        if part not in current:
                            matches = False
                            break
                        current = current[part]
                    
                    # Check if the value matches
                    if matches:
                        if isinstance(current, list):
                            if value not in current:
                                matches = False
                        elif current != value:
                            matches = False
                else:
                    # Handle top-level keys
                    if key not in template:
                        matches = False
                    elif isinstance(template[key], list):
                        if value not in template[key]:
                            matches = False
                    elif template[key] != value:
                        matches = False
            
            if matches:
                matching_templates.append({
                    'template_id': template['template_id'],
                    'title': template['title'],
                    'description': template['description'],
                    'applicability': template['applicability'],
                    'estimated_duration': template['estimated_duration']
                })
        
        return matching_templates

    def customize_template(self, template_id: str, aircraft_config: Dict[str, Any]) -> Optional[Dict]:
        """
        Customize a template based on aircraft configuration.

        Args:
            template_id: The ID of the template to customize.
            aircraft_config: Dictionary containing aircraft configuration parameters.

        Returns:
            Customized template dictionary or None if template not found.
        """
        template = self.get_template(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None

        # Create a deep copy of the template to avoid modifying the original
        import copy
        customized_template = copy.deepcopy(template)

        # Process each step in the procedure
        self._customize_steps(customized_template.get('procedure_steps', []), aircraft_config)

        # Add customization metadata
        customized_template['customization'] = {
            'aircraft_config': aircraft_config,
            'customized_at': self._get_current_timestamp()
        }

        return customized_template

    def _customize_steps(self, steps: List[Dict], aircraft_config: Dict[str, Any]) -> None:
        """
        Recursively customize procedure steps based on aircraft configuration.

        Args:
            steps: List of procedure steps to customize.
            aircraft_config: Dictionary containing aircraft configuration parameters.
        """
        steps_to_remove = []

        for i, step in enumerate(steps):
            # Check if the entire step is configuration dependent
            if step.get('configuration_dependent', False):
                # Check if this step applies to the current configuration
                if not self._is_applicable(step, aircraft_config):
                    steps_to_remove.append(i)
                    continue

            # Process substeps recursively
            substeps = step.get('substeps', [])
            substeps_to_remove = []

            for j, substep in enumerate(substeps):
                if substep.get('configuration_dependent', False):
                    # Check if this substep applies to the current configuration
                    if not self._is_applicable(substep, aircraft_config):
                        substeps_to_remove.append(j)
                        continue

            # Remove non-applicable substeps (in reverse order to maintain indices)
            for j in sorted(substeps_to_remove, reverse=True):
                substeps.pop(j)

        # Remove non-applicable steps (in reverse order to maintain indices)
        for i in sorted(steps_to_remove, reverse=True):
            steps.pop(i)

    def _is_applicable(self, item: Dict, aircraft_config: Dict[str, Any]) -> bool:
        """
        Check if a configuration-dependent item is applicable to the current aircraft configuration.

        Args:
            item: The configuration-dependent item to check.
            aircraft_config: Dictionary containing aircraft configuration parameters.

        Returns:
            True if the item is applicable, False otherwise.
        """
        # If the item specifies configuration variables, check that they exist in the aircraft config
        config_vars = item.get('configuration_variables', [])
        for var in config_vars:
            if var not in aircraft_config:
                return False

        # If the item specifies applicable configurations, check that the aircraft config matches
        applicable_configs = item.get('applicable_configurations', {})
        for key, values in applicable_configs.items():
            if key not in aircraft_config:
                return False
            
            if isinstance(values, list):
                if aircraft_config[key] not in values:
                    return False
            else:
                if aircraft_config[key] != values:
                    return False

        return True

    def _get_current_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.

        Returns:
            Current timestamp string.
        """
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def save_customized_template(self, customized_template: Dict, output_dir: str) -> str:
        """
        Save a customized template to a file.

        Args:
            customized_template: The customized template to save.
            output_dir: Directory where the customized template should be saved.

        Returns:
            Path to the saved template file.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        template_id = customized_template.get('template_id')
        if not template_id:
            raise ValueError("Customized template missing template_id")

        # Generate a unique filename based on template ID and timestamp
        timestamp = customized_template.get('customization', {}).get('customized_at', self._get_current_timestamp())
        timestamp = timestamp.replace(':', '-').replace('.', '-')
        filename = f"{template_id}_customized_{timestamp}.json"
        file_path = os.path.join(output_dir, filename)

        with open(file_path, 'w') as file:
            json.dump(customized_template, file, indent=2)

        logger.info(f"Saved customized template to: {file_path}")
        return file_path
