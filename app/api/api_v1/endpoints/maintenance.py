"""Maintenance Procedure Generator endpoints for MAGPIE platform."""

import logging
import os
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from app.core.mock.service import mock_data_service
from app.core.agents.maintenance_agent import MaintenanceAgent
from app.services.maintenance_procedure_template_service import MaintenanceProcedureTemplateService
from app.services.regulatory_requirements_service import RegulatoryRequirementsService
from app.services.tools_and_parts_service import ToolsAndPartsService
from app.services.safety_precautions_service import SafetyPrecautionsService
from app.services.aircraft_configuration_service import AircraftConfigurationService

logger = logging.getLogger(__name__)
router = APIRouter()


class MaintenanceRequest(BaseModel):
    """Maintenance procedure request model."""

    aircraft_type: str
    system: str
    procedure_type: str
    parameters: Dict[str, Any] = {}


class LLMMaintenanceRequest(BaseModel):
    """LLM-based maintenance procedure request model."""

    procedure_type: str = Field(..., description="Type of procedure (inspection, repair, etc.)")
    aircraft_type: str = Field(..., description="Type of aircraft")
    aircraft_model: str = Field(..., description="Specific model of aircraft")
    system: str = Field(..., description="System to perform procedure on")
    components: str = Field("All components", description="Components involved in the procedure")
    configuration: str = Field("Standard configuration", description="Aircraft configuration details")
    regulatory_requirements: str = Field("Standard FAA/EASA regulations", description="Regulatory requirements to follow")
    special_considerations: str = Field("None", description="Special considerations for the procedure")
    use_large_model: bool = Field(False, description="Whether to use the large model for generation")


class TemplateFilterRequest(BaseModel):
    """Request model for filtering maintenance procedure templates."""

    aircraft_categories: Optional[List[str]] = Field(None, description="Filter by aircraft categories")
    pressurization_system_types: Optional[List[str]] = Field(None, description="Filter by pressurization system types")
    engine_types: Optional[List[str]] = Field(None, description="Filter by engine types")


class AircraftConfigRequest(BaseModel):
    """Request model for aircraft configuration parameters."""

    aircraft_model: str = Field(..., description="Aircraft model identifier")
    pressurization_system_type: Optional[str] = Field(None, description="Type of pressurization system")
    pressurization_source_type: Optional[str] = Field(None, description="Source of pressurization")
    engine_type: Optional[str] = Field(None, description="Type of engine")
    has_pressurization: Optional[bool] = Field(None, description="Whether the aircraft has pressurization")
    has_isolation_valves: Optional[bool] = Field(None, description="Whether the aircraft has isolation valves")
    has_auto_pressurization_mode: Optional[bool] = Field(None, description="Whether the aircraft has automatic pressurization mode")
    has_valve_position_indicator: Optional[bool] = Field(None, description="Whether the aircraft has valve position indicators")
    has_audible_warning: Optional[bool] = Field(None, description="Whether the aircraft has audible warnings")
    has_visual_warning: Optional[bool] = Field(None, description="Whether the aircraft has visual warnings")
    has_auto_oxygen_deployment: Optional[bool] = Field(None, description="Whether the aircraft has automatic oxygen deployment")
    has_emergency_descent_mode: Optional[bool] = Field(None, description="Whether the aircraft has emergency descent mode")
    has_separate_negative_relief_valve: Optional[bool] = Field(None, description="Whether the aircraft has a separate negative relief valve")
    max_differential_pressure: Optional[float] = Field(None, description="Maximum differential pressure")
    max_allowable_leak_rate: Optional[float] = Field(None, description="Maximum allowable leak rate")
    safety_valve_type: Optional[str] = Field(None, description="Type of safety valve")
    warning_system_type: Optional[str] = Field(None, description="Type of warning system")
    additional_parameters: Optional[Dict[str, Any]] = Field(default={}, description="Additional configuration parameters")


class TemplateProcedureRequest(BaseModel):
    """Request model for generating a maintenance procedure from a template."""

    template_id: str = Field(..., description="ID of the template to use")
    aircraft_config: AircraftConfigRequest = Field(..., description="Aircraft configuration parameters")
    output_format: str = Field("json", description="Output format (json or markdown)")


def get_maintenance_agent():
    """
    Dependency for getting a MaintenanceAgent instance.

    Returns:
        MaintenanceAgent: An instance of the MaintenanceAgent.
    """
    template_service = MaintenanceProcedureTemplateService()
    regulatory_service = RegulatoryRequirementsService()
    tools_and_parts_service = ToolsAndPartsService()
    safety_precautions_service = SafetyPrecautionsService()
    aircraft_configuration_service = AircraftConfigurationService()
    return MaintenanceAgent(
        template_service=template_service,
        regulatory_service=regulatory_service,
        tools_and_parts_service=tools_and_parts_service,
        safety_precautions_service=safety_precautions_service,
        aircraft_configuration_service=aircraft_configuration_service
    )


