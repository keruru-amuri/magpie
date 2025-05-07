"""Service layer for mock data."""

import logging
from typing import Any, Dict, List, Optional

from app.core.mock.config import MockDataConfig, MockDataSource, mock_data_config
from app.core.mock.loader import MockDataLoader, mock_data_loader

logger = logging.getLogger(__name__)


class MockDataService:
    """Service for accessing mock data."""

    def __init__(
        self,
        config: MockDataConfig = mock_data_config,
        loader: MockDataLoader = mock_data_loader,
    ):
        """
        Initialize the mock data service.

        Args:
            config: Mock data configuration.
            loader: Mock data loader.
        """
        self.config = config
        self.loader = loader

    # Documentation services

    def get_documentation_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available documentation.

        Returns:
            List of documentation metadata.

        Raises:
            ValueError: If documentation mock data is disabled.
        """
        if not self.config.is_source_enabled(MockDataSource.DOCUMENTATION):
            raise ValueError("Documentation mock data is disabled")

        return self.loader.get_documentation_list()

    def get_documentation(self, doc_id: str) -> Dict[str, Any]:
        """
        Get documentation by ID.

        Args:
            doc_id: Documentation ID.

        Returns:
            Documentation data.

        Raises:
            ValueError: If documentation mock data is disabled.
            FileNotFoundError: If documentation is not found.
        """
        if not self.config.is_source_enabled(MockDataSource.DOCUMENTATION):
            raise ValueError("Documentation mock data is disabled")

        try:
            return self.loader.load_documentation(doc_id)
        except FileNotFoundError:
            logger.error(f"Documentation not found: {doc_id}")
            raise

    def search_documentation(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search documentation.

        Args:
            query: Search parameters.
                - keywords: List of keywords to search for
                - text: Free text search query
                - aircraft_type: Filter by aircraft type (e.g., "Boeing 737", "Airbus A320")
                - document_type: Filter by document type (e.g., "manual", "bulletin", "directive", "catalog")
                - system: Filter by aircraft system (e.g., "hydraulic", "electrical")
                - max_results: Maximum number of results to return (default: 5)

        Returns:
            Search results.

        Raises:
            ValueError: If documentation mock data is disabled.
        """
        if not self.config.is_source_enabled(MockDataSource.DOCUMENTATION):
            raise ValueError("Documentation mock data is disabled")

        # Get all documentation
        docs = self.get_documentation_list()

        # Apply filters
        filtered_docs = self._filter_documentation(docs, query)

        # Get maximum number of results to return
        max_results = query.get("max_results", 5)

        # Search through documentation and calculate relevance scores
        results = []
        for doc in filtered_docs:
            doc_id = doc["id"]
            try:
                doc_data = self.get_documentation(doc_id)

                # Calculate document-level relevance score
                doc_relevance = self._calculate_document_relevance(doc_data, query)

                # If document is relevant, search through sections
                if doc_relevance > 0:
                    # Find relevant sections
                    section_results = self._find_relevant_sections(doc_data, query)

                    # Add section results to overall results
                    results.extend(section_results)
            except FileNotFoundError:
                logger.warning(f"Document not found: {doc_id}")
                continue

        # Sort results by relevance score (descending)
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Limit to max_results
        results = results[:max_results]

        return {
            "query": query,
            "results_count": len(results),
            "results": results,
        }

    def _filter_documentation(self, docs: List[Dict[str, Any]], query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter documentation based on query parameters.

        Args:
            docs: List of documentation metadata.
            query: Search parameters.

        Returns:
            Filtered list of documentation metadata.
        """
        filtered_docs = docs.copy()

        # Filter by keywords if provided
        keywords = query.get("keywords", [])
        if keywords and isinstance(keywords, list):
            filtered_docs = [
                doc for doc in filtered_docs
                if any(keyword.lower() in doc["title"].lower() for keyword in keywords)
            ]

        # Filter by document type if provided
        doc_type = query.get("document_type")
        if doc_type:
            filtered_docs = [
                doc for doc in filtered_docs
                if doc["type"].lower() == doc_type.lower()
            ]

        # Filter by aircraft type if provided (based on title)
        aircraft_type = query.get("aircraft_type")
        if aircraft_type:
            filtered_docs = [
                doc for doc in filtered_docs
                if aircraft_type.lower() in doc["title"].lower()
            ]

        return filtered_docs

    def _calculate_document_relevance(self, doc_data: Dict[str, Any], query: Dict[str, Any]) -> float:
        """
        Calculate relevance score for a document.

        Args:
            doc_data: Document data.
            query: Search parameters.

        Returns:
            Relevance score (0.0 to 1.0).
        """
        relevance = 0.0

        # Get search terms
        search_terms = []

        # Add keywords to search terms
        keywords = query.get("keywords", [])
        if keywords and isinstance(keywords, list):
            search_terms.extend(keywords)

        # Add text search to search terms
        text_search = query.get("text")
        if text_search and isinstance(text_search, str):
            # Split text search into words
            search_terms.extend(text_search.lower().split())

        # If no search terms, return default relevance
        if not search_terms:
            return 0.5

        # Check title for search terms
        title_matches = sum(1 for term in search_terms if term.lower() in doc_data["title"].lower())
        if title_matches > 0:
            relevance += 0.3 * (title_matches / len(search_terms))

        # Check content for search terms
        content_matches = sum(1 for term in search_terms if term.lower() in doc_data["content"].lower())
        if content_matches > 0:
            relevance += 0.2 * (content_matches / len(search_terms))

        # Check sections for search terms
        section_matches = 0
        for section in doc_data["sections"]:
            section_title_matches = sum(1 for term in search_terms if term.lower() in section["title"].lower())
            section_content_matches = sum(1 for term in search_terms if term.lower() in section["content"].lower())
            section_matches += section_title_matches + section_content_matches

        if section_matches > 0:
            relevance += 0.5 * min(1.0, section_matches / (len(search_terms) * len(doc_data["sections"])))

        return min(1.0, relevance)

    def _find_relevant_sections(self, doc_data: Dict[str, Any], query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find relevant sections in a document.

        Args:
            doc_data: Document data.
            query: Search parameters.

        Returns:
            List of relevant sections with relevance scores.
        """
        results = []

        # Get search terms
        search_terms = []

        # Add keywords to search terms
        keywords = query.get("keywords", [])
        if keywords and isinstance(keywords, list):
            search_terms.extend(keywords)

        # Add text search to search terms
        text_search = query.get("text")
        if text_search and isinstance(text_search, str):
            # Split text search into words
            search_terms.extend(text_search.lower().split())

        # If no search terms, return empty results
        if not search_terms:
            # Return first section as default
            if doc_data["sections"]:
                section = doc_data["sections"][0]
                results.append({
                    "doc_id": doc_data["id"],
                    "section_id": section["id"],
                    "title": section["title"],
                    "relevance_score": 0.5,  # Default relevance
                    "snippet": section["content"][:150] + "...",
                    "document_title": doc_data["title"],
                    "document_type": doc_data["type"]
                })
            return results

        # Check each section for search terms
        for section in doc_data["sections"]:
            section_relevance = 0.0

            # Check section title for search terms
            title_matches = sum(1 for term in search_terms if term.lower() in section["title"].lower())
            if title_matches > 0:
                section_relevance += 0.4 * (title_matches / len(search_terms))

            # Check section content for search terms
            content_matches = sum(1 for term in search_terms if term.lower() in section["content"].lower())
            if content_matches > 0:
                section_relevance += 0.6 * (content_matches / len(search_terms))

            # If section is relevant, add to results
            if section_relevance > 0:
                # Create snippet around the first search term match
                snippet = self._create_snippet(section["content"], search_terms)

                results.append({
                    "doc_id": doc_data["id"],
                    "section_id": section["id"],
                    "title": section["title"],
                    "relevance_score": section_relevance,
                    "snippet": snippet,
                    "document_title": doc_data["title"],
                    "document_type": doc_data["type"]
                })

        return results

    def _create_snippet(self, content: str, search_terms: List[str], max_length: int = 150) -> str:
        """
        Create a snippet of content around the first search term match.

        Args:
            content: Content to create snippet from.
            search_terms: Search terms to find in content.
            max_length: Maximum length of snippet.

        Returns:
            Snippet of content.
        """
        content_lower = content.lower()

        # Find the first occurrence of any search term
        first_match_pos = -1
        first_match_term = ""

        for term in search_terms:
            term_lower = term.lower()
            pos = content_lower.find(term_lower)
            if pos != -1 and (first_match_pos == -1 or pos < first_match_pos):
                first_match_pos = pos
                first_match_term = term

        # If no match found, return beginning of content
        if first_match_pos == -1:
            return content[:max_length] + "..."

        # Calculate snippet start and end positions
        start_pos = max(0, first_match_pos - max_length // 3)
        end_pos = min(len(content), first_match_pos + len(first_match_term) + max_length // 3)

        # Create snippet
        snippet = content[start_pos:end_pos]

        # Add ellipsis if snippet doesn't start at beginning or end at end
        if start_pos > 0:
            snippet = "..." + snippet
        if end_pos < len(content):
            snippet = snippet + "..."

        return snippet

    # Troubleshooting services

    def get_troubleshooting_systems(self) -> List[Dict[str, Any]]:
        """
        Get a list of available troubleshooting systems.

        Returns:
            List of system metadata.

        Raises:
            ValueError: If troubleshooting mock data is disabled.
        """
        if not self.config.is_source_enabled(MockDataSource.TROUBLESHOOTING):
            raise ValueError("Troubleshooting mock data is disabled")

        return self.loader.get_troubleshooting_systems()

    def get_troubleshooting_symptoms(self, system_id: str) -> Dict[str, Any]:
        """
        Get symptoms for a system.

        Args:
            system_id: System ID.

        Returns:
            System data with symptoms.

        Raises:
            ValueError: If troubleshooting mock data is disabled.
            FileNotFoundError: If system is not found.
        """
        if not self.config.is_source_enabled(MockDataSource.TROUBLESHOOTING):
            raise ValueError("Troubleshooting mock data is disabled")

        try:
            return self.loader.load_troubleshooting(system_id)
        except FileNotFoundError:
            logger.error(f"System not found: {system_id}")
            raise

    def analyze_troubleshooting(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a troubleshooting case.

        Args:
            request: Troubleshooting request with system, symptoms, and context.

        Returns:
            Analysis results.

        Raises:
            ValueError: If troubleshooting mock data is disabled.
            FileNotFoundError: If system is not found.
        """
        if not self.config.is_source_enabled(MockDataSource.TROUBLESHOOTING):
            raise ValueError("Troubleshooting mock data is disabled")

        system_id = request.get("system")
        if not system_id:
            raise ValueError("System ID is required")

        try:
            # Load the analysis data for the system
            # In a real implementation, this would generate an analysis based on the symptoms
            analysis_data = self.loader.load_file(
                self.config.paths.troubleshooting_path / f"{system_id}-analysis.json",
                file_type="json",
            )

            # Update the request in the analysis data
            analysis_data["request"] = request

            return analysis_data
        except FileNotFoundError:
            logger.error(f"Analysis data not found for system: {system_id}")
            raise

    # Maintenance services

    def get_maintenance_aircraft_types(self) -> List[Dict[str, Any]]:
        """
        Get a list of available aircraft types for maintenance.

        Returns:
            List of aircraft type metadata.

        Raises:
            ValueError: If maintenance mock data is disabled.
        """
        if not self.config.is_source_enabled(MockDataSource.MAINTENANCE):
            raise ValueError("Maintenance mock data is disabled")

        return self.loader.get_maintenance_aircraft_types()

    def get_maintenance_systems(self, aircraft_id: str) -> Dict[str, Any]:
        """
        Get systems for an aircraft type.

        Args:
            aircraft_id: Aircraft type ID.

        Returns:
            Aircraft data with systems.

        Raises:
            ValueError: If maintenance mock data is disabled.
            FileNotFoundError: If aircraft type is not found.
        """
        if not self.config.is_source_enabled(MockDataSource.MAINTENANCE):
            raise ValueError("Maintenance mock data is disabled")

        try:
            # Load systems for the aircraft
            systems = self.loader.load_file(
                self.config.paths.maintenance_path / aircraft_id / "systems.json",
                file_type="json",
            )

            # Get aircraft name from aircraft types
            aircraft_types = self.get_maintenance_aircraft_types()
            aircraft_name = next(
                (at["name"] for at in aircraft_types if at["id"] == aircraft_id),
                "Unknown Aircraft"
            )

            return {
                "aircraft_id": aircraft_id,
                "aircraft_name": aircraft_name,
                "systems": systems,
            }
        except FileNotFoundError:
            logger.error(f"Aircraft type not found: {aircraft_id}")
            raise

    def get_maintenance_procedure_types(self, aircraft_id: str, system_id: str) -> Dict[str, Any]:
        """
        Get procedure types for a system.

        Args:
            aircraft_id: Aircraft type ID.
            system_id: System ID.

        Returns:
            System data with procedure types.

        Raises:
            ValueError: If maintenance mock data is disabled.
            FileNotFoundError: If aircraft type or system is not found.
        """
        if not self.config.is_source_enabled(MockDataSource.MAINTENANCE):
            raise ValueError("Maintenance mock data is disabled")

        try:
            # Load procedure types for the system
            procedure_types = self.loader.load_file(
                self.config.paths.maintenance_path / aircraft_id / system_id / "procedure_types.json",
                file_type="json",
            )

            # Get system name from systems
            systems_data = self.get_maintenance_systems(aircraft_id)
            system_name = next(
                (s["name"] for s in systems_data["systems"] if s["id"] == system_id),
                "Unknown System"
            )

            return {
                "system_id": system_id,
                "system_name": system_name,
                "procedure_types": procedure_types,
            }
        except FileNotFoundError:
            logger.error(f"System not found: {system_id} for aircraft: {aircraft_id}")
            raise

    def generate_maintenance_procedure(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a maintenance procedure.

        Args:
            request: Maintenance procedure request with aircraft type, system, procedure type, and parameters.

        Returns:
            Generated maintenance procedure.

        Raises:
            ValueError: If maintenance mock data is disabled.
            FileNotFoundError: If aircraft type, system, or procedure type is not found.
        """
        if not self.config.is_source_enabled(MockDataSource.MAINTENANCE):
            raise ValueError("Maintenance mock data is disabled")

        aircraft_id = request.get("aircraft_type")
        system_id = request.get("system")
        procedure_id = request.get("procedure_type")

        if not all([aircraft_id, system_id, procedure_id]):
            raise ValueError("Aircraft type, system, and procedure type are required")

        try:
            # Load the maintenance procedure
            procedure = self.loader.load_file(
                self.config.paths.maintenance_path / aircraft_id / system_id / f"{procedure_id}.json",
                file_type="json",
            )

            return {
                "request": request,
                "procedure": procedure,
            }
        except FileNotFoundError:
            logger.error(f"Procedure not found: {procedure_id} for system: {system_id}, aircraft: {aircraft_id}")
            raise


# WebSocket services

    def get_mock_response(
        self,
        query: str,
        agent_type: str = "documentation",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a mock response for a WebSocket message.

        Args:
            query: User query
            agent_type: Agent type (documentation, troubleshooting, maintenance)
            conversation_id: Optional conversation ID

        Returns:
            Mock response data
        """
        import random

        # Documentation responses
        documentation_responses = [
            "I've found some relevant documentation for you. The maintenance manual section 5.3.2 covers this topic in detail.",
            "According to the aircraft manual, this procedure requires special tooling. Would you like me to list the required tools?",
            "The technical documentation indicates that this component has a service life of 5,000 flight hours or 3 years, whichever comes first.",
            "Based on the documentation, this system requires inspection every 500 flight hours or 6 months.",
            "The maintenance manual recommends using part number AB-123-456 for this replacement.",
        ]

        # Troubleshooting responses
        troubleshooting_responses = [
            "Based on the symptoms you've described, this could be an issue with the hydraulic pressure sensor. I recommend checking the electrical connections first.",
            "This sounds like a known issue with the avionics cooling system. Have you checked the temperature sensors?",
            "The intermittent warning light you mentioned is typically caused by a loose connector in the landing gear assembly.",
            "From your description, I suspect a fault in the fuel quantity indicating system. Let's start by checking the wiring harness.",
            "This behavior is consistent with a faulty pressure relief valve. I recommend performing a functional test of the valve before replacing it.",
        ]

        # Maintenance responses
        maintenance_responses = [
            "Here's a step-by-step procedure for replacing that component:\n1. Ensure aircraft power is off\n2. Access the component through panel A-123\n3. Disconnect electrical connectors\n4. Remove mounting bolts\n5. Install new component\n6. Reconnect electrical connectors\n7. Perform functional test",
            "For this maintenance task, you'll need the following tools:\n- 10mm socket wrench\n- Torque wrench (5-20 Nm)\n- Multimeter\n- Safety wire pliers\n- Calibrated pressure gauge",
            "The correct torque specification for those bolts is 15 ± 2 Nm. Make sure to use a calibrated torque wrench and apply thread-locking compound.",
            "This maintenance procedure requires two technicians and approximately 4 hours to complete. Make sure you have all necessary parts before starting.",
            "After completing this maintenance task, you'll need to perform a leak check using the following procedure...",
        ]

        # Select response based on agent type
        if agent_type == "documentation":
            response_text = random.choice(documentation_responses)
            confidence = 0.85 + random.random() * 0.1
        elif agent_type == "troubleshooting":
            response_text = random.choice(troubleshooting_responses)
            confidence = 0.75 + random.random() * 0.15
        elif agent_type == "maintenance":
            response_text = random.choice(maintenance_responses)
            confidence = 0.9 + random.random() * 0.08
        else:
            response_text = "I'm not sure how to help with that. Could you provide more details?"
            confidence = 0.6 + random.random() * 0.1

        # Create response
        response = {
            "response": response_text,
            "agentType": agent_type,
            "confidence": confidence,
            "conversationId": conversation_id or f"conv-{random.randint(1000, 9999)}",
            "messageId": f"msg-{random.randint(1000, 9999)}"
        }

        return response


# Create a singleton instance for use throughout the application
mock_data_service = MockDataService()
