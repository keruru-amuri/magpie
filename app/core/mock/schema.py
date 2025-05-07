"""Schema validation for mock data."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import jsonschema conditionally to avoid dependency issues
try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from app.core.mock.config import MockDataConfig, MockDataSource, mock_data_config

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validator for mock data schemas."""

    def __init__(self, config: MockDataConfig = mock_data_config):
        """
        Initialize the schema validator.

        Args:
            config: Mock data configuration.
        """
        self.config = config
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

    def _load_schema(self, schema_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a JSON schema from a file.

        Args:
            schema_path: Path to the schema file.

        Returns:
            The loaded schema as a dictionary.

        Raises:
            FileNotFoundError: If the schema file does not exist.
            json.JSONDecodeError: If the schema file is not valid JSON.
        """
        schema_path_str = str(schema_path)

        # Check if schema is already cached
        if schema_path_str in self._schema_cache:
            return self._schema_cache[schema_path_str]

        # Load schema from file
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Cache schema
        self._schema_cache[schema_path_str] = schema

        return schema

    def validate(self, data: Any, schema_name: str, source: MockDataSource) -> List[str]:
        """
        Validate data against a schema.

        Args:
            data: The data to validate.
            schema_name: The name of the schema file (without path).
            source: The mock data source.

        Returns:
            A list of validation error messages, or an empty list if validation succeeds.
        """
        if not self.config.validate_schemas:
            return []

        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema is not installed. Schema validation is disabled.")
            return []

        # Construct schema path
        schema_path = self.config.paths.schemas_path / source.value / schema_name

        try:
            # Load schema
            schema = self._load_schema(schema_path)

            # Validate data
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(data))

            # Return error messages
            return [error.message for error in errors]

        except FileNotFoundError:
            logger.error(f"Schema file not found: {schema_path}")
            return [f"Schema file not found: {schema_path}"]

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file {schema_path}: {e}")
            return [f"Invalid JSON in schema file: {e}"]

        except Exception as e:
            logger.error(f"Error validating data against schema {schema_path}: {e}")
            return [f"Validation error: {e}"]

    def is_valid(self, data: Any, schema_name: str, source: MockDataSource) -> bool:
        """
        Check if data is valid according to a schema.

        Args:
            data: The data to validate.
            schema_name: The name of the schema file (without path).
            source: The mock data source.

        Returns:
            True if the data is valid, False otherwise.
        """
        return len(self.validate(data, schema_name, source)) == 0
