"""
Aircraft Configuration Service for the MAGPIE platform.

This module provides functionality for managing and querying aircraft configuration data
for maintenance procedures.
"""
import json
import logging
import os
from typing import Dict, List, Optional, Any, Set
from functools import lru_cache
import time

from app.core.mock.loader import get_mock_data_loader
from app.core.mock.config import MockDataSource

logger = logging.getLogger(__name__)


class AircraftConfigurationService:
    """
    Service for managing aircraft configuration data.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the aircraft configuration service.

        Args:
            data_dir: Directory containing aircraft configuration data files.
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

        self.mock_data_loader = get_mock_data_loader()
        self.aircraft_types = {}
        self.aircraft_systems = {}
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutes

        self._load_data()

    def _load_data(self) -> None:
        """
        Load aircraft configuration data from files.
        """
        try:
            # Load aircraft types
            aircraft_types_file = os.path.join(self.data_dir, "aircraft_types.json")
            if os.path.exists(aircraft_types_file):
                self.aircraft_types = self.mock_data_loader.load_file(
                    file_path=aircraft_types_file,
                    file_type="json",
                    source=MockDataSource.MAINTENANCE
                )
                logger.info(f"Loaded {len(self.aircraft_types)} aircraft types")

            # Load aircraft systems
            aircraft_systems_file = os.path.join(self.data_dir, "aircraft_systems.json")
            if os.path.exists(aircraft_systems_file):
                self.aircraft_systems = self.mock_data_loader.load_file(
                    file_path=aircraft_systems_file,
                    file_type="json",
                    source=MockDataSource.MAINTENANCE
                )
                logger.info(f"Loaded {len(self.aircraft_systems)} aircraft systems")
        except Exception as e:
            logger.error(f"Error loading aircraft configuration data: {str(e)}")

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get data from cache if available and not expired.

        Args:
            key: Cache key.

        Returns:
            Cached data or None if not available or expired.
        """
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.cache_ttl:
                return self.cache[key]
        return None

    def _store_in_cache(self, key: str, data: Any) -> None:
        """
        Store data in cache.

        Args:
            key: Cache key.
            data: Data to cache.
        """
        self.cache[key] = data
        self.cache_timestamps[key] = time.time()

    def get_all_aircraft_types(self) -> List[Dict]:
        """
        Get all aircraft types.

        Returns:
            List of all aircraft types.
        """
        cache_key = "all_aircraft_types"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        result = list(self.aircraft_types)
        self._store_in_cache(cache_key, result)
        return result

    def get_aircraft_type(self, aircraft_type: str) -> Optional[Dict]:
        """
        Get a specific aircraft type.

        Args:
            aircraft_type: The aircraft type to retrieve.

        Returns:
            The aircraft type dictionary or None if not found.
        """
        cache_key = f"aircraft_type:{aircraft_type}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Normalize aircraft type
        aircraft_type = aircraft_type.lower().replace(" ", "_")

        # Find matching aircraft type
        for ac_type in self.aircraft_types:
            if ac_type["id"].lower() == aircraft_type or ac_type["name"].lower() == aircraft_type:
                self._store_in_cache(cache_key, ac_type)
                return ac_type

        return None

    def get_all_systems(self) -> List[Dict]:
        """
        Get all aircraft systems.

        Returns:
            List of all aircraft systems.
        """
        cache_key = "all_systems"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        result = list(self.aircraft_systems)
        self._store_in_cache(cache_key, result)
        return result

    def get_system(self, system: str) -> Optional[Dict]:
        """
        Get a specific aircraft system.

        Args:
            system: The system to retrieve.

        Returns:
            The system dictionary or None if not found.
        """
        cache_key = f"system:{system}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Normalize system
        normalized_system = system.lower().replace(" ", "_")

        # Find matching system
        for sys in self.aircraft_systems:
            if sys["id"].lower() == normalized_system:
                self._store_in_cache(cache_key, sys)
                return sys

            # Check if the name matches (case-insensitive)
            if sys["name"].lower() == system.lower():
                self._store_in_cache(cache_key, sys)
                return sys

        return None

    def get_systems_for_aircraft_type(self, aircraft_type: str) -> List[Dict]:
        """
        Get systems for a specific aircraft type.

        Args:
            aircraft_type: The aircraft type to retrieve systems for.

        Returns:
            List of systems for the specified aircraft type.
        """
        cache_key = f"systems_for_aircraft:{aircraft_type}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Normalize aircraft type
        aircraft_type = aircraft_type.lower().replace(" ", "_")

        # Find matching aircraft type
        ac_type = self.get_aircraft_type(aircraft_type)
        if not ac_type:
            return []

        # Get systems for this aircraft type
        systems = []
        for sys in self.aircraft_systems:
            if "applicable_aircraft_types" in sys and (
                "all" in sys["applicable_aircraft_types"] or
                ac_type["id"] in sys["applicable_aircraft_types"] or
                ac_type["name"] in sys["applicable_aircraft_types"]
            ):
                systems.append(sys)

        self._store_in_cache(cache_key, systems)
        return systems

    def get_procedure_types_for_system(self, aircraft_type: str, system: str) -> List[Dict]:
        """
        Get procedure types for a specific aircraft system.

        Args:
            aircraft_type: The aircraft type.
            system: The system to retrieve procedure types for.

        Returns:
            List of procedure types for the specified system.
        """
        cache_key = f"procedure_types:{aircraft_type}:{system}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Normalize inputs
        aircraft_type = aircraft_type.lower().replace(" ", "_")
        system = system.lower().replace(" ", "_")

        # Find matching aircraft type and system
        ac_type = self.get_aircraft_type(aircraft_type)
        sys_type = self.get_system(system)

        if not ac_type or not sys_type:
            return []

        # Construct path to procedure types file
        procedure_types_file = os.path.join(
            self.data_dir,
            f"ac-{ac_type['id']}",
            f"sys-{sys_type['id']}",
            "procedure_types.json"
        )

        try:
            if os.path.exists(procedure_types_file):
                procedure_types = self.mock_data_loader.load_file(
                    file_path=procedure_types_file,
                    file_type="json",
                    source=MockDataSource.MAINTENANCE
                )
                self._store_in_cache(cache_key, procedure_types)
                return procedure_types
        except Exception as e:
            logger.error(f"Error loading procedure types: {str(e)}")

        return []

    def get_procedure_for_system(
        self,
        aircraft_type: str,
        system: str,
        procedure_type: str
    ) -> Optional[Dict]:
        """
        Get a procedure for a specific aircraft system and procedure type.

        Args:
            aircraft_type: The aircraft type.
            system: The system.
            procedure_type: The procedure type.

        Returns:
            The procedure dictionary or None if not found.
        """
        cache_key = f"procedure:{aircraft_type}:{system}:{procedure_type}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Normalize inputs
        aircraft_type = aircraft_type.lower().replace(" ", "_")
        system = system.lower().replace(" ", "_")
        procedure_type = procedure_type.lower().replace(" ", "_")

        # Find matching aircraft type and system
        ac_type = self.get_aircraft_type(aircraft_type)
        sys_type = self.get_system(system)

        if not ac_type or not sys_type:
            return None

        # Get procedure types for this system
        procedure_types = self.get_procedure_types_for_system(aircraft_type, system)

        # Find matching procedure type
        proc_type = None
        for pt in procedure_types:
            if pt["id"].lower() == procedure_type or pt["name"].lower() == procedure_type:
                proc_type = pt
                break

        if not proc_type:
            return None

        # Construct path to procedure file
        procedure_file = os.path.join(
            self.data_dir,
            f"ac-{ac_type['id']}",
            f"sys-{sys_type['id']}",
            f"proc-{proc_type['id']}.json"
        )

        try:
            if os.path.exists(procedure_file):
                procedure = self.mock_data_loader.load_file(
                    file_path=procedure_file,
                    file_type="json",
                    source=MockDataSource.MAINTENANCE
                )
                self._store_in_cache(cache_key, procedure)
                return procedure
        except Exception as e:
            logger.error(f"Error loading procedure: {str(e)}")

        return None

    def get_aircraft_configuration(self, aircraft_type: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific aircraft type.

        Args:
            aircraft_type: The aircraft type to retrieve configuration for.

        Returns:
            Dictionary with aircraft configuration information.
        """
        cache_key = f"aircraft_configuration:{aircraft_type}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Normalize aircraft type
        aircraft_type = aircraft_type.lower().replace(" ", "_")

        # Find matching aircraft type
        ac_type = self.get_aircraft_type(aircraft_type)
        if not ac_type:
            return {"error": f"Aircraft type '{aircraft_type}' not found"}

        # Get systems for this aircraft type
        systems = self.get_systems_for_aircraft_type(aircraft_type)

        # Build configuration
        configuration = {
            "aircraft_type": ac_type,
            "systems": systems,
            "procedure_types": {}
        }

        # Get procedure types for each system
        for system in systems:
            procedure_types = self.get_procedure_types_for_system(aircraft_type, system["id"])
            configuration["procedure_types"][system["id"]] = procedure_types

        self._store_in_cache(cache_key, configuration)
        return configuration


# Create a singleton instance
@lru_cache()
def get_aircraft_configuration_service() -> AircraftConfigurationService:
    """
    Get the aircraft configuration service instance.

    Returns:
        AircraftConfigurationService: An instance of the AircraftConfigurationService.
    """
    return AircraftConfigurationService()
