"""Data loader for mock data."""

import json
import logging
import random
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import yaml conditionally to avoid dependency issues
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from app.core.mock.config import MockDataConfig, MockDataSource, mock_data_config
from app.core.mock.schema import SchemaValidator

logger = logging.getLogger(__name__)


class MockDataLoader:
    """Loader for mock data."""

    def __init__(
        self,
        config: MockDataConfig = mock_data_config,
        validator: Optional[SchemaValidator] = None
    ):
        """
        Initialize the mock data loader.

        Args:
            config: Mock data configuration.
            validator: Schema validator instance.
        """
        self.config = config
        self.validator = validator or SchemaValidator(config)
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}

    def _simulate_latency(self):
        """Simulate network latency if configured."""
        if self.config.simulate_latency:
            latency = random.randint(
                self.config.min_latency_ms,
                self.config.max_latency_ms
            ) / 1000.0  # Convert to seconds
            time.sleep(latency)

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Get data from cache if available and not expired.

        Args:
            cache_key: Cache key.

        Returns:
            Cached data or None if not available or expired.
        """
        if not self.config.enable_cache:
            return None

        if cache_key not in self._cache:
            return None

        # Check if cache entry has expired
        if cache_key in self._cache_timestamps:
            timestamp = self._cache_timestamps[cache_key]
            if time.time() - timestamp > self.config.cache_ttl_seconds:
                # Cache entry has expired
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
                return None

        return self._cache[cache_key]

    def _store_in_cache(self, cache_key: str, data: Any):
        """
        Store data in cache.

        Args:
            cache_key: Cache key.
            data: Data to cache.
        """
        if not self.config.enable_cache:
            return

        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()

    def _load_json_file(self, file_path: Union[str, Path]) -> Any:
        """
        Load data from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            The loaded data.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        with open(file_path, "r") as f:
            return json.load(f)

    def _load_yaml_file(self, file_path: Union[str, Path]) -> Any:
        """
        Load data from a YAML file.

        Args:
            file_path: Path to the YAML file.

        Returns:
            The loaded data.

        Raises:
            FileNotFoundError: If the file does not exist.
            yaml.YAMLError: If the file is not valid YAML.
            ImportError: If PyYAML is not available.
        """
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is not installed. Cannot load YAML files.")

        with open(file_path, "r") as f:
            return yaml.safe_load(f)

    def _load_text_file(self, file_path: Union[str, Path]) -> str:
        """
        Load data from a text file.

        Args:
            file_path: Path to the text file.

        Returns:
            The loaded text.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        with open(file_path, "r") as f:
            return f.read()

    def load_file(
        self,
        file_path: Union[str, Path],
        file_type: Optional[str] = None,
        validate_schema: Optional[bool] = None,
        schema_name: Optional[str] = None,
        source: Optional[MockDataSource] = None,
    ) -> Any:
        """
        Load data from a file.

        Args:
            file_path: Path to the file.
            file_type: Type of file ('json', 'yaml', 'text'). If None, inferred from file extension.
            validate_schema: Whether to validate the data against a schema. If None, uses config setting.
            schema_name: Name of the schema file to validate against.
            source: Mock data source for schema validation.

        Returns:
            The loaded data.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file type cannot be determined.
            ValidationError: If schema validation fails and is enabled.
        """
        # Convert to Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Create cache key
        cache_key = f"file:{file_path}"

        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Simulate latency
        self._simulate_latency()

        # Determine file type if not specified
        if file_type is None:
            suffix = file_path.suffix.lower()
            if suffix == ".json":
                file_type = "json"
            elif suffix in (".yaml", ".yml"):
                file_type = "yaml"
            elif suffix in (".txt", ".md"):
                file_type = "text"
            else:
                raise ValueError(f"Cannot determine file type for {file_path}")

        # Load data based on file type
        try:
            if file_type == "json":
                data = self._load_json_file(file_path)
            elif file_type == "yaml":
                data = self._load_yaml_file(file_path)
            elif file_type == "text":
                data = self._load_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Validate schema if requested
            should_validate = self.config.validate_schemas if validate_schema is None else validate_schema
            if should_validate and schema_name and source:
                errors = self.validator.validate(data, schema_name, source)
                if errors:
                    error_msg = f"Schema validation failed for {file_path}: {', '.join(errors)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            # Store in cache
            self._store_in_cache(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            raise

    def load_documentation(self, doc_id: str) -> Dict[str, Any]:
        """
        Load documentation data.

        Args:
            doc_id: Documentation ID.

        Returns:
            Documentation data.

        Raises:
            FileNotFoundError: If the documentation file does not exist.
            ValueError: If the documentation is not valid.
        """
        if not self.config.is_source_enabled(MockDataSource.DOCUMENTATION):
            raise ValueError("Documentation mock data is disabled")

        # Create cache key
        cache_key = f"documentation:{doc_id}"

        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Simulate latency
        self._simulate_latency()

        # Construct file path
        file_path = self.config.paths.documentation_path / f"{doc_id}.json"

        try:
            # Load data
            data = self.load_file(
                file_path,
                file_type="json",
                schema_name="documentation.json",
                source=MockDataSource.DOCUMENTATION,
            )

            # Store in cache
            self._store_in_cache(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error loading documentation {doc_id}: {e}")
            raise

    def load_troubleshooting(self, system_id: str) -> Dict[str, Any]:
        """
        Load troubleshooting data.

        Args:
            system_id: System ID.

        Returns:
            Troubleshooting data.

        Raises:
            FileNotFoundError: If the troubleshooting file does not exist.
            ValueError: If the troubleshooting data is not valid.
        """
        if not self.config.is_source_enabled(MockDataSource.TROUBLESHOOTING):
            raise ValueError("Troubleshooting mock data is disabled")

        # Create cache key
        cache_key = f"troubleshooting:{system_id}"

        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Simulate latency
        self._simulate_latency()

        # Construct file path
        file_path = self.config.paths.troubleshooting_path / f"{system_id}.json"

        try:
            # Load data
            data = self.load_file(
                file_path,
                file_type="json",
                schema_name="troubleshooting.json",
                source=MockDataSource.TROUBLESHOOTING,
            )

            # Store in cache
            self._store_in_cache(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error loading troubleshooting data for system {system_id}: {e}")
            raise

    def load_maintenance(self, aircraft_id: str, system_id: str, procedure_id: str) -> Dict[str, Any]:
        """
        Load maintenance procedure data.

        Args:
            aircraft_id: Aircraft ID.
            system_id: System ID.
            procedure_id: Procedure ID.

        Returns:
            Maintenance procedure data.

        Raises:
            FileNotFoundError: If the maintenance procedure file does not exist.
            ValueError: If the maintenance procedure data is not valid.
        """
        if not self.config.is_source_enabled(MockDataSource.MAINTENANCE):
            raise ValueError("Maintenance mock data is disabled")

        # Create cache key
        cache_key = f"maintenance:{aircraft_id}:{system_id}:{procedure_id}"

        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Simulate latency
        self._simulate_latency()

        # Construct file path
        file_path = self.config.paths.maintenance_path / aircraft_id / system_id / f"{procedure_id}.json"

        try:
            # Load data
            data = self.load_file(
                file_path,
                file_type="json",
                schema_name="maintenance.json",
                source=MockDataSource.MAINTENANCE,
            )

            # Store in cache
            self._store_in_cache(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error loading maintenance procedure {procedure_id} for aircraft {aircraft_id}, system {system_id}: {e}")
            raise

    def clear_cache(self):
        """Clear the data cache."""
        self._cache.clear()
        self._cache_timestamps.clear()

    def get_documentation_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available documentation.

        Returns:
            List of documentation metadata.
        """
        if not self.config.is_source_enabled(MockDataSource.DOCUMENTATION):
            raise ValueError("Documentation mock data is disabled")

        # Create cache key
        cache_key = "documentation:list"

        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Simulate latency
        self._simulate_latency()

        # Construct file path
        file_path = self.config.paths.documentation_path / "index.json"

        try:
            # Load data
            data = self.load_file(
                file_path,
                file_type="json",
                schema_name="documentation_list.json",
                source=MockDataSource.DOCUMENTATION,
            )

            # Store in cache
            self._store_in_cache(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error loading documentation list: {e}")
            raise

    def get_troubleshooting_systems(self) -> List[Dict[str, Any]]:
        """
        Get a list of available troubleshooting systems.

        Returns:
            List of system metadata.
        """
        if not self.config.is_source_enabled(MockDataSource.TROUBLESHOOTING):
            raise ValueError("Troubleshooting mock data is disabled")

        # Create cache key
        cache_key = "troubleshooting:systems"

        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Simulate latency
        self._simulate_latency()

        # Construct file path
        file_path = self.config.paths.troubleshooting_path / "systems.json"

        try:
            # Load data
            data = self.load_file(
                file_path,
                file_type="json",
                schema_name="systems.json",
                source=MockDataSource.TROUBLESHOOTING,
            )

            # Store in cache
            self._store_in_cache(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error loading troubleshooting systems: {e}")
            raise

    def get_maintenance_aircraft_types(self) -> List[Dict[str, Any]]:
        """
        Get a list of available aircraft types for maintenance.

        Returns:
            List of aircraft type metadata.
        """
        if not self.config.is_source_enabled(MockDataSource.MAINTENANCE):
            raise ValueError("Maintenance mock data is disabled")

        # Create cache key
        cache_key = "maintenance:aircraft_types"

        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Simulate latency
        self._simulate_latency()

        # Construct file path
        file_path = self.config.paths.maintenance_path / "aircraft_types.json"

        try:
            # Load data
            data = self.load_file(
                file_path,
                file_type="json",
                schema_name="aircraft_types.json",
                source=MockDataSource.MAINTENANCE,
            )

            # Store in cache
            self._store_in_cache(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error loading maintenance aircraft types: {e}")
            raise


# Create a singleton instance for use throughout the application
@lru_cache()
def get_mock_data_loader() -> MockDataLoader:
    """
    Get the mock data loader instance.

    Returns:
        MockDataLoader instance.
    """
    return MockDataLoader()


# Export the loader instance for use throughout the application
mock_data_loader = get_mock_data_loader()
