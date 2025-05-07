"""
Troubleshooting Agent for the MAGPIE platform.

This agent diagnoses aircraft system issues and provides step-by-step troubleshooting guidance.
"""
import logging
import json
from typing import Dict, List, Optional, Any, Tuple

from app.services.llm_service import LLMService
from app.services.troubleshooting_service import troubleshooting_service
from app.services.prompt_templates import (
    TROUBLESHOOTING_ANALYSIS_TEMPLATE,
    TROUBLESHOOTING_PROCEDURE_TEMPLATE
)

# Configure logging
logger = logging.getLogger(__name__)


class TroubleshootingAgent:
    """
    Agent for diagnosing aircraft system issues and providing troubleshooting guidance.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        troubleshooting_service: Optional[Any] = None
    ):
        """
        Initialize troubleshooting agent.

        Args:
            llm_service: LLM service for generating responses
            troubleshooting_service: Service for accessing troubleshooting data
        """
        self.llm_service = llm_service or LLMService()
        self.troubleshooting_service = troubleshooting_service

        # Import troubleshooting service if not provided
        if not self.troubleshooting_service:
            from app.services.troubleshooting_service import troubleshooting_service
            self.troubleshooting_service = troubleshooting_service

    async def process_query(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a troubleshooting query.

        Args:
            query: User query
            conversation_id: Optional conversation ID
            context: Optional context information
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            Dict[str, Any]: Response with troubleshooting information
        """
        try:
            # Extract system and symptoms from query
            system, symptoms = await self.extract_system_and_symptoms(query, context, model)

            if not system or not symptoms:
                return {
                    "response": "I need more information about the system and symptoms to provide troubleshooting assistance.",
                    "diagnosis": None
                }

            # Get diagnosis
            diagnosis = await self.diagnose_issue(system, symptoms, query, context)

            if not diagnosis:
                return {
                    "response": "I couldn't generate a diagnosis based on the provided information.",
                    "diagnosis": None
                }

            # Generate response using LLM
            response = await self.generate_response(query, diagnosis, context, model, temperature, max_tokens)

            return {
                "response": response,
                "diagnosis": diagnosis["analysis"]
            }
        except Exception as e:
            logger.error(f"Error processing troubleshooting query: {str(e)}")
            return {
                "response": "I encountered an error while processing your query. Please try again later.",
                "diagnosis": None
            }

    async def extract_system_and_symptoms(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> tuple[Optional[str], Optional[List[str]]]:
        """
        Extract system and symptoms from query.

        Args:
            query: User query
            context: Optional context information
            model: Optional model to use

        Returns:
            tuple[Optional[str], Optional[List[str]]]: System and symptoms
        """
        try:
            # Check if system and symptoms are in context
            if context:
                system = context.get("system")
                symptoms = context.get("symptoms")

                if system and symptoms:
                    return system, symptoms

            # Use LLM to extract system and symptoms
            system_prompt = (
                "You are a helpful aircraft troubleshooting assistant. "
                "Your task is to extract the aircraft system and symptoms from the user's query. "
                "Respond with a JSON object containing 'system' and 'symptoms' fields."
            )

            user_prompt = f"Extract the aircraft system and symptoms from this query: {query}"

            response = await self.llm_service.generate_completion_raw(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model or "gpt-4.1-mini",
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            if not response or not response.get("content"):
                return None, None

            try:
                import json
                data = json.loads(response["content"])

                system = data.get("system")
                symptoms = data.get("symptoms", [])

                if isinstance(symptoms, str):
                    symptoms = [symptoms]

                return system, symptoms
            except Exception as e:
                logger.error(f"Error parsing system and symptoms: {str(e)}")
                return None, None
        except Exception as e:
            logger.error(f"Error extracting system and symptoms: {str(e)}")
            return None, None

    async def diagnose_issue(
        self,
        system: str,
        symptoms: List[str],
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Diagnose an issue based on system and symptoms.

        Args:
            system: System name
            symptoms: List of symptoms
            query: Original user query
            context: Optional context information

        Returns:
            Optional[Dict[str, Any]]: Diagnosis result
        """
        try:
            # Get diagnosis from troubleshooting service
            diagnosis = await self.troubleshooting_service.diagnose_issue(
                system=system,
                symptoms=symptoms,
                context=query
            )

            return diagnosis
        except Exception as e:
            logger.error(f"Error diagnosing issue: {str(e)}")
            return None

    async def generate_response(
        self,
        query: str,
        diagnosis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response based on diagnosis.

        Args:
            query: User query
            diagnosis: Diagnosis result
            context: Optional context information
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            str: Generated response
        """
        try:
            # Format diagnosis for the prompt
            import json
            formatted_diagnosis = json.dumps(diagnosis, indent=2)

            # Create prompt variables
            prompt_variables = {
                "query": query,
                "diagnosis": formatted_diagnosis
            }

            # Add context if available
            if context:
                context_str = "\n".join([f"{key}: {value}" for key, value in context.items()])
                prompt_variables["context"] = context_str

            # Generate response
            response = await self.llm_service.generate_completion(
                prompt_template=TROUBLESHOOTING_ANALYSIS_TEMPLATE,
                variables=prompt_variables,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if not response or not response.get("content"):
                return "I couldn't generate a response based on the diagnosis."

            return response["content"]
        except Exception as e:
            logger.error(f"Error generating troubleshooting response: {str(e)}")
            return "I encountered an error while generating a response. Please try again later."

    async def get_available_systems(self) -> List[Dict[str, Any]]:
        """
        Get available systems for troubleshooting.

        Returns:
            List[Dict[str, Any]]: List of available systems
        """
        try:
            return await self.troubleshooting_service.get_systems()
        except Exception as e:
            logger.error(f"Error getting available systems: {str(e)}")
            return []

    async def get_symptoms_for_system(self, system_id: str) -> List[Dict[str, Any]]:
        """
        Get symptoms for a system.

        Args:
            system_id: System ID

        Returns:
            List[Dict[str, Any]]: List of symptoms
        """
        try:
            return await self.troubleshooting_service.get_symptoms(system_id)
        except Exception as e:
            logger.error(f"Error getting symptoms for system: {str(e)}")
            return []

    async def generate_troubleshooting_procedure(
        self,
        system_id: str,
        cause_id: str,
        aircraft_type: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a detailed troubleshooting procedure for a specific cause.

        Args:
            system_id: System ID
            cause_id: Cause ID
            aircraft_type: Optional aircraft type for customization
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            Dict[str, Any]: Detailed troubleshooting procedure with LLM-enhanced instructions
        """
        try:
            # Get the basic procedure from the troubleshooting service
            procedure = await self.troubleshooting_service.generate_troubleshooting_procedure(
                system_id=system_id,
                cause_id=cause_id,
                aircraft_type=aircraft_type
            )

            if "error" in procedure:
                return procedure

            # Enhance the procedure with LLM
            enhanced_procedure = await self._enhance_procedure_with_llm(
                procedure=procedure,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return enhanced_procedure
        except Exception as e:
            logger.error(f"Error generating troubleshooting procedure: {str(e)}")
            return {
                "error": f"Error generating troubleshooting procedure: {str(e)}"
            }

    async def _enhance_procedure_with_llm(
        self,
        procedure: Dict[str, Any],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhance a troubleshooting procedure with LLM-generated content.

        Args:
            procedure: Basic procedure from the troubleshooting service
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            Dict[str, Any]: Enhanced procedure
        """
        try:
            # Format procedure for the prompt
            formatted_procedure = json.dumps(procedure, indent=2)

            # Create prompt variables
            prompt_variables = {
                "procedure": formatted_procedure,
                "system_id": procedure.get("system_id", ""),
                "cause_id": procedure.get("cause_id", "")
            }

            # Generate enhanced procedure
            response = await self.llm_service.generate_completion(
                prompt_template=TROUBLESHOOTING_PROCEDURE_TEMPLATE,
                variables=prompt_variables,
                model=model,
                temperature=temperature or 0.4,  # Lower temperature for more precise instructions
                max_tokens=max_tokens or 1500  # Ensure enough tokens for comprehensive procedure
            )

            if not response or not response.get("content"):
                return procedure  # Return original procedure if enhancement fails

            # Parse the enhanced content
            try:
                enhanced_content = json.loads(response["content"])

                # Merge the enhanced content with the original procedure
                enhanced_procedure = procedure.copy()

                # Update with enhanced content
                if "detailed_steps" in enhanced_content:
                    enhanced_procedure["detailed_steps"] = enhanced_content["detailed_steps"]

                if "additional_notes" in enhanced_content:
                    enhanced_procedure["additional_notes"] = enhanced_content["additional_notes"]

                if "troubleshooting_tips" in enhanced_content:
                    enhanced_procedure["troubleshooting_tips"] = enhanced_content["troubleshooting_tips"]

                return enhanced_procedure
            except json.JSONDecodeError:
                # If parsing fails, add the raw content as additional notes
                procedure["additional_notes"] = response["content"]
                return procedure
        except Exception as e:
            logger.error(f"Error enhancing procedure with LLM: {str(e)}")
            return procedure  # Return original procedure if enhancement fails

    async def get_maintenance_history(
        self,
        aircraft_id: str,
        system_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get maintenance history for an aircraft.

        Args:
            aircraft_id: Aircraft ID
            system_id: Optional system ID to filter by
            limit: Maximum number of records to return

        Returns:
            Dict[str, Any]: Maintenance history
        """
        try:
            # In a real implementation, this would query a maintenance history database
            # For now, return mock data
            return {
                "aircraft_id": aircraft_id,
                "system_id": system_id,
                "recent_events": [
                    {
                        "id": "event-001",
                        "date": "2025-03-15",
                        "type": "inspection",
                        "description": "Routine inspection of hydraulic system",
                        "technician": "John Doe",
                        "findings": "No issues found"
                    },
                    {
                        "id": "event-002",
                        "date": "2025-02-20",
                        "type": "repair",
                        "description": "Replaced hydraulic pump",
                        "technician": "Jane Smith",
                        "findings": "Worn pump causing pressure fluctuations"
                    },
                    {
                        "id": "event-003",
                        "date": "2025-01-10",
                        "type": "issue_reported",
                        "description": "Pilot reported unusual noise from hydraulic system",
                        "technician": "N/A",
                        "findings": "Pending investigation"
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error getting maintenance history: {str(e)}")
            return {
                "aircraft_id": aircraft_id,
                "system_id": system_id,
                "recent_events": []
            }

    async def diagnose_with_maintenance_history(
        self,
        system: str,
        symptoms: List[str],
        aircraft_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Diagnose an issue with maintenance history integration.

        Args:
            system: System ID
            symptoms: List of symptom IDs
            aircraft_id: Aircraft ID
            query: Original user query
            context: Optional context information

        Returns:
            Optional[Dict[str, Any]]: Diagnosis result with maintenance history integration
        """
        try:
            # Get maintenance history
            maintenance_history = await self.get_maintenance_history(
                aircraft_id=aircraft_id,
                system_id=system
            )

            # Get diagnosis with maintenance history
            diagnosis = await self.troubleshooting_service.diagnose_issue(
                system=system,
                symptoms=symptoms,
                context=query,
                maintenance_history=maintenance_history
            )

            return diagnosis
        except Exception as e:
            logger.error(f"Error diagnosing with maintenance history: {str(e)}")
            return None
