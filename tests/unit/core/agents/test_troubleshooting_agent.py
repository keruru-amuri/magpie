"""
Unit tests for the TroubleshootingAgent.
"""
import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

from app.core.agents.troubleshooting_agent import TroubleshootingAgent


class TestTroubleshootingAgent:
    """
    Test the TroubleshootingAgent class.
    """

    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        service = MagicMock()
        service.generate_completion = AsyncMock(return_value={"content": "This is a mock response"})
        service.generate_completion_raw = AsyncMock(return_value={
            "content": json.dumps({
                "system": "Hydraulic System",
                "symptoms": ["Low pressure", "Unusual noise"]
            })
        })
        return service

    @pytest.fixture
    def mock_troubleshooting_service(self):
        """
        Create a mock troubleshooting service.
        """
        service = MagicMock()
        service.get_systems = AsyncMock(return_value=[
            {
                "id": "system-001",
                "name": "Hydraulic System",
                "description": "Aircraft hydraulic system"
            },
            {
                "id": "system-002",
                "name": "Electrical System",
                "description": "Aircraft electrical system"
            }
        ])
        service.get_symptoms = AsyncMock(return_value=[
            {
                "id": "symptom-001",
                "description": "Low pressure",
                "system_id": "system-001"
            },
            {
                "id": "symptom-002",
                "description": "Unusual noise",
                "system_id": "system-001"
            }
        ])
        service.diagnose_issue = AsyncMock(return_value={
            "request": {
                "system": "Hydraulic System",
                "symptoms": ["Low pressure", "Unusual noise"],
                "context": "The hydraulic system is making unusual noises and showing low pressure."
            },
            "analysis": {
                "potential_causes": [
                    {
                        "id": "cause-001",
                        "description": "Faulty component",
                        "probability": 0.75,
                        "evidence": "Based on the symptoms provided, this is likely caused by a faulty component."
                    },
                    {
                        "id": "cause-002",
                        "description": "Improper maintenance",
                        "probability": 0.45,
                        "evidence": "The symptoms may also indicate improper maintenance procedures."
                    }
                ],
                "recommended_actions": [
                    {
                        "id": "action-001",
                        "description": "Inspect component",
                        "priority": "high",
                        "tools_required": ["Inspection tool", "Pressure gauge"],
                        "estimated_time": "30 minutes"
                    },
                    {
                        "id": "action-002",
                        "description": "Replace component if faulty",
                        "priority": "medium",
                        "tools_required": ["Replacement part", "Wrench set"],
                        "estimated_time": "2 hours"
                    }
                ],
                "safety_notes": [
                    "Ensure system is depressurized before inspection",
                    "Follow proper lockout/tagout procedures"
                ]
            }
        })
        return service

    @pytest.fixture
    def agent(self, mock_llm_service, mock_troubleshooting_service):
        """
        Create a TroubleshootingAgent instance.
        """
        return TroubleshootingAgent(
            llm_service=mock_llm_service,
            troubleshooting_service=mock_troubleshooting_service
        )

    @pytest.mark.asyncio
    async def test_process_query(self, agent, mock_llm_service, mock_troubleshooting_service):
        """
        Test processing a query.
        """
        # Call process_query
        result = await agent.process_query(
            query="The hydraulic system is making unusual noises and showing low pressure.",
            conversation_id="test-conversation",
            context={"aircraft_type": "Boeing 737"}
        )

        # Verify result
        assert "response" in result
        assert "diagnosis" in result
        assert result["response"] == "This is a mock response"
        assert "potential_causes" in result["diagnosis"]
        assert "recommended_actions" in result["diagnosis"]

        # Verify extract_system_and_symptoms was called
        mock_llm_service.generate_completion_raw.assert_called_once()

        # Verify diagnose_issue was called
        mock_troubleshooting_service.diagnose_issue.assert_called_once()

        # Verify generate_response was called
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_system_and_symptoms(self, agent, mock_llm_service):
        """
        Test extracting system and symptoms.
        """
        # Call extract_system_and_symptoms
        system, symptoms = await agent.extract_system_and_symptoms(
            query="The hydraulic system is making unusual noises and showing low pressure.",
            context=None
        )

        # Verify result
        assert system == "Hydraulic System"
        assert symptoms == ["Low pressure", "Unusual noise"]

        # Verify generate_completion_raw was called
        mock_llm_service.generate_completion_raw.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_system_and_symptoms_from_context(self, agent, mock_llm_service):
        """
        Test extracting system and symptoms from context.
        """
        # Call extract_system_and_symptoms with context
        system, symptoms = await agent.extract_system_and_symptoms(
            query="What could be causing these issues?",
            context={
                "system": "Hydraulic System",
                "symptoms": ["Low pressure", "Unusual noise"]
            }
        )

        # Verify result
        assert system == "Hydraulic System"
        assert symptoms == ["Low pressure", "Unusual noise"]

        # Verify generate_completion_raw was not called
        mock_llm_service.generate_completion_raw.assert_not_called()

    @pytest.mark.asyncio
    async def test_diagnose_issue(self, agent, mock_troubleshooting_service):
        """
        Test diagnosing an issue.
        """
        # Call diagnose_issue
        result = await agent.diagnose_issue(
            system="Hydraulic System",
            symptoms=["Low pressure", "Unusual noise"],
            query="The hydraulic system is making unusual noises and showing low pressure.",
            context=None
        )

        # Verify result
        assert "request" in result
        assert "analysis" in result
        assert "potential_causes" in result["analysis"]
        assert "recommended_actions" in result["analysis"]

        # Verify diagnose_issue was called
        mock_troubleshooting_service.diagnose_issue.assert_called_once_with(
            system="Hydraulic System",
            symptoms=["Low pressure", "Unusual noise"],
            context="The hydraulic system is making unusual noises and showing low pressure."
        )

    @pytest.mark.asyncio
    async def test_generate_response(self, agent, mock_llm_service):
        """
        Test generating a response.
        """
        # Create diagnosis
        diagnosis = {
            "request": {
                "system": "Hydraulic System",
                "symptoms": ["Low pressure", "Unusual noise"],
                "context": "The hydraulic system is making unusual noises and showing low pressure."
            },
            "analysis": {
                "potential_causes": [
                    {
                        "id": "cause-001",
                        "description": "Faulty component",
                        "probability": 0.75
                    }
                ],
                "recommended_actions": [
                    {
                        "id": "action-001",
                        "description": "Inspect component",
                        "priority": "high"
                    }
                ]
            }
        }

        # Call generate_response
        result = await agent.generate_response(
            query="The hydraulic system is making unusual noises and showing low pressure.",
            diagnosis=diagnosis,
            context={"aircraft_type": "Boeing 737"}
        )

        # Verify result
        assert result == "This is a mock response"

        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_systems(self, agent, mock_troubleshooting_service):
        """
        Test getting available systems.
        """
        # Call get_available_systems
        result = await agent.get_available_systems()

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "system-001"
        assert result[1]["id"] == "system-002"

        # Verify get_systems was called
        mock_troubleshooting_service.get_systems.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_symptoms_for_system(self, agent, mock_troubleshooting_service):
        """
        Test getting symptoms for a system.
        """
        # Call get_symptoms_for_system
        result = await agent.get_symptoms_for_system("system-001")

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "symptom-001"
        assert result[1]["id"] == "symptom-002"

        # Verify get_symptoms was called
        mock_troubleshooting_service.get_symptoms.assert_called_once_with("system-001")

    @pytest.mark.asyncio
    async def test_process_query_no_system_symptoms(self, agent):
        """
        Test processing a query with no system or symptoms.
        """
        # Mock extract_system_and_symptoms to return None
        with patch.object(agent, 'extract_system_and_symptoms', return_value=(None, None)):
            # Call process_query
            result = await agent.process_query(
                query="Can you help me with an issue?",
                conversation_id="test-conversation"
            )

            # Verify result
            assert "response" in result
            assert "diagnosis" in result
            assert "I need more information" in result["response"]
            assert result["diagnosis"] is None

    @pytest.mark.asyncio
    async def test_process_query_error(self, agent, mock_troubleshooting_service):
        """
        Test processing a query with an error.
        """
        # Mock extract_system_and_symptoms to raise an exception
        with patch.object(agent, 'extract_system_and_symptoms', side_effect=Exception("Test error")):
            # Call process_query
            result = await agent.process_query(
                query="The hydraulic system is making unusual noises and showing low pressure.",
                conversation_id="test-conversation"
            )

            # Verify result
            assert "response" in result
            assert "diagnosis" in result
            assert "error" in result["response"].lower()
            assert result["diagnosis"] is None

    @pytest.mark.asyncio
    async def test_generate_troubleshooting_procedure(self, agent):
        """
        Test generating a troubleshooting procedure.
        """
        # Mock troubleshooting_service.generate_troubleshooting_procedure
        procedure = {
            "system_id": "sys-001",
            "cause_id": "cause-001",
            "solution": {
                "id": "sol-001",
                "description": "Replace component",
                "difficulty": "medium",
                "estimated_time": "2 hours",
                "steps": [
                    "Step 1: Prepare necessary tools",
                    "Step 2: Remove access panels"
                ]
            },
            "parts_and_tools": {
                "parts": [{"id": "part-001", "name": "Hydraulic Pump"}],
                "tools": [{"id": "tool-001", "name": "Hydraulic Pressure Gauge"}]
            },
            "safety_precautions": [
                "Ensure aircraft is properly grounded before beginning work"
            ]
        }
        agent.troubleshooting_service.generate_troubleshooting_procedure = AsyncMock(return_value=procedure)

        # Mock _enhance_procedure_with_llm
        enhanced_procedure = procedure.copy()
        enhanced_procedure["detailed_steps"] = [
            "Detailed step 1: Gather all necessary tools including wrenches and pressure gauge",
            "Detailed step 2: Ensure all hydraulic pressure is relieved before removing panels"
        ]
        agent._enhance_procedure_with_llm = AsyncMock(return_value=enhanced_procedure)

        # Call generate_troubleshooting_procedure
        result = await agent.generate_troubleshooting_procedure(
            system_id="sys-001",
            cause_id="cause-001",
            aircraft_type="Boeing 737"
        )

        # Verify result
        assert result == enhanced_procedure
        assert "detailed_steps" in result
        agent.troubleshooting_service.generate_troubleshooting_procedure.assert_called_once_with(
            system_id="sys-001",
            cause_id="cause-001",
            aircraft_type="Boeing 737"
        )
        agent._enhance_procedure_with_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_enhance_procedure_with_llm(self, agent, mock_llm_service):
        """
        Test enhancing a procedure with LLM.
        """
        # Create procedure
        procedure = {
            "system_id": "sys-001",
            "cause_id": "cause-001",
            "solution": {
                "id": "sol-001",
                "description": "Replace component",
                "difficulty": "medium",
                "estimated_time": "2 hours",
                "steps": [
                    "Step 1: Prepare necessary tools",
                    "Step 2: Remove access panels"
                ]
            }
        }

        # Mock LLM response
        mock_llm_service.generate_completion.return_value = {
            "content": json.dumps({
                "detailed_steps": [
                    "Detailed step 1: Gather all necessary tools including wrenches and pressure gauge",
                    "Detailed step 2: Ensure all hydraulic pressure is relieved before removing panels"
                ],
                "additional_notes": [
                    "Note: Always wear proper PPE when working with hydraulic systems"
                ],
                "troubleshooting_tips": [
                    "Tip: Check for leaks around fittings before replacing the entire component"
                ]
            })
        }

        # Call _enhance_procedure_with_llm
        result = await agent._enhance_procedure_with_llm(procedure)

        # Verify result
        assert "detailed_steps" in result
        assert "additional_notes" in result
        assert "troubleshooting_tips" in result
        assert len(result["detailed_steps"]) == 2
        assert len(result["additional_notes"]) == 1
        assert len(result["troubleshooting_tips"]) == 1
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_maintenance_history(self, agent):
        """
        Test getting maintenance history.
        """
        # Call get_maintenance_history
        result = await agent.get_maintenance_history(
            aircraft_id="ac-001",
            system_id="sys-001"
        )

        # Verify result
        assert "aircraft_id" in result
        assert "system_id" in result
        assert "recent_events" in result
        assert len(result["recent_events"]) > 0

    @pytest.mark.asyncio
    async def test_diagnose_with_maintenance_history(self, agent):
        """
        Test diagnosing with maintenance history.
        """
        # Mock get_maintenance_history
        maintenance_history = {
            "aircraft_id": "ac-001",
            "system_id": "sys-001",
            "recent_events": [
                {
                    "id": "event-001",
                    "date": "2025-03-15",
                    "type": "inspection",
                    "description": "Routine inspection of hydraulic system",
                    "findings": "No issues found"
                }
            ]
        }
        agent.get_maintenance_history = AsyncMock(return_value=maintenance_history)

        # Mock troubleshooting_service.diagnose_issue
        diagnosis = {
            "request": {
                "system": "sys-001",
                "symptoms": ["sym-001", "sym-002"],
                "context": "The hydraulic system is making unusual noises"
            },
            "analysis": {
                "potential_causes": [
                    {
                        "id": "cause-001",
                        "description": "Component wear and tear",
                        "probability": 0.75
                    }
                ]
            }
        }
        agent.troubleshooting_service.diagnose_issue = AsyncMock(return_value=diagnosis)

        # Call diagnose_with_maintenance_history
        result = await agent.diagnose_with_maintenance_history(
            system="sys-001",
            symptoms=["sym-001", "sym-002"],
            aircraft_id="ac-001",
            query="The hydraulic system is making unusual noises"
        )

        # Verify result
        assert result == diagnosis
        agent.get_maintenance_history.assert_called_once_with(
            aircraft_id="ac-001",
            system_id="sys-001"
        )
        agent.troubleshooting_service.diagnose_issue.assert_called_once_with(
            system="sys-001",
            symptoms=["sym-001", "sym-002"],
            context="The hydraulic system is making unusual noises",
            maintenance_history=maintenance_history
        )