def get_regulatory_service():
    """
    Dependency for getting a RegulatoryRequirementsService instance.

    Returns:
        RegulatoryRequirementsService: An instance of the RegulatoryRequirementsService.
    """
    return RegulatoryRequirementsService()


@router.get("/maintenance/aircraft-types", summary="Get Available Aircraft Types", tags=["maintenance"])
async def get_aircraft_types():
    """
    Get a list of available aircraft types for maintenance procedures.

    Returns:
        dict: List of available aircraft types with metadata.
    """
    try:
        # Get aircraft types list from mock data service
        aircraft_types = mock_data_service.get_maintenance_aircraft_types()

        return {
            "status": "success",
            "message": "Aircraft types retrieved successfully",
            "data": aircraft_types,
        }
    except ValueError as e:
        # Mock data is disabled
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        return {
            "status": "success",
            "message": "Aircraft types retrieved successfully",
            "data": [
                {
                    "id": "ac-001",
                    "name": "Boeing 737",
                    "variants": ["737-700", "737-800", "737-900"],
                },
                {
                    "id": "ac-002",
                    "name": "Airbus A320",
                    "variants": ["A320-200", "A320neo"],
                },
                {
                    "id": "ac-003",
                    "name": "Embraer E190",
                    "variants": ["E190-E2"],
                },
            ],
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error retrieving aircraft types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving aircraft types",
        )


