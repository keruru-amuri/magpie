"""
Unit tests for the MaintenanceAgent.
"""
import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

from app.core.agents.maintenance_agent import MaintenanceAgent


class TestMaintenanceAgent:
    """
    Test the MaintenanceAgent class.
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
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic System",
                "procedure_type": "Inspection",
                "parameters": {
                    "component": "Pump",
                    "interval": "100 hours"
                }
            })
        })
        service.generate_response_async = AsyncMock(return_value={
            "content": json.dumps({
                "id": "maint-001",
                "title": "Test Procedure",
                "description": "Test procedure description",
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Test Step",
                        "description": "Test step description",
                        "cautions": ["Test caution"]
                    }
                ],
                "safety_precautions": ["Test safety precaution"],
                "tools_required": [
                    {
                        "id": "tool-001",
                        "name": "Test Tool",
                        "specification": "Test specification"
                    }
                ]
            })
        })
        return service

    @pytest.fixture
    def mock_maintenance_service(self):
        """
        Create a mock maintenance service.
        """
        service = MagicMock()
        service.get_aircraft_types = AsyncMock(return_value=[
            {
                "id": "aircraft-001",
                "name": "Boeing 737",
                "description": "Boeing 737 aircraft"
            },
            {
                "id": "aircraft-002",
                "name": "Airbus A320",
                "description": "Airbus A320 aircraft"
            }
        ])
        service.get_systems = AsyncMock(return_value=[
            {
                "id": "system-001",
                "name": "Hydraulic System",
                "description": "Aircraft hydraulic system",
                "aircraft_id": "aircraft-001"
            },
            {
                "id": "system-002",
                "name": "Electrical System",
                "description": "Aircraft electrical system",
                "aircraft_id": "aircraft-001"
            }
        ])
        service.get_procedure_types = AsyncMock(return_value=[
            {
                "id": "procedure-type-001",
                "name": "Inspection",
                "description": "Inspection procedure"
            },
            {
                "id": "procedure-type-002",
                "name": "Replacement",
                "description": "Replacement procedure"
            }
        ])
        service.generate_procedure = AsyncMock(return_value={
            "request": {
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic System",
                "procedure_type": "Inspection",
                "parameters": {
                    "component": "Pump",
                    "interval": "100 hours"
                }
            },
            "procedure": {
                "title": "Inspection Procedure for Hydraulic System on Boeing 737",
                "description": "This procedure provides steps for inspection of the Hydraulic System on Boeing 737 aircraft.",
                "prerequisites": [
                    "Ensure aircraft is properly grounded",
                    "Obtain necessary tools and equipment",
                    "Review relevant technical documentation"
                ],
                "safety_precautions": [
                    "Follow all safety protocols",
                    "Use appropriate personal protective equipment",
                    "Ensure system is de-energized before beginning work"
                ],
                "tools_required": [
                    "Standard tool kit",
                    "Specialized tools as needed",
                    "Calibrated measurement equipment"
                ],
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Prepare the work area",
                        "details": "Clear the work area and ensure proper lighting and ventilation."
                    },
                    {
                        "step_number": 2,
                        "description": "Access the system",
                        "details": "Remove access panels or covers as necessary."
                    },
                    {
                        "step_number": 3,
                        "description": "Perform the inspection",
                        "details": "Follow the specific steps for the inspection procedure."
                    },
                    {
                        "step_number": 4,
                        "description": "Verify completion",
                        "details": "Ensure all work has been completed correctly."
                    },
                    {
                        "step_number": 5,
                        "description": "Close up and document",
                        "details": "Replace all access panels and document the work performed."
                    }
                ],
                "verification": [
                    "Perform functional test as required",
                    "Verify proper operation of the system",
                    "Document all test results"
                ],
                "references": [
                    {
                        "title": "Aircraft Maintenance Manual",
                        "section": "Chapter 5, Section 3",
                        "document_id": "AMM-001"
                    },
                    {
                        "title": "Component Maintenance Manual",
                        "section": "Chapter 2, Section 1",
                        "document_id": "CMM-001"
                    }
                ]
            }
        })
        return service

    @pytest.fixture
    def mock_template_service(self):
        """
        Create a mock template service.
        """
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_regulatory_service(self):
        """
        Create a mock regulatory service.
        """
        service = MagicMock()
        service.get_regulatory_citations = MagicMock(return_value=[
            {
                "authority": "FAA",
                "reference_id": "14 CFR 43.13",
                "title": "Performance rules (general)",
                "description": "General performance rules for maintenance"
            },
            {
                "authority": "EASA",
                "reference_id": "Part-145",
                "title": "Maintenance Organisation Approvals",
                "description": "Requirements for maintenance organizations"
            }
        ])
        service.validate_procedure_against_regulations = MagicMock(return_value={
            "valid": True,
            "requirements": ["14 CFR 43.13", "Part-145"],
            "issues": [],
            "recommendations": ["Consider adding a reference to EASA Part-145 - Maintenance Organisation Approvals"]
        })
        return service

    @pytest.fixture
    def agent(self, mock_llm_service, mock_maintenance_service, mock_template_service, mock_regulatory_service):
        """
        Create a MaintenanceAgent instance.
        """
        return MaintenanceAgent(
            llm_service=mock_llm_service,
            maintenance_service=mock_maintenance_service,
            template_service=mock_template_service,
            regulatory_service=mock_regulatory_service
        )

    @pytest.mark.asyncio
    async def test_process_query(self, agent, mock_llm_service, mock_maintenance_service):
        """
        Test processing a query.
        """
        # Call process_query
        result = await agent.process_query(
            query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
            conversation_id="test-conversation",
            context={"aircraft_type": "Boeing 737"}
        )

        # Verify result
        assert "response" in result
        assert "procedure" in result
        assert result["response"] == "This is a mock response"
        assert "title" in result["procedure"]
        assert "steps" in result["procedure"]

        # Verify extract_maintenance_parameters was called
        mock_llm_service.generate_completion_raw.assert_called_once()

        # Verify generate_procedure was called
        mock_maintenance_service.generate_procedure.assert_called_once()

        # Verify generate_response was called
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_maintenance_parameters(self, agent, mock_llm_service):
        """
        Test extracting maintenance parameters.
        """
        # Call extract_maintenance_parameters
        result = await agent.extract_maintenance_parameters(
            query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
            context=None
        )

        # Verify result
        assert result["aircraft_type"] == "Boeing 737"
        assert result["system"] == "Hydraulic System"
        assert result["procedure_type"] == "Inspection"
        assert "component" in result["parameters"]
        assert result["parameters"]["component"] == "Pump"

        # Verify generate_completion_raw was called
        mock_llm_service.generate_completion_raw.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_maintenance_parameters_from_context(self, agent, mock_llm_service):
        """
        Test extracting maintenance parameters from context.
        """
        # Call extract_maintenance_parameters with context
        result = await agent.extract_maintenance_parameters(
            query="What are the steps for this procedure?",
            context={
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic System",
                "procedure_type": "Inspection",
                "parameters": {
                    "component": "Pump",
                    "interval": "100 hours"
                }
            }
        )

        # Verify result
        assert result["aircraft_type"] == "Boeing 737"
        assert result["system"] == "Hydraulic System"
        assert result["procedure_type"] == "Inspection"
        assert "component" in result["parameters"]
        assert result["parameters"]["component"] == "Pump"

        # Verify generate_completion_raw was not called
        mock_llm_service.generate_completion_raw.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_procedure(self, agent, mock_maintenance_service):
        """
        Test generating a procedure.
        """
        # Call generate_procedure
        result = await agent.generate_procedure(
            aircraft_type="Boeing 737",
            system="Hydraulic System",
            procedure_type="Inspection",
            parameters={"component": "Pump", "interval": "100 hours"},
            query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
            context=None
        )

        # Verify result
        assert "request" in result
        assert "procedure" in result
        assert "title" in result["procedure"]
        assert "steps" in result["procedure"]

        # Verify generate_procedure was called
        mock_maintenance_service.generate_procedure.assert_called_once_with(
            aircraft_type="Boeing 737",
            system="Hydraulic System",
            procedure_type="Inspection",
            parameters={"component": "Pump", "interval": "100 hours"}
        )

    @pytest.mark.asyncio
    async def test_generate_response(self, agent, mock_llm_service):
        """
        Test generating a response.
        """
        # Create procedure
        procedure = {
            "request": {
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic System",
                "procedure_type": "Inspection",
                "parameters": {
                    "component": "Pump",
                    "interval": "100 hours"
                }
            },
            "procedure": {
                "title": "Inspection Procedure for Hydraulic System on Boeing 737",
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Prepare the work area"
                    },
                    {
                        "step_number": 2,
                        "description": "Access the system"
                    }
                ]
            }
        }

        # Call generate_response
        result = await agent.generate_response(
            query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
            procedure=procedure,
            context={"aircraft_type": "Boeing 737"}
        )

        # Verify result
        assert result == "This is a mock response"

        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_aircraft_types(self, agent, mock_maintenance_service):
        """
        Test getting aircraft types.
        """
        # Call get_aircraft_types
        result = await agent.get_aircraft_types()

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "aircraft-001"
        assert result[1]["id"] == "aircraft-002"

        # Verify get_aircraft_types was called
        mock_maintenance_service.get_aircraft_types.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_systems_for_aircraft(self, agent, mock_maintenance_service):
        """
        Test getting systems for an aircraft.
        """
        # Call get_systems_for_aircraft
        result = await agent.get_systems_for_aircraft("aircraft-001")

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "system-001"
        assert result[1]["id"] == "system-002"

        # Verify get_systems was called
        mock_maintenance_service.get_systems.assert_called_once_with("aircraft-001")

    @pytest.mark.asyncio
    async def test_get_procedure_types(self, agent, mock_maintenance_service):
        """
        Test getting procedure types.
        """
        # Call get_procedure_types
        result = await agent.get_procedure_types("aircraft-001", "system-001")

        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "procedure-type-001"
        assert result[1]["id"] == "procedure-type-002"

        # Verify get_procedure_types was called
        mock_maintenance_service.get_procedure_types.assert_called_once_with("aircraft-001", "system-001")

    @pytest.mark.asyncio
    async def test_process_query_no_parameters(self, agent):
        """
        Test processing a query with no parameters.
        """
        # Mock extract_maintenance_parameters to return None
        with patch.object(agent, 'extract_maintenance_parameters', return_value=None):
            # Call process_query
            result = await agent.process_query(
                query="Can you help me with a maintenance procedure?",
                conversation_id="test-conversation"
            )

            # Verify result
            assert "response" in result
            assert "procedure" in result
            assert "I need more information" in result["response"]
            assert result["procedure"] is None

    @pytest.mark.asyncio
    async def test_process_query_error(self, agent):
        """
        Test processing a query with an error.
        """
        # Mock extract_maintenance_parameters to raise an exception
        with patch.object(agent, 'extract_maintenance_parameters', side_effect=Exception("Test error")):
            # Call process_query
            result = await agent.process_query(
                query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
                conversation_id="test-conversation"
            )

            # Verify result
            assert "response" in result
            assert "procedure" in result
            assert "error" in result["response"].lower()
            assert result["procedure"] is None

    @pytest.fixture
    def mock_template(self):
        """
        Fixture providing a mock template.
        """
        return {
            "template_id": "MP-TEST-001",
            "title": "Test Template",
            "description": "Test template for unit testing",
            "applicability": {
                "aircraft_categories": ["commercial", "private"],
                "engine_types": ["turbofan"]
            },
            "estimated_duration": {
                "hours": 2,
                "minutes": 30
            },
            "required_qualifications": [
                {
                    "qualification_id": "QUAL-001",
                    "name": "Test Qualification",
                    "description": "Test qualification description"
                }
            ],
            "regulatory_references": [
                {
                    "authority": "FAA",
                    "reference_id": "14 CFR 43.13",
                    "description": "Performance rules (general)"
                }
            ],
            "safety_precautions": [
                {
                    "precaution_id": "SP-001",
                    "severity": "warning",
                    "description": "Test safety precaution"
                }
            ],
            "required_tools": [
                {
                    "tool_id": "TL-001",
                    "name": "Test Tool",
                    "description": "Test tool description",
                    "optional": False
                }
            ],
            "required_materials": [
                {
                    "material_id": "MT-001",
                    "name": "Test Material",
                    "description": "Test material description",
                    "quantity": "1",
                    "optional": False
                }
            ],
            "procedure_steps": [
                {
                    "step_id": "STEP-001",
                    "title": "Test Step",
                    "description": "Test step description",
                    "substeps": [
                        {
                            "substep_id": "SUBSTEP-001-01",
                            "description": "Test substep description"
                        }
                    ]
                }
            ],
            "sign_off_requirements": {
                "inspector_certification": True,
                "supervisor_review": False,
                "quality_assurance_review": False,
                "documentation_required": [
                    "Test documentation"
                ]
            },
            "references": [
                {
                    "reference_id": "REF-001",
                    "title": "Test Reference",
                    "section": "Test Section",
                    "document_id": "DOC-001"
                }
            ],
            "revision_history": [
                {
                    "revision": "A",
                    "date": "2023-01-01",
                    "description": "Initial release"
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_get_available_templates_all(self, agent, mock_template_service):
        """
        Test retrieving all available templates.
        """
        # Configure mock
        mock_templates = [
            {
                "template_id": "MP-TEST-001",
                "title": "Test Template 1",
                "description": "Test template 1"
            },
            {
                "template_id": "MP-TEST-002",
                "title": "Test Template 2",
                "description": "Test template 2"
            }
        ]
        mock_template_service.get_all_templates.return_value = mock_templates

        # Call method
        result = await agent.get_available_templates()

        # Verify result
        assert result.success is True
        assert "Found 2 available maintenance procedure templates" in result.response
        assert result.data["templates"] == mock_templates
        mock_template_service.get_all_templates.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_templates_filtered(self, agent, mock_template_service):
        """
        Test retrieving templates filtered by criteria.
        """
        # Configure mock
        mock_templates = [
            {
                "template_id": "MP-TEST-001",
                "title": "Test Template 1",
                "description": "Test template 1"
            }
        ]
        criteria = {"applicability.aircraft_categories": "commercial"}
        mock_template_service.get_templates_by_criteria.return_value = mock_templates

        # Call method
        result = await agent.get_available_templates(criteria)

        # Verify result
        assert result.success is True
        assert "Found 1 templates matching your criteria" in result.response
        assert result.data["templates"] == mock_templates
        mock_template_service.get_templates_by_criteria.assert_called_once_with(criteria)

    @pytest.mark.asyncio
    async def test_get_template_details_found(self, agent, mock_template_service, mock_template):
        """
        Test retrieving template details when template exists.
        """
        # Configure mock
        mock_template_service.get_template.return_value = mock_template

        # Call method
        result = await agent.get_template_details("MP-TEST-001")

        # Verify result
        assert result.success is True
        assert "Here are the details for maintenance procedure template MP-TEST-001" in result.response
        assert result.data["template"] == mock_template
        mock_template_service.get_template.assert_called_once_with("MP-TEST-001")

    @pytest.mark.asyncio
    async def test_get_template_details_not_found(self, agent, mock_template_service):
        """
        Test retrieving template details when template does not exist.
        """
        # Configure mock
        mock_template_service.get_template.return_value = None

        # Call method
        result = await agent.get_template_details("NON-EXISTENT")

        # Verify result
        assert result.success is False
        assert "I couldn't find a template with ID NON-EXISTENT" in result.response
        assert result.data is None

    @pytest.mark.asyncio
    async def test_generate_procedure_from_template_json(self, agent, mock_template_service, mock_template):
        """
        Test generating a procedure from a template in JSON format.
        """
        # Configure mocks
        mock_template_service.get_template.return_value = mock_template
        mock_template_service.customize_template.return_value = mock_template

        # Call method
        aircraft_config = {"engine_type": "turbofan"}
        result = await agent.generate_procedure_from_template("MP-TEST-001", aircraft_config, "json")

        # Verify result
        assert result.success is True
        assert "I've generated a customized maintenance procedure" in result.response
        assert result.data["procedure"] == mock_template
        assert result.data["format"] == "json"
        assert result.data["template_id"] == "MP-TEST-001"
        assert result.data["aircraft_config"] == aircraft_config
        assert "generated_at" in result.data
        mock_template_service.get_template.assert_called_once_with("MP-TEST-001")
        mock_template_service.customize_template.assert_called_once_with("MP-TEST-001", aircraft_config)

    @pytest.mark.asyncio
    async def test_generate_procedure_from_template_markdown(self, agent, mock_template_service, mock_template):
        """
        Test generating a procedure from a template in Markdown format.
        """
        # Configure mocks
        mock_template_service.get_template.return_value = mock_template
        mock_template_service.customize_template.return_value = mock_template

        # Patch the _format_procedure_as_markdown method
        with patch.object(agent, '_format_procedure_as_markdown', return_value="# Markdown Content"):
            # Call method
            aircraft_config = {"engine_type": "turbofan"}
            result = await agent.generate_procedure_from_template("MP-TEST-001", aircraft_config, "markdown")

            # Verify result
            assert result.success is True
            assert "I've generated a customized maintenance procedure" in result.response
            assert result.data["procedure"] == "# Markdown Content"
            assert result.data["format"] == "markdown"
            agent._format_procedure_as_markdown.assert_called_once_with(mock_template)

    def test_format_procedure_as_markdown(self, agent, mock_template):
        """
        Test formatting a procedure as Markdown.
        """
        # Call method
        markdown = agent._format_procedure_as_markdown(mock_template)

        # Verify result
        assert "# Test Template" in markdown
        assert "## Description" in markdown
        assert "## Applicability" in markdown
        assert "## Required Qualifications" in markdown
        assert "## Estimated Duration" in markdown
        assert "## Regulatory References" in markdown
        assert "## Safety Precautions" in markdown
        assert "## Required Tools" in markdown
        assert "## Required Materials" in markdown
        assert "## Procedure Steps" in markdown
        assert "### STEP-001: Test Step" in markdown
        assert "## Sign-Off Requirements" in markdown
        assert "## References" in markdown
        assert "## Revision History" in markdown

    @pytest.mark.asyncio
    async def test_validate_procedure_valid(self, agent):
        """
        Test validating a valid procedure.
        """
        # Create a valid procedure
        procedure = {
            "template_id": "MP-TEST-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "safety_precautions": [
                {
                    "precaution_id": "SP-001",
                    "severity": "warning",
                    "description": "Test safety precaution"
                }
            ],
            "procedure_steps": [
                {
                    "step_id": "STEP-001",
                    "title": "Test Step",
                    "description": "Test step description"
                }
            ]
        }

        # Call method
        result = await agent.validate_procedure(procedure)

        # Verify result
        assert result.success is True
        assert "The maintenance procedure has been validated successfully" in result.response
        assert result.data["validation_result"] == "passed"

    @pytest.mark.asyncio
    async def test_validate_procedure_invalid(self, agent):
        """
        Test validating an invalid procedure.
        """
        # Create an invalid procedure (missing required fields)
        procedure = {
            "template_id": "MP-TEST-001",
            # Missing title
            "description": "Test procedure description",
            # Missing safety_precautions
            "procedure_steps": [
                {
                    # Missing step_id
                    "title": "Test Step",
                    # Missing description
                }
            ]
        }

        # Call method
        result = await agent.validate_procedure(procedure)

        # Verify result
        assert result.success is False
        assert "The maintenance procedure failed validation" in result.response
        assert len(result.data["validation_errors"]) > 0
        assert "Missing required field: title" in result.data["validation_errors"]
        assert "Procedure is missing safety precautions" in result.data["validation_errors"]
        assert "Step 1 is missing step_id" in result.data["validation_errors"]
        assert "Step 1 is missing description" in result.data["validation_errors"]

    @pytest.mark.asyncio
    async def test_save_procedure(self, agent, mock_template_service):
        """
        Test saving a procedure.
        """
        # Configure mock
        mock_template_service.save_customized_template.return_value = "/mock/output/procedure.json"

        # Call method
        procedure = {"template_id": "MP-TEST-001"}
        result = await agent.save_procedure(procedure, "/mock/output")

        # Verify result
        assert result.success is True
        assert "The maintenance procedure has been saved successfully" in result.response
        assert result.data["file_path"] == "/mock/output/procedure.json"
        mock_template_service.save_customized_template.assert_called_once_with(procedure, "/mock/output")

    @pytest.mark.asyncio
    async def test_generate_procedure_with_llm(self, agent, mock_llm_service):
        """
        Test generating a procedure with LLM.
        """
        # Configure mock
        mock_response = {
            "content": json.dumps({
                "id": "maint-001",
                "title": "Test Procedure",
                "description": "Test procedure description",
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Test Step",
                        "description": "Test step description",
                        "cautions": ["Test caution"]
                    }
                ],
                "safety_precautions": ["Test safety precaution"],
                "tools_required": [
                    {
                        "id": "tool-001",
                        "name": "Test Tool",
                        "specification": "Test specification"
                    }
                ]
            })
        }
        mock_llm_service.generate_response_async.return_value = mock_response

        # Call method
        procedure = await agent.generate_procedure_with_llm(
            procedure_type="Inspection",
            aircraft_type="Boeing 737",
            aircraft_model="737-800",
            system="Hydraulic",
            components="Pumps, Reservoirs",
            configuration="Standard configuration",
            regulatory_requirements="FAA regulations",
            special_considerations="None"
        )

        # Verify result
        assert procedure is not None
        assert procedure["id"] == "maint-001"
        assert procedure["title"] == "Test Procedure"
        assert len(procedure["steps"]) == 1
        assert len(procedure["safety_precautions"]) == 1
        assert len(procedure["tools_required"]) == 1

        # Verify LLM service was called with correct parameters
        mock_llm_service.generate_response_async.assert_called_once()
        args, kwargs = mock_llm_service.generate_response_async.call_args
        assert kwargs["template_name"] == "maintenance_procedure_generation"
        assert kwargs["variables"]["procedure_type"] == "Inspection"
        assert kwargs["variables"]["aircraft_type"] == "Boeing 737"
        assert kwargs["variables"]["system"] == "Hydraulic"

    @pytest.mark.asyncio
    async def test_generate_procedure_with_llm_validation_failure(self, agent, mock_llm_service):
        """
        Test generating a procedure with LLM when validation fails.
        """
        # Configure mock to return an invalid procedure (missing required fields)
        mock_response = {
            "content": json.dumps({
                "id": "maint-001",
                "title": "Test Procedure",
                # Missing description
                # Missing steps
                "safety_precautions": ["Test safety precaution"]
                # Missing tools_required
            })
        }
        mock_llm_service.generate_response_async.return_value = mock_response

        # Call method
        procedure = await agent.generate_procedure_with_llm(
            procedure_type="Inspection",
            aircraft_type="Boeing 737",
            aircraft_model="737-800",
            system="Hydraulic",
            components="Pumps, Reservoirs",
            configuration="Standard configuration",
            regulatory_requirements="FAA regulations",
            special_considerations="None"
        )

        # Verify result
        assert procedure is None

    @pytest.mark.asyncio
    async def test_enhance_procedure_with_llm(self, agent, mock_llm_service):
        """
        Test enhancing a procedure with LLM.
        """
        # Configure mock
        mock_response = {
            "content": json.dumps({
                "id": "maint-001",
                "title": "Enhanced Test Procedure",
                "description": "Enhanced test procedure description",
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Enhanced Test Step",
                        "description": "Enhanced test step description",
                        "cautions": ["Enhanced test caution"]
                    }
                ],
                "safety_precautions": ["Enhanced test safety precaution"],
                "tools_required": [
                    {
                        "id": "tool-001",
                        "name": "Enhanced Test Tool",
                        "specification": "Enhanced test specification"
                    }
                ]
            })
        }
        mock_llm_service.generate_response_async.return_value = mock_response

        # Base procedure to enhance
        base_procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description",
                    "cautions": ["Test caution"]
                }
            ],
            "safety_precautions": ["Test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "specification": "Test specification"
                }
            ]
        }

        # Call method
        enhanced_procedure = await agent.enhance_procedure_with_llm(
            base_procedure=base_procedure,
            aircraft_type="Boeing 737",
            aircraft_model="737-800",
            system="Hydraulic",
            components="Pumps, Reservoirs",
            configuration="Standard configuration",
            regulatory_requirements="FAA regulations",
            special_considerations="None"
        )

        # Verify result
        assert enhanced_procedure is not None
        assert enhanced_procedure["id"] == "maint-001"
        assert enhanced_procedure["title"] == "Enhanced Test Procedure"
        assert len(enhanced_procedure["steps"]) == 1
        assert len(enhanced_procedure["safety_precautions"]) == 1
        assert len(enhanced_procedure["tools_required"]) == 1

        # Verify LLM service was called with correct parameters
        mock_llm_service.generate_response_async.assert_called_once()
        args, kwargs = mock_llm_service.generate_response_async.call_args
        assert kwargs["template_name"] == "maintenance_procedure_enhancement"
        assert kwargs["variables"]["aircraft_type"] == "Boeing 737"
        assert kwargs["variables"]["system"] == "Hydraulic"
        assert "base_procedure" in kwargs["variables"]

    @pytest.mark.asyncio
    async def test_generate_procedure_hybrid_approach(self, agent, mock_maintenance_service, mock_llm_service):
        """
        Test the hybrid approach for generating procedures.
        """
        # Configure mock maintenance service to fail (no template available)
        mock_maintenance_service.generate_procedure.side_effect = FileNotFoundError("No template found")

        # Configure mock LLM service to return a valid procedure
        mock_response = {
            "content": json.dumps({
                "id": "maint-001",
                "title": "Test Procedure",
                "description": "Test procedure description",
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Test Step",
                        "description": "Test step description",
                        "cautions": ["Test caution"]
                    }
                ],
                "safety_precautions": ["Test safety precaution"],
                "tools_required": [
                    {
                        "id": "tool-001",
                        "name": "Test Tool",
                        "specification": "Test specification"
                    }
                ]
            })
        }
        mock_llm_service.generate_response_async.return_value = mock_response

        # Call method
        procedure = await agent.generate_procedure(
            aircraft_type="Boeing 737",
            system="Hydraulic",
            procedure_type="Inspection",
            parameters={
                "aircraft_model": "737-800",
                "components": "Pumps, Reservoirs",
                "configuration": "Standard configuration",
                "regulatory_requirements": "FAA regulations",
                "special_considerations": "None"
            },
            query="Generate a maintenance procedure for inspecting the hydraulic system of a Boeing 737-800"
        )

        # Verify result
        assert procedure is not None
        assert "request" in procedure
        assert "procedure" in procedure
        assert procedure["procedure"]["id"] == "maint-001"
        assert procedure["procedure"]["title"] == "Test Procedure"

        # Verify maintenance service was called
        mock_maintenance_service.generate_procedure.assert_called_once()

        # Verify LLM service was called
        mock_llm_service.generate_response_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_procedure_template_available(self, agent, mock_maintenance_service):
        """
        Test generating a procedure when a template is available.
        """
        # Configure mock maintenance service to return a procedure
        mock_procedure = {
            "request": {
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic",
                "procedure_type": "Inspection",
                "parameters": {}
            },
            "procedure": {
                "id": "maint-001",
                "title": "Hydraulic System Inspection",
                "description": "Procedure for inspecting the hydraulic system",
                "steps": []
            }
        }
        mock_maintenance_service.generate_procedure.return_value = mock_procedure

        # Call method
        procedure = await agent.generate_procedure(
            aircraft_type="Boeing 737",
            system="Hydraulic",
            procedure_type="Inspection",
            parameters={},
            query="Generate a maintenance procedure for inspecting the hydraulic system of a Boeing 737"
        )

        # Verify result
        assert procedure is not None
        assert procedure == mock_procedure

        # Verify maintenance service was called
        mock_maintenance_service.generate_procedure.assert_called_once()

    def test_format_llm_procedure_as_markdown(self, agent):
        """
        Test formatting a procedure as markdown.
        """
        # Create a test procedure
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description",
                    "cautions": ["Test caution"],
                    "notes": ["Test note"],
                    "verification": "Test verification"
                }
            ],
            "safety_precautions": ["Test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "specification": "Test specification"
                }
            ],
            "parts_required": [
                {
                    "id": "part-001",
                    "name": "Test Part",
                    "part_number": "TP-001",
                    "quantity": 2
                }
            ],
            "equipment_required": [
                {
                    "id": "equip-001",
                    "name": "Test Equipment",
                    "specification": "Test specification"
                }
            ],
            "estimated_time_minutes": 90,
            "post_procedure_checks": ["Test check"],
            "references": [
                {
                    "id": "ref-001",
                    "title": "Test Reference",
                    "document_number": "TR-001"
                }
            ]
        }

        # Format the procedure
        markdown = agent._format_llm_procedure_as_markdown(procedure)

        # Verify result
        assert "# Test Procedure" in markdown
        assert "**ID:** maint-001" in markdown
        assert "## Description" in markdown
        assert "Test procedure description" in markdown
        assert "## Safety Precautions" in markdown
        assert "* Test safety precaution" in markdown
        assert "## Tools Required" in markdown
        assert "* **Test Tool**: Test specification" in markdown
        assert "## Parts Required" in markdown
        assert "* **Test Part** (P/N: TP-001): Qty 2" in markdown
        assert "## Equipment Required" in markdown
        assert "* **Test Equipment**: Test specification" in markdown
        assert "**Estimated Time:** 1 hour 30 minutes" in markdown
        assert "## Procedure Steps" in markdown
        assert "### Step 1: Test Step" in markdown
        assert "Test step description" in markdown
        assert "**Cautions:**" in markdown
        assert "* Test caution" in markdown
        assert "**Notes:**" in markdown
        assert "* Test note" in markdown
        assert "**Verification:** Test verification" in markdown
        assert "## Post-Procedure Checks" in markdown
        assert "* Test check" in markdown
        assert "## References" in markdown
        assert "* **Test Reference** (Doc #: TR-001)" in markdown

    def test_enrich_procedure_with_regulatory_info_simple(self, agent):
        """
        Test enriching a procedure with regulatory information using the simple method.
        """
        # Create a test procedure
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
                }
            ],
            "safety_precautions": ["Test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "specification": "Test specification"
                }
            ]
        }

        # Enrich the procedure
        enriched = agent._enrich_procedure_with_regulatory_info(
            procedure=procedure,
            regulatory_requirements="FAA Part 43"
        )

        # Verify result
        assert "This procedure complies with FAA Part 43" in enriched["description"]
        assert "Comply with all FAA Part 43 during this procedure." in enriched["safety_precautions"]
        assert "references" in enriched
        assert len(enriched["references"]) == 1
        assert enriched["references"][0]["title"] == "FAA Part 43 Compliance Documentation"

        # Test with existing references
        procedure_with_refs = procedure.copy()
        procedure_with_refs["references"] = [
            {
                "id": "ref-001",
                "title": "Test Reference",
                "document_number": "TR-001"
            }
        ]

        enriched = agent._enrich_procedure_with_regulatory_info(
            procedure=procedure_with_refs,
            regulatory_requirements="FAA Part 43"
        )

        # Verify result
        assert len(enriched["references"]) == 2
        assert enriched["references"][0]["title"] == "Test Reference"
        assert enriched["references"][1]["title"] == "FAA Part 43 Compliance Documentation"

        # Test with existing regulatory reference
        procedure_with_reg_ref = procedure.copy()
        procedure_with_reg_ref["references"] = [
            {
                "id": "ref-001",
                "title": "FAA Part 43 Compliance Documentation",
                "document_number": "REG-001"
            }
        ]

        enriched = agent._enrich_procedure_with_regulatory_info(
            procedure=procedure_with_reg_ref,
            regulatory_requirements="FAA Part 43"
        )

        # Verify result
        assert len(enriched["references"]) == 1
        assert enriched["references"][0]["title"] == "FAA Part 43 Compliance Documentation"

    def test_enrich_procedure_with_regulatory_info_detailed(self, agent, mock_regulatory_service):
        """
        Test enriching a procedure with regulatory information using the detailed method.
        """
        # Create a test procedure
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
                }
            ],
            "safety_precautions": ["Test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "specification": "Test specification"
                }
            ]
        }

        # Enrich the procedure with detailed information
        enriched = agent._enrich_procedure_with_regulatory_info(
            procedure=procedure,
            regulatory_requirements="FAA and EASA regulations",
            procedure_type="inspection",
            system="hydraulic",
            aircraft_type="Boeing 737",
            aircraft_category="commercial",
            jurisdiction="United States"
        )

        # Verify result
        assert "This procedure complies with FAA and EASA regulations" in enriched["description"]
        assert "Comply with all FAA and EASA regulations during this procedure." in enriched["safety_precautions"]
        assert "references" in enriched
        assert len(enriched["references"]) == 2
        assert "regulatory_compliance" in enriched
        assert len(enriched["regulatory_compliance"]) == 2

        # Verify regulatory service was called
        mock_regulatory_service.get_regulatory_citations.assert_called_once_with(
            procedure_type="inspection",
            system="hydraulic",
            aircraft_type="Boeing 737",
            aircraft_category="commercial",
            jurisdiction="United States"
        )

    @pytest.mark.asyncio
    async def test_validate_procedure_with_regulatory_info(self, agent, mock_regulatory_service):
        """
        Test validating a procedure with regulatory information.
        """
        # Create a test procedure
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
                }
            ],
            "safety_precautions": ["Test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "specification": "Test specification"
                }
            ]
        }

        # Validate the procedure
        result = await agent.validate_procedure(
            procedure=procedure,
            procedure_type="inspection",
            system="hydraulic",
            aircraft_type="Boeing 737",
            aircraft_category="commercial",
            jurisdiction="United States"
        )

        # Verify result
        assert result.success is True
        assert "validated successfully" in result.response
        assert "validation_result" in result.data
        assert result.data["validation_result"] == "passed"
        assert "regulatory_validation" in result.data
        assert "recommendations" in result.data

        # Verify regulatory service was called
        mock_regulatory_service.validate_procedure_against_regulations.assert_called_once_with(
            procedure=procedure,
            procedure_type="inspection",
            system="hydraulic",
            aircraft_type="Boeing 737",
            aircraft_category="commercial",
            jurisdiction="United States"
        )

    @pytest.mark.asyncio
    async def test_validate_procedure_invalid(self, agent, mock_regulatory_service):
        """
        Test validating an invalid procedure.
        """
        # Create an invalid procedure (missing steps)
        procedure = {
            "title": "Test Procedure",
            "description": "Test procedure description"
        }

        # Validate the procedure
        result = await agent.validate_procedure(
            procedure=procedure,
            procedure_type="inspection",
            system="hydraulic"
        )

        # Verify result
        assert result.success is False
        assert "failed validation" in result.response
        assert "validation_errors" in result.data
        assert "Procedure is missing steps" in result.data["validation_errors"]

        # Mock regulatory service to return invalid result
        mock_regulatory_service.validate_procedure_against_regulations.return_value = {
            "valid": False,
            "requirements": ["14 CFR 43.13", "Part-145"],
            "issues": ["Missing required regulatory reference"],
            "recommendations": []
        }

        # Create a procedure with steps but invalid for regulatory requirements
        procedure_with_steps = {
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
                }
            ],
            "safety_precautions": ["Test safety precaution"]
        }

        # Validate the procedure
        result = await agent.validate_procedure(
            procedure=procedure_with_steps,
            procedure_type="inspection",
            system="hydraulic"
        )

        # Verify result
        assert result.success is False
        assert "failed validation" in result.response
        assert "validation_errors" in result.data
        assert any("Regulatory compliance issue" in error for error in result.data["validation_errors"])
