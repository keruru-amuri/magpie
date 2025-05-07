"""
Regulatory Requirements Service for the MAGPIE platform.

This module provides functionality for managing and querying regulatory requirements
for aircraft maintenance procedures.
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


class RegulatoryRequirementsService:
    """
    Service for managing regulatory requirements.
    """

    def __init__(self, requirements_dir: str = None):
        """
        Initialize the regulatory requirements service.

        Args:
            requirements_dir: Directory containing regulatory requirements files.
                If None, uses default directory.
        """
        if requirements_dir is None:
            # Default to the regulatory requirements directory in the mock data folder
            self.requirements_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "mock", "maintenance", "regulatory_requirements"
            )
        else:
            self.requirements_dir = requirements_dir

        self.mock_data_loader = get_mock_data_loader()
        self.requirements: Dict[str, Dict] = {}
        self.task_mappings: Dict[str, Dict[str, List[str]]] = {}
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutes

        self._load_requirements()
        self._load_task_mappings()

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

    def _load_requirements(self) -> None:
        """
        Load regulatory requirements from files.
        """
        try:
            # Check cache first
            cache_key = "all_requirements"
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                self.requirements = cached_data
                return

            # Load FAA requirements
            faa_file = os.path.join(self.requirements_dir, "faa_requirements.json")
            if os.path.exists(faa_file):
                faa_requirements = self.mock_data_loader.load_file(
                    file_path=faa_file,
                    file_type="json",
                    source=MockDataSource.MAINTENANCE
                )
                for req in faa_requirements:
                    self.requirements[req["id"]] = req

            # Load EASA requirements
            easa_file = os.path.join(self.requirements_dir, "easa_requirements.json")
            if os.path.exists(easa_file):
                easa_requirements = self.mock_data_loader.load_file(
                    file_path=easa_file,
                    file_type="json",
                    source=MockDataSource.MAINTENANCE
                )
                for req in easa_requirements:
                    self.requirements[req["id"]] = req

            # Store in cache
            self._store_in_cache(cache_key, self.requirements)

            logger.info(f"Loaded {len(self.requirements)} regulatory requirements")
        except Exception as e:
            logger.error(f"Error loading regulatory requirements: {str(e)}")

    def _load_task_mappings(self) -> None:
        """
        Load task mappings from file.
        """
        try:
            # Check cache first
            cache_key = "task_mappings"
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                self.task_mappings = cached_data
                return

            # Load task mappings
            mappings_file = os.path.join(self.requirements_dir, "task_mappings.json")
            if os.path.exists(mappings_file):
                self.task_mappings = self.mock_data_loader.load_file(
                    file_path=mappings_file,
                    file_type="json",
                    source=MockDataSource.MAINTENANCE
                )

                # Store in cache
                self._store_in_cache(cache_key, self.task_mappings)

                logger.info(f"Loaded task mappings for {len(self.task_mappings)} procedure types")
            else:
                logger.warning(f"Task mappings file not found: {mappings_file}")
        except Exception as e:
            logger.error(f"Error loading task mappings: {str(e)}")

    def get_all_requirements(self) -> List[Dict]:
        """
        Get all regulatory requirements.

        Returns:
            List of all regulatory requirements.
        """
        return list(self.requirements.values())

    def get_requirement(self, requirement_id: str) -> Optional[Dict]:
        """
        Get a specific regulatory requirement by ID.

        Args:
            requirement_id: The ID of the requirement to retrieve.

        Returns:
            The requirement dictionary or None if not found.
        """
        return self.requirements.get(requirement_id)

    def get_requirements_by_authority(self, authority: str) -> List[Dict]:
        """
        Get regulatory requirements by authority.

        Args:
            authority: The regulatory authority (e.g., "FAA", "EASA").

        Returns:
            List of matching requirements.
        """
        return [
            req for req in self.requirements.values()
            if req["authority"].upper() == authority.upper()
        ]

    def get_requirements_by_tags(self, tags: List[str]) -> List[Dict]:
        """
        Get regulatory requirements by tags.

        Args:
            tags: List of tags to match.

        Returns:
            List of matching requirements.
        """
        matching_requirements = []
        for req in self.requirements.values():
            if any(tag.lower() in [t.lower() for t in req["tags"]] for tag in tags):
                matching_requirements.append(req)
        return matching_requirements

    def get_requirements_by_applicability(
        self,
        aircraft_type: Optional[str] = None,
        aircraft_category: Optional[str] = None,
        operation_category: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> List[Dict]:
        """
        Get regulatory requirements by applicability.

        Args:
            aircraft_type: Aircraft type (e.g., "Boeing 737").
            aircraft_category: Aircraft category (e.g., "commercial").
            operation_category: Operation category (e.g., "IFR").
            jurisdiction: Jurisdiction (e.g., "United States").

        Returns:
            List of matching requirements.
        """
        matching_requirements = []
        for req in self.requirements.values():
            applicability = req.get("applicability", {})

            # Check aircraft type
            if aircraft_type and applicability.get("aircraft_types"):
                if aircraft_type.lower() not in [t.lower() for t in applicability["aircraft_types"]] and "all" not in applicability["aircraft_types"]:
                    continue

            # Check aircraft category
            if aircraft_category and applicability.get("aircraft_categories"):
                if aircraft_category.lower() not in [c.lower() for c in applicability["aircraft_categories"]]:
                    continue

            # Check operation category
            if operation_category and applicability.get("operation_categories"):
                if operation_category.lower() not in [c.lower() for c in applicability["operation_categories"]] and "all" not in applicability["operation_categories"]:
                    continue

            # Check jurisdiction
            if jurisdiction and applicability.get("jurisdictions"):
                if jurisdiction.lower() not in [j.lower() for j in applicability["jurisdictions"]]:
                    continue

            matching_requirements.append(req)

        return matching_requirements

    def get_requirements_for_task(
        self,
        procedure_type: str,
        system: str,
        aircraft_type: Optional[str] = None,
        aircraft_category: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> List[Dict]:
        """
        Get regulatory requirements for a specific maintenance task.

        Args:
            procedure_type: Type of procedure (e.g., "inspection", "repair").
            system: System being maintained (e.g., "fuel_system", "avionics").
            aircraft_type: Aircraft type (optional).
            aircraft_category: Aircraft category (optional).
            jurisdiction: Jurisdiction (optional).

        Returns:
            List of applicable regulatory requirements.
        """
        # Create cache key
        cache_key = f"requirements_for_task:{procedure_type}:{system}:{aircraft_type}:{aircraft_category}:{jurisdiction}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Normalize procedure type and system
        procedure_type = procedure_type.lower().replace(" ", "_")
        system = system.lower().replace(" ", "_")

        # Get requirement IDs from task mappings
        requirement_ids = set()

        # Check if we have mappings for this procedure type
        if procedure_type in self.task_mappings:
            # Check if we have mappings for this system
            if system in self.task_mappings[procedure_type]:
                requirement_ids.update(self.task_mappings[procedure_type][system])

            # Also include general requirements
            if "general" in self.task_mappings[procedure_type]:
                requirement_ids.update(self.task_mappings[procedure_type]["general"])

        # Get the actual requirements
        requirements = [
            self.requirements[req_id] for req_id in requirement_ids
            if req_id in self.requirements
        ]

        # Filter by applicability if provided
        if aircraft_type or aircraft_category or jurisdiction:
            filtered_requirements = []
            for req in requirements:
                applicability = req.get("applicability", {})

                # Check aircraft type
                if aircraft_type and applicability.get("aircraft_types"):
                    if aircraft_type.lower() not in [t.lower() for t in applicability["aircraft_types"]] and "all" not in applicability["aircraft_types"]:
                        continue

                # Check aircraft category
                if aircraft_category and applicability.get("aircraft_categories"):
                    if aircraft_category.lower() not in [c.lower() for c in applicability["aircraft_categories"]]:
                        continue

                # Check jurisdiction
                if jurisdiction and applicability.get("jurisdictions"):
                    if jurisdiction.lower() not in [j.lower() for j in applicability["jurisdictions"]]:
                        continue

                filtered_requirements.append(req)

            # Store in cache
            self._store_in_cache(cache_key, filtered_requirements)

            return filtered_requirements

        # Store in cache
        self._store_in_cache(cache_key, requirements)

        return requirements

    def validate_procedure_against_regulations(
        self,
        procedure: Dict[str, Any],
        procedure_type: str,
        system: str,
        aircraft_type: Optional[str] = None,
        aircraft_category: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a maintenance procedure against applicable regulatory requirements.

        Args:
            procedure: The procedure to validate.
            procedure_type: Type of procedure.
            system: System being maintained.
            aircraft_type: Aircraft type (optional).
            aircraft_category: Aircraft category (optional).
            jurisdiction: Jurisdiction (optional).

        Returns:
            Dictionary with validation results.
        """
        # Create a cache key based on procedure content and parameters
        procedure_hash = hash(str(procedure))
        cache_key = f"validate_procedure:{procedure_hash}:{procedure_type}:{system}:{aircraft_type}:{aircraft_category}:{jurisdiction}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Get applicable requirements
        applicable_requirements = self.get_requirements_for_task(
            procedure_type=procedure_type,
            system=system,
            aircraft_type=aircraft_type,
            aircraft_category=aircraft_category,
            jurisdiction=jurisdiction
        )

        # Initialize validation results
        validation_results = {
            "valid": True,
            "requirements": [req["reference_id"] for req in applicable_requirements],
            "issues": [],
            "recommendations": []
        }

        # Check for required fields
        required_fields = ["title", "description", "steps", "safety_precautions"]
        for field in required_fields:
            if field not in procedure:
                validation_results["valid"] = False
                validation_results["issues"].append(f"Missing required field: {field}")

        # Check for safety precautions
        if "safety_precautions" in procedure:
            if not procedure["safety_precautions"]:
                validation_results["valid"] = False
                validation_results["issues"].append("Procedure has empty safety precautions")

        # Check for steps
        if "steps" in procedure:
            if not procedure["steps"]:
                validation_results["valid"] = False
                validation_results["issues"].append("Procedure has no steps")
            else:
                # Check each step
                for i, step in enumerate(procedure["steps"]):
                    if not isinstance(step, dict):
                        validation_results["valid"] = False
                        validation_results["issues"].append(f"Step {i+1} is not a dictionary")
                        continue

                    # Check for required step fields
                    step_required_fields = ["step_number", "title", "description"]
                    for field in step_required_fields:
                        if field not in step:
                            validation_results["valid"] = False
                            validation_results["issues"].append(f"Step {i+1} missing required field: {field}")

        # Add recommendations based on applicable requirements
        for req in applicable_requirements:
            # Check if the procedure references this requirement
            if "references" in procedure and isinstance(procedure["references"], list):
                found = False
                for ref in procedure["references"]:
                    if isinstance(ref, dict) and "title" in ref and req["reference_id"] in ref["title"]:
                        found = True
                        break

                if not found:
                    validation_results["recommendations"].append(
                        f"Consider adding a reference to {req['authority']} {req['reference_id']} - {req['title']}"
                    )

        # Store in cache
        self._store_in_cache(cache_key, validation_results)

        return validation_results

    def get_regulatory_citations(
        self,
        procedure_type: str,
        system: str,
        aircraft_type: Optional[str] = None,
        aircraft_category: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> List[Dict]:
        """
        Get regulatory citations for a specific maintenance task.

        Args:
            procedure_type: Type of procedure.
            system: System being maintained.
            aircraft_type: Aircraft type (optional).
            aircraft_category: Aircraft category (optional).
            jurisdiction: Jurisdiction (optional).

        Returns:
            List of regulatory citations.
        """
        # Create cache key
        cache_key = f"regulatory_citations:{procedure_type}:{system}:{aircraft_type}:{aircraft_category}:{jurisdiction}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Get applicable requirements
        applicable_requirements = self.get_requirements_for_task(
            procedure_type=procedure_type,
            system=system,
            aircraft_type=aircraft_type,
            aircraft_category=aircraft_category,
            jurisdiction=jurisdiction
        )

        # Format as citations
        citations = []
        for req in applicable_requirements:
            citations.append({
                "authority": req["authority"],
                "reference_id": req["reference_id"],
                "title": req["title"],
                "description": req["description"]
            })

        # Store in cache
        self._store_in_cache(cache_key, citations)

        return citations