@router.get("/maintenance/systems/{aircraft_id}", summary="Get Systems for Aircraft Type", tags=["maintenance"])
async def get_systems(aircraft_id: str):
    """
    Get a list of systems for a specific aircraft type.

    Args:
        aircraft_id: The ID of the aircraft type to get systems for.

    Returns:
        dict: List of systems for the specified aircraft type.

    Raises:
        HTTPException: If aircraft type is not found.
    """
    try:
        # Get systems for aircraft type from mock data service
        systems_data = mock_data_service.get_maintenance_systems(aircraft_id)

        return {
            "status": "success",
            "message": f"Systems for aircraft type {aircraft_id} retrieved successfully",
            "data": systems_data,
        }
    except FileNotFoundError:
        # Aircraft type not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aircraft type with ID {aircraft_id} not found",
        )
    except ValueError as e:
        # Mock data is disabled
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        if aircraft_id not in ["ac-001", "ac-002", "ac-003"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aircraft type with ID {aircraft_id} not found",
            )

        return {
            "status": "success",
            "message": f"Systems for aircraft type {aircraft_id} retrieved successfully",
            "data": {
                "aircraft_id": aircraft_id,
                "aircraft_name": "Boeing 737" if aircraft_id == "ac-001" else "Airbus A320",
                "systems": [
                    {
                        "id": "sys-001",
                        "name": "Hydraulic System",
                        "description": "Aircraft hydraulic system components and functions",
                    },
                    {
                        "id": "sys-002",
                        "name": "Electrical System",
                        "description": "Aircraft electrical system components and functions",
                    },
                    {
                        "id": "sys-003",
                        "name": "Avionics System",
                        "description": "Aircraft avionics system components and functions",
                    },
                ],
            },
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error retrieving systems for aircraft type {aircraft_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving systems for aircraft type {aircraft_id}",
        )


@router.get("/maintenance/procedure-types/{aircraft_id}/{system_id}", summary="Get Procedure Types for System", tags=["maintenance"])
async def get_procedure_types(aircraft_id: str, system_id: str):
    """
    Get a list of procedure types for a specific system.

    Args:
        aircraft_id: The ID of the aircraft type.
        system_id: The ID of the system to get procedure types for.

    Returns:
        dict: List of procedure types for the specified system.

    Raises:
        HTTPException: If aircraft type or system is not found.
    """
    try:
        # Get procedure types for system from mock data service
        procedure_types_data = mock_data_service.get_maintenance_procedure_types(aircraft_id, system_id)

        return {
            "status": "success",
            "message": f"Procedure types for system {system_id} retrieved successfully",
            "data": procedure_types_data,
        }
    except FileNotFoundError:
        # Aircraft type or system not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System with ID {system_id} not found for aircraft type {aircraft_id}",
        )
    except ValueError as e:
        # Mock data is disabled
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        if system_id not in ["sys-001", "sys-002", "sys-003"] or aircraft_id not in ["ac-001", "ac-002", "ac-003"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System with ID {system_id} not found for aircraft type {aircraft_id}",
            )

        return {
            "status": "success",
            "message": f"Procedure types for system {system_id} retrieved successfully",
            "data": {
                "system_id": system_id,
                "system_name": "Hydraulic System" if system_id == "sys-001" else "Electrical System",
                "procedure_types": [
                    {
                        "id": "proc-001",
                        "name": "Inspection",
                        "description": "Visual inspection of components",
                        "interval": "Daily",
                    },
                    {
                        "id": "proc-002",
                        "name": "Functional Test",
                        "description": "Testing system functionality",
                        "interval": "Weekly",
                    },
                    {
                        "id": "proc-003",
                        "name": "Replacement",
                        "description": "Component replacement procedure",
                        "interval": "As needed",
                    },
                ],
            },
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error retrieving procedure types for system {system_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving procedure types for system {system_id}",
        )


@router.post("/maintenance/generate", summary="Generate Maintenance Procedure", tags=["maintenance"])
async def generate_maintenance_procedure(request: MaintenanceRequest):
    """
    Generate a maintenance procedure based on aircraft type, system, and procedure type.

    Args:
        request: Maintenance procedure request with aircraft type, system, procedure type, and parameters.

    Returns:
        dict: Generated maintenance procedure with steps, tools, and safety precautions.
    """
    try:
        # Convert request to dictionary
        request_dict = {
            "aircraft_type": request.aircraft_type,
            "system": request.system,
            "procedure_type": request.procedure_type,
            "parameters": request.parameters,
        }

        # Generate maintenance procedure using mock data service
        procedure_data = mock_data_service.generate_maintenance_procedure(request_dict)

        return {
            "status": "success",
            "message": "Maintenance procedure generated successfully",
            "data": procedure_data,
        }
    except FileNotFoundError:
        # Aircraft type, system, or procedure type not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find procedure for aircraft type {request.aircraft_type}, system {request.system}, procedure type {request.procedure_type}",
        )
    except ValueError as e:
        # Mock data is disabled or invalid request
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        return {
            "status": "success",
            "message": "Maintenance procedure generated successfully",
            "data": {
                "request": {
                    "aircraft_type": request.aircraft_type,
                    "system": request.system,
                    "procedure_type": request.procedure_type,
                    "parameters": request.parameters,
                },
                "procedure": {
                    "id": "maint-001",
                    "title": f"{request.procedure_type} Procedure for {request.system}",
                    "description": f"This procedure provides instructions for performing {request.procedure_type} on the {request.system} of {request.aircraft_type} aircraft.",
                    "estimated_time": "2 hours",
                    "skill_level": "Technician Level 2",
                    "safety_precautions": [
                        "Ensure aircraft is properly grounded",
                        "Wear appropriate personal protective equipment",
                        "Follow all safety protocols in the maintenance manual",
                    ],
                    "tools_required": [
                        {
                            "id": "tool-001",
                            "name": "Socket Set",
                            "specification": "Standard, 10-19mm",
                        },
                        {
                            "id": "tool-002",
                            "name": "Torque Wrench",
                            "specification": "Calibrated, 5-50 Nm",
                        },
                        {
                            "id": "tool-003",
                            "name": "Multimeter",
                            "specification": "Digital, CAT III 600V",
                        },
                    ],
                    "parts_required": [
                        {
                            "id": "part-001",
                            "name": "O-ring",
                            "part_number": "OR-123-456",
                            "quantity": 2,
                        },
                        {
                            "id": "part-002",
                            "name": "Hydraulic Fluid",
                            "part_number": "HF-789-012",
                            "quantity": 1,
                        },
                    ],
                    "steps": [
                        {
                            "step_number": 1,
                            "title": "Preparation",
                            "description": "Gather all necessary tools and parts. Ensure aircraft is in a safe state for maintenance.",
                            "cautions": ["Verify aircraft power is off"],
                            "images": [],
                        },
                        {
                            "step_number": 2,
                            "title": "Access Panel Removal",
                            "description": "Remove access panel to gain access to the system components.",
                            "cautions": ["Support panel during removal"],
                            "images": [],
                        },
                        {
                            "step_number": 3,
                            "title": "Component Inspection",
                            "description": "Inspect components for damage, wear, or leakage.",
                            "cautions": ["Document any findings"],
                            "images": [],
                        },
                        {
                            "step_number": 4,
                            "title": "Functional Testing",
                            "description": "Perform functional tests to verify system operation.",
                            "cautions": ["Follow test procedures exactly"],
                            "images": [],
                        },
                        {
                            "step_number": 5,
                            "title": "Reassembly",
                            "description": "Reinstall access panel and secure all fasteners.",
                            "cautions": ["Torque fasteners to specified values"],
                            "images": [],
                        },
                        {
                            "step_number": 6,
                            "title": "Documentation",
                            "description": "Complete maintenance records and documentation.",
                            "cautions": ["Ensure all work is properly documented"],
                            "images": [],
                        },
                    ],
                    "references": [
                        {
                            "id": "ref-001",
                            "type": "manual",
                            "title": "Aircraft Maintenance Manual",
                            "section": "Chapter 29 - Hydraulic Power",
                        },
                        {
                            "id": "ref-002",
                            "type": "service_bulletin",
                            "title": "Service Bulletin SB-123-456",
                            "date": "2025-01-15",
                        },
                    ],
                },
            },
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error generating maintenance procedure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating maintenance procedure",
        )


@router.get("/maintenance/templates", summary="Get Available Maintenance Procedure Templates", tags=["maintenance"])
async def get_templates(
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Get a list of available maintenance procedure templates.

    Returns:
        dict: List of available maintenance procedure templates.
    """
    try:
        result = await agent.get_available_templates()

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.response
            )

        return {
            "status": "success",
            "message": result.response,
            "data": result.data
        }
    except Exception as e:
        logger.error(f"Error retrieving maintenance procedure templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving maintenance procedure templates"
        )


@router.post("/maintenance/templates/filter", summary="Filter Maintenance Procedure Templates", tags=["maintenance"])
async def filter_templates(
    filter_request: TemplateFilterRequest,
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Filter maintenance procedure templates by criteria.

    Args:
        filter_request: Filter criteria for maintenance procedure templates.

    Returns:
        dict: List of matching maintenance procedure templates.
    """
    try:
        # Convert request to criteria dictionary
        criteria = {}

        if filter_request.aircraft_categories:
            criteria["applicability.aircraft_categories"] = filter_request.aircraft_categories

        if filter_request.pressurization_system_types:
            criteria["applicability.pressurization_system_types"] = filter_request.pressurization_system_types

        if filter_request.engine_types:
            criteria["applicability.engine_types"] = filter_request.engine_types

        result = await agent.get_available_templates(criteria)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.response
            )

        return {
            "status": "success",
            "message": result.response,
            "data": result.data
        }
    except Exception as e:
        logger.error(f"Error filtering maintenance procedure templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error filtering maintenance procedure templates"
        )


@router.get("/maintenance/templates/{template_id}", summary="Get Maintenance Procedure Template Details", tags=["maintenance"])
async def get_template_details(
    template_id: str,
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Get detailed information about a specific maintenance procedure template.

    Args:
        template_id: ID of the template to retrieve.

    Returns:
        dict: Detailed information about the maintenance procedure template.
    """
    try:
        result = await agent.get_template_details(template_id)

        if not result.success:
            if "couldn't find" in result.response.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.response
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.response
                )

        return {
            "status": "success",
            "message": result.response,
            "data": result.data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving template details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving template details"
        )


@router.post("/maintenance/templates/generate", summary="Generate Maintenance Procedure from Template", tags=["maintenance"])
async def generate_procedure_from_template(
    request: TemplateProcedureRequest,
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Generate a customized maintenance procedure based on a template and aircraft configuration.

    Args:
        request: Template procedure request with template ID and aircraft configuration.

    Returns:
        dict: Generated maintenance procedure.
    """
    try:
        # Convert request to dictionary
        aircraft_config = request.aircraft_config.model_dump(exclude_none=True)

        # Add additional parameters if any
        if request.aircraft_config.additional_parameters:
            aircraft_config.update(request.aircraft_config.additional_parameters)

        # Remove additional_parameters key
        if "additional_parameters" in aircraft_config:
            del aircraft_config["additional_parameters"]

        result = await agent.generate_procedure_from_template(
            template_id=request.template_id,
            aircraft_config=aircraft_config,
            output_format=request.output_format
        )

        if not result.success:
            if "couldn't find" in result.response.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.response
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.response
                )

        return {
            "status": "success",
            "message": result.response,
            "data": result.data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating procedure from template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating procedure from template"
        )


@router.post("/maintenance/templates/validate", summary="Validate Maintenance Procedure", tags=["maintenance"])
async def validate_procedure(
    procedure: Dict[str, Any],
    procedure_type: Optional[str] = Query(None, description="Type of procedure"),
    system: Optional[str] = Query(None, description="System being maintained"),
    aircraft_type: Optional[str] = Query(None, description="Aircraft type"),
    aircraft_category: Optional[str] = Query(None, description="Aircraft category"),
    jurisdiction: Optional[str] = Query(None, description="Jurisdiction"),
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Validate a maintenance procedure against regulatory requirements.

    Args:
        procedure: The procedure to validate.
        procedure_type: Type of procedure (optional).
        system: System being maintained (optional).
        aircraft_type: Aircraft type (optional).
        aircraft_category: Aircraft category (optional).
        jurisdiction: Jurisdiction (optional).

    Returns:
        dict: Validation results.
    """
    try:
        result = await agent.validate_procedure(
            procedure=procedure,
            procedure_type=procedure_type,
            system=system,
            aircraft_type=aircraft_type,
            aircraft_category=aircraft_category,
            jurisdiction=jurisdiction
        )

        return {
            "status": "success" if result.success else "error",
            "message": result.response,
            "data": result.data
        }
    except Exception as e:
        logger.error(f"Error validating procedure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating procedure"
        )


@router.post("/maintenance/generate-with-llm", summary="Generate Maintenance Procedure with LLM", tags=["maintenance"])
async def generate_procedure_with_llm(
    request: LLMMaintenanceRequest,
    format_type: str = "json",
    enrich_regulatory: bool = False,
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Generate a maintenance procedure using LLM.

    Args:
        request: LLM-based maintenance procedure request with procedure details.
        format_type: Format type (json, markdown)
        enrich_regulatory: Whether to enrich the procedure with regulatory information

    Returns:
        dict: Generated maintenance procedure.
    """
    try:
        # Determine model size based on request
        from app.services.llm_service import ModelSize
        model_size = ModelSize.LARGE if request.use_large_model else ModelSize.MEDIUM

        # Generate procedure using LLM
        procedure_result = agent.generate_procedure_with_llm(
            procedure_type=request.procedure_type,
            aircraft_type=request.aircraft_type,
            aircraft_model=request.aircraft_model,
            system=request.system,
            components=request.components,
            configuration=request.configuration,
            regulatory_requirements=request.regulatory_requirements,
            special_considerations=request.special_considerations,
            model_size=model_size
        )

        # Handle both sync and async results for testing
        if hasattr(procedure_result, "__await__"):
            procedure = await procedure_result
        else:
            procedure = procedure_result

        if not procedure:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate procedure with LLM"
            )

        # Enrich with regulatory information if requested
        if enrich_regulatory:
            enriched_procedure = agent._enrich_procedure_with_regulatory_info(
                procedure=procedure,
                regulatory_requirements=request.regulatory_requirements
            )
            # Handle both sync and async results for testing
            if hasattr(enriched_procedure, "__await__"):
                procedure = await enriched_procedure
            else:
                procedure = enriched_procedure

        # Format the procedure if markdown is requested
        if format_type.lower() == "markdown":
            formatted_procedure = agent._format_llm_procedure_as_markdown(procedure)
            # Handle both sync and async results for testing
            if hasattr(formatted_procedure, "__await__"):
                formatted_procedure = await formatted_procedure
            else:
                formatted_procedure = formatted_procedure

            return {
                "status": "success",
                "message": "Maintenance procedure generated successfully with LLM",
                "data": {
                    "request": request.model_dump(),
                    "format": "markdown",
                    "procedure": formatted_procedure
                }
            }
        else:  # Default to JSON
            return {
                "status": "success",
                "message": "Maintenance procedure generated successfully with LLM",
                "data": {
                    "request": request.model_dump(),
                    "format": "json",
                    "procedure": procedure
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating procedure with LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating procedure with LLM"
        )


@router.post("/maintenance/generate-hybrid", summary="Generate Maintenance Procedure with Hybrid Approach", tags=["maintenance"])
async def generate_procedure_hybrid(
    request: MaintenanceRequest,
    format_type: str = "json",
    enrich_regulatory: bool = False,
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Generate a maintenance procedure using a hybrid approach (template-based or LLM-based).

    Args:
        request: Maintenance procedure request with aircraft type, system, procedure type, and parameters.
        format_type: Format type (json, markdown)
        enrich_regulatory: Whether to enrich the procedure with regulatory information

    Returns:
        dict: Generated maintenance procedure.
    """
    try:
        # Generate procedure using hybrid approach
        result_obj = agent.generate_procedure(
            aircraft_type=request.aircraft_type,
            system=request.system,
            procedure_type=request.procedure_type,
            parameters=request.parameters,
            query=f"Generate a {request.procedure_type} procedure for {request.system} system on {request.aircraft_type}"
        )

        # Handle both sync and async results for testing
        if hasattr(result_obj, "__await__"):
            result = await result_obj
        else:
            result = result_obj

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate procedure"
            )

        # Extract the procedure from the result
        procedure = result.get("procedure")
        if not procedure:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract procedure from result"
            )

        # Enrich with regulatory information if requested
        regulatory_requirements = request.parameters.get("regulatory_requirements", "Standard FAA/EASA regulations")
        if enrich_regulatory and regulatory_requirements:
            enriched_procedure = agent._enrich_procedure_with_regulatory_info(
                procedure=procedure,
                regulatory_requirements=regulatory_requirements
            )
            # Handle both sync and async results for testing
            if hasattr(enriched_procedure, "__await__"):
                procedure = await enriched_procedure
            else:
                procedure = enriched_procedure

        # Format the procedure if markdown is requested
        if format_type.lower() == "markdown":
            formatted_procedure = agent._format_llm_procedure_as_markdown(procedure)
            # Handle both sync and async results for testing
            if hasattr(formatted_procedure, "__await__"):
                formatted_procedure = await formatted_procedure
            else:
                formatted_procedure = formatted_procedure

            return {
                "status": "success",
                "message": "Maintenance procedure generated successfully with hybrid approach",
                "data": {
                    "request": {
                        "aircraft_type": request.aircraft_type,
                        "system": request.system,
                        "procedure_type": request.procedure_type,
                        "parameters": request.parameters
                    },
                    "format": "markdown",
                    "procedure": formatted_procedure,
                    "generation_method": "template" if "template_id" in procedure else "llm"
                }
            }
        else:  # Default to JSON
            return {
                "status": "success",
                "message": "Maintenance procedure generated successfully with hybrid approach",
                "data": {
                    "request": {
                        "aircraft_type": request.aircraft_type,
                        "system": request.system,
                        "procedure_type": request.procedure_type,
                        "parameters": request.parameters
                    },
                    "format": "json",
                    "procedure": procedure,
                    "generation_method": "template" if "template_id" in procedure else "llm"
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating procedure with hybrid approach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating procedure with hybrid approach"
        )


@router.post("/maintenance/enhance-with-llm", summary="Enhance Maintenance Procedure with LLM", tags=["maintenance"])
async def enhance_procedure_with_llm(
    base_procedure: Dict[str, Any],
    aircraft_type: str,
    aircraft_model: str,
    system: str,
    components: str = "All components",
    configuration: str = "Standard configuration",
    regulatory_requirements: str = "Standard FAA/EASA regulations",
    special_considerations: str = "None",
    use_large_model: bool = False,
    format_type: str = "json",
    enrich_regulatory: bool = False,
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Enhance a template-based procedure with LLM.

    Args:
        base_procedure: Base procedure to enhance
        aircraft_type: Type of aircraft
        aircraft_model: Specific model of aircraft
        system: System to perform procedure on
        components: Components involved in the procedure
        configuration: Aircraft configuration details
        regulatory_requirements: Regulatory requirements to follow
        special_considerations: Special considerations for the procedure
        use_large_model: Whether to use the large model for enhancement
        format_type: Format type (json, markdown)
        enrich_regulatory: Whether to enrich the procedure with regulatory information

    Returns:
        dict: Enhanced maintenance procedure.
    """
    try:
        # Determine model size based on request
        from app.services.llm_service import ModelSize
        model_size = ModelSize.LARGE if use_large_model else ModelSize.MEDIUM

        # Enhance procedure using LLM
        procedure_result = agent.enhance_procedure_with_llm(
            base_procedure=base_procedure,
            aircraft_type=aircraft_type,
            aircraft_model=aircraft_model,
            system=system,
            components=components,
            configuration=configuration,
            regulatory_requirements=regulatory_requirements,
            special_considerations=special_considerations,
            model_size=model_size
        )

        # Handle both sync and async results for testing
        if hasattr(procedure_result, "__await__"):
            enhanced_procedure = await procedure_result
        else:
            enhanced_procedure = procedure_result

        if not enhanced_procedure:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enhance procedure with LLM"
            )

        # Enrich with regulatory information if requested
        if enrich_regulatory:
            enriched_procedure = agent._enrich_procedure_with_regulatory_info(
                procedure=enhanced_procedure,
                regulatory_requirements=regulatory_requirements
            )
            # Handle both sync and async results for testing
            if hasattr(enriched_procedure, "__await__"):
                enhanced_procedure = await enriched_procedure
            else:
                enhanced_procedure = enriched_procedure

        # Format the procedure if markdown is requested
        if format_type.lower() == "markdown":
            formatted_procedure = agent._format_llm_procedure_as_markdown(enhanced_procedure)
            # Handle both sync and async results for testing
            if hasattr(formatted_procedure, "__await__"):
                formatted_procedure = await formatted_procedure
            else:
                formatted_procedure = formatted_procedure

            return {
                "status": "success",
                "message": "Maintenance procedure enhanced successfully with LLM",
                "data": {
                    "request": {
                        "aircraft_type": aircraft_type,
                        "aircraft_model": aircraft_model,
                        "system": system,
                        "components": components,
                        "configuration": configuration,
                        "regulatory_requirements": regulatory_requirements,
                        "special_considerations": special_considerations
                    },
                    "format": "markdown",
                    "procedure": formatted_procedure
                }
            }
        else:  # Default to JSON
            return {
                "status": "success",
                "message": "Maintenance procedure enhanced successfully with LLM",
                "data": {
                    "request": {
                        "aircraft_type": aircraft_type,
                        "aircraft_model": aircraft_model,
                        "system": system,
                        "components": components,
                        "configuration": configuration,
                        "regulatory_requirements": regulatory_requirements,
                        "special_considerations": special_considerations
                    },
                    "format": "json",
                    "procedure": enhanced_procedure
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing procedure with LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error enhancing procedure with LLM"
        )


@router.post("/maintenance/format-procedure", summary="Format Maintenance Procedure", tags=["maintenance"])
async def format_procedure(
    procedure: Dict[str, Any],
    format_type: str = "json",
    enrich_regulatory: bool = False,
    regulatory_requirements: Optional[str] = None,
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Format a maintenance procedure in different formats.

    Args:
        procedure: The procedure to format
        format_type: Format type (json, markdown)
        enrich_regulatory: Whether to enrich the procedure with regulatory information
        regulatory_requirements: Regulatory requirements to add if enriching

    Returns:
        dict: Formatted maintenance procedure.
    """
    try:
        # Validate the procedure
        validation_result = agent._validate_llm_procedure(procedure)
        # Handle both sync and async results for testing
        if hasattr(validation_result, "__await__"):
            validation_result = await validation_result

        if not validation_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid procedure format"
            )

        # Enrich with regulatory information if requested
        if enrich_regulatory and regulatory_requirements:
            enriched_procedure = agent._enrich_procedure_with_regulatory_info(
                procedure=procedure,
                regulatory_requirements=regulatory_requirements
            )
            # Handle both sync and async results for testing
            if hasattr(enriched_procedure, "__await__"):
                procedure = await enriched_procedure
            else:
                procedure = enriched_procedure

        # Format the procedure
        if format_type.lower() == "markdown":
            formatted_procedure = agent._format_llm_procedure_as_markdown(procedure)
            # Handle both sync and async results for testing
            if hasattr(formatted_procedure, "__await__"):
                formatted_procedure = await formatted_procedure

            return {
                "status": "success",
                "message": "Maintenance procedure formatted successfully",
                "data": {
                    "format": "markdown",
                    "procedure": formatted_procedure
                }
            }
        else:  # Default to JSON
            return {
                "status": "success",
                "message": "Maintenance procedure formatted successfully",
                "data": {
                    "format": "json",
                    "procedure": procedure
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error formatting procedure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error formatting procedure"
        )


@router.post("/maintenance/templates/save", summary="Save Maintenance Procedure", tags=["maintenance"])
async def save_procedure(
    procedure: Dict[str, Any],
    output_dir: Optional[str] = None,
    agent: MaintenanceAgent = Depends(get_maintenance_agent)
):
    """
    Save a maintenance procedure to a file.

    Args:
        procedure: The procedure to save.
        output_dir: Optional output directory.

    Returns:
        dict: Save result.
    """
    try:
        result = await agent.save_procedure(procedure, output_dir)

        return {
            "status": "success" if result.success else "error",
            "message": result.response,
            "data": result.data
        }
    except Exception as e:
        logger.error(f"Error saving procedure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving procedure"
        )


@router.get("/maintenance/regulatory-requirements", summary="Get Regulatory Requirements", tags=["maintenance"])
async def get_regulatory_requirements(
    authority: Optional[str] = Query(None, description="Filter by regulatory authority (e.g., FAA, EASA)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    aircraft_type: Optional[str] = Query(None, description="Filter by aircraft type"),
    aircraft_category: Optional[str] = Query(None, description="Filter by aircraft category"),
    operation_category: Optional[str] = Query(None, description="Filter by operation category"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    regulatory_service: RegulatoryRequirementsService = Depends(get_regulatory_service)
):
    """
    Get regulatory requirements with optional filtering.

    Args:
        authority: Filter by regulatory authority (e.g., FAA, EASA).
        tag: Filter by tag.
        aircraft_type: Filter by aircraft type.
        aircraft_category: Filter by aircraft category.
        operation_category: Filter by operation category.
        jurisdiction: Filter by jurisdiction.

    Returns:
        dict: List of regulatory requirements.
    """
    try:
        if authority:
            requirements = regulatory_service.get_requirements_by_authority(authority)
        elif tag:
            requirements = regulatory_service.get_requirements_by_tags([tag])
        elif any([aircraft_type, aircraft_category, operation_category, jurisdiction]):
            requirements = regulatory_service.get_requirements_by_applicability(
                aircraft_type=aircraft_type,
                aircraft_category=aircraft_category,
                operation_category=operation_category,
                jurisdiction=jurisdiction
            )
        else:
            requirements = regulatory_service.get_all_requirements()

        return {
            "status": "success",
            "message": "Regulatory requirements retrieved successfully",
            "data": requirements
        }
    except Exception as e:
        logger.error(f"Error retrieving regulatory requirements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving regulatory requirements"
        )


@router.get("/maintenance/regulatory-requirements/{requirement_id}", summary="Get Regulatory Requirement by ID", tags=["maintenance"])
async def get_regulatory_requirement(
    requirement_id: str,
    regulatory_service: RegulatoryRequirementsService = Depends(get_regulatory_service)
):
    """
    Get a specific regulatory requirement by ID.

    Args:
        requirement_id: The ID of the regulatory requirement to retrieve.

    Returns:
        dict: The regulatory requirement.
    """
    try:
        requirement = regulatory_service.get_requirement(requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Regulatory requirement with ID {requirement_id} not found"
            )

        return {
            "status": "success",
            "message": f"Regulatory requirement {requirement_id} retrieved successfully",
            "data": requirement
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving regulatory requirement {requirement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving regulatory requirement {requirement_id}"
        )


@router.get("/maintenance/regulatory-requirements/task/{procedure_type}/{system}", summary="Get Regulatory Requirements for Task", tags=["maintenance"])
async def get_regulatory_requirements_for_task(
    procedure_type: str,
    system: str,
    aircraft_type: Optional[str] = Query(None, description="Aircraft type"),
    aircraft_category: Optional[str] = Query(None, description="Aircraft category"),
    jurisdiction: Optional[str] = Query(None, description="Jurisdiction"),
    regulatory_service: RegulatoryRequirementsService = Depends(get_regulatory_service)
):
    """
    Get regulatory requirements for a specific maintenance task.

    Args:
        procedure_type: Type of procedure (e.g., "inspection", "repair").
        system: System being maintained (e.g., "fuel_system", "avionics").
        aircraft_type: Aircraft type (optional).
        aircraft_category: Aircraft category (optional).
        jurisdiction: Jurisdiction (optional).

    Returns:
        dict: List of applicable regulatory requirements.
    """
    try:
        requirements = regulatory_service.get_requirements_for_task(
            procedure_type=procedure_type,
            system=system,
            aircraft_type=aircraft_type,
            aircraft_category=aircraft_category,
            jurisdiction=jurisdiction
        )

        return {
            "status": "success",
            "message": f"Regulatory requirements for {procedure_type} of {system} retrieved successfully",
            "data": requirements
        }
    except Exception as e:
        logger.error(f"Error retrieving regulatory requirements for task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving regulatory requirements for task"
        )


@router.get("/maintenance/aircraft-configuration/{aircraft_type}", summary="Get Aircraft Configuration", tags=["maintenance"])
async def get_aircraft_configuration(
    aircraft_type: str,
    aircraft_config_service: AircraftConfigurationService = Depends(lambda: AircraftConfigurationService())
):
    """
    Get configuration for a specific aircraft type.

    Args:
        aircraft_type: The aircraft type to get configuration for.

    Returns:
        dict: Aircraft configuration data.
    """
    try:
        configuration = aircraft_config_service.get_aircraft_configuration(aircraft_type)
        if "error" in configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=configuration["error"]
            )

        return {
            "status": "success",
            "message": f"Aircraft configuration for {aircraft_type} retrieved successfully",
            "data": configuration
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving aircraft configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving aircraft configuration: {str(e)}"
        )


@router.get("/maintenance/aircraft-configuration/types", summary="Get All Aircraft Types", tags=["maintenance"])
async def get_all_aircraft_types(
    aircraft_config_service: AircraftConfigurationService = Depends(lambda: AircraftConfigurationService())
):
    """
    Get all available aircraft types.

    Returns:
        dict: List of all aircraft types.
    """
    try:
        aircraft_types = aircraft_config_service.get_all_aircraft_types()

        return {
            "status": "success",
            "message": "Aircraft types retrieved successfully",
            "data": aircraft_types
        }
    except Exception as e:
        logger.error(f"Error retrieving aircraft types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving aircraft types: {str(e)}"
        )


@router.get("/maintenance/aircraft-configuration/{aircraft_type}/systems", summary="Get Systems for Aircraft Type", tags=["maintenance"])
async def get_systems_for_aircraft_type(
    aircraft_type: str,
    aircraft_config_service: AircraftConfigurationService = Depends(lambda: AircraftConfigurationService())
):
    """
    Get systems for a specific aircraft type.

    Args:
        aircraft_type: The aircraft type to get systems for.

    Returns:
        dict: List of systems for the specified aircraft type.
    """
    try:
        systems = aircraft_config_service.get_systems_for_aircraft_type(aircraft_type)
        if not systems:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No systems found for aircraft type {aircraft_type}"
            )

        return {
            "status": "success",
            "message": f"Systems for aircraft type {aircraft_type} retrieved successfully",
            "data": systems
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving systems for aircraft type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving systems for aircraft type: {str(e)}"
        )


@router.get("/maintenance/aircraft-configuration/{aircraft_type}/systems/{system}/procedure-types", summary="Get Procedure Types for System", tags=["maintenance"])
async def get_procedure_types_for_system(
    aircraft_type: str,
    system: str,
    aircraft_config_service: AircraftConfigurationService = Depends(lambda: AircraftConfigurationService())
):
    """
    Get procedure types for a specific aircraft system.

    Args:
        aircraft_type: The aircraft type.
        system: The system to get procedure types for.

    Returns:
        dict: List of procedure types for the specified system.
    """
    try:
        procedure_types = aircraft_config_service.get_procedure_types_for_system(
            aircraft_type=aircraft_type,
            system=system
        )
        if not procedure_types:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No procedure types found for system {system} on aircraft type {aircraft_type}"
            )

        return {
            "status": "success",
            "message": f"Procedure types for system {system} on aircraft type {aircraft_type} retrieved successfully",
            "data": procedure_types
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving procedure types for system: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving procedure types for system: {str(e)}"
        )