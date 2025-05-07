"""Tools and Parts API endpoints for MAGPIE platform."""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from app.services.tools_and_parts_service import ToolsAndPartsService

logger = logging.getLogger(__name__)
router = APIRouter()


class ResourceRequest(BaseModel):
    """Request model for resource queries."""
    
    aircraft_type: Optional[str] = Field(None, description="Aircraft type (e.g., 'Boeing 737')")
    system: Optional[str] = Field(None, description="Aircraft system (e.g., 'hydraulic')")
    procedure_type: Optional[str] = Field(None, description="Procedure type (e.g., 'inspection')")
    specific_procedure: Optional[str] = Field(None, description="Specific procedure name")
    format: str = Field("json", description="Output format (json or markdown)")


def get_tools_and_parts_service():
    """
    Dependency for getting a ToolsAndPartsService instance.

    Returns:
        ToolsAndPartsService: An instance of the ToolsAndPartsService.
    """
    return ToolsAndPartsService()


@router.get("/tools", response_model=List[Dict[str, Any]], tags=["tools-and-parts"])
def get_tools(
    category: Optional[str] = None,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get all tools or tools by category.

    Args:
        category: Optional category to filter by
        service: ToolsAndPartsService instance

    Returns:
        List of tools
    """
    if category:
        return service.get_tools_by_category(category)
    else:
        return service.get_all_tools()


@router.get("/tools/{tool_id}", response_model=Dict[str, Any], tags=["tools-and-parts"])
def get_tool(
    tool_id: str,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get a specific tool by ID.

    Args:
        tool_id: ID of the tool to retrieve
        service: ToolsAndPartsService instance

    Returns:
        Tool details
    """
    tool = service.get_tool(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with ID {tool_id} not found"
        )
    return tool


@router.get("/parts", response_model=List[Dict[str, Any]], tags=["tools-and-parts"])
def get_parts(
    category: Optional[str] = None,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get all parts or parts by category.

    Args:
        category: Optional category to filter by
        service: ToolsAndPartsService instance

    Returns:
        List of parts
    """
    if category:
        return service.get_parts_by_category(category)
    else:
        return service.get_all_parts()


@router.get("/parts/{part_id}", response_model=Dict[str, Any], tags=["tools-and-parts"])
def get_part(
    part_id: str,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get a specific part by ID.

    Args:
        part_id: ID of the part to retrieve
        service: ToolsAndPartsService instance

    Returns:
        Part details
    """
    part = service.get_part(part_id)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part with ID {part_id} not found"
        )
    return part


@router.get("/equipment", response_model=List[Dict[str, Any]], tags=["tools-and-parts"])
def get_equipment(
    category: Optional[str] = None,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get all equipment or equipment by category.

    Args:
        category: Optional category to filter by
        service: ToolsAndPartsService instance

    Returns:
        List of equipment
    """
    if category:
        return service.get_equipment_by_category(category)
    else:
        return service.get_all_equipment()


@router.get("/equipment/{equipment_id}", response_model=Dict[str, Any], tags=["tools-and-parts"])
def get_equipment_item(
    equipment_id: str,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get a specific equipment item by ID.

    Args:
        equipment_id: ID of the equipment to retrieve
        service: ToolsAndPartsService instance

    Returns:
        Equipment details
    """
    equipment = service.get_equipment(equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment with ID {equipment_id} not found"
        )
    return equipment


@router.get("/aircraft/{aircraft_type}/tools", response_model=List[Dict[str, Any]], tags=["tools-and-parts"])
def get_aircraft_tools(
    aircraft_type: str,
    system: str,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get tools for a specific aircraft system.

    Args:
        aircraft_type: Type of aircraft (e.g., "Boeing 737")
        system: Aircraft system (e.g., "hydraulic")
        service: ToolsAndPartsService instance

    Returns:
        List of tools for the specified aircraft system
    """
    return service.get_tools_for_aircraft_system(aircraft_type, system)


@router.get("/aircraft/{aircraft_type}/parts", response_model=List[Dict[str, Any]], tags=["tools-and-parts"])
def get_aircraft_parts(
    aircraft_type: str,
    system: str,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get parts for a specific aircraft system.

    Args:
        aircraft_type: Type of aircraft (e.g., "Boeing 737")
        system: Aircraft system (e.g., "hydraulic")
        service: ToolsAndPartsService instance

    Returns:
        List of parts for the specified aircraft system
    """
    return service.get_parts_for_aircraft_system(aircraft_type, system)


@router.post("/procedure/resources", tags=["tools-and-parts"])
def get_procedure_resources(
    request: ResourceRequest,
    service: ToolsAndPartsService = Depends(get_tools_and_parts_service)
):
    """
    Get resources (tools, parts, equipment) for a specific maintenance procedure.

    Args:
        request: Resource request parameters
        service: ToolsAndPartsService instance

    Returns:
        Dictionary with tools, parts, and equipment for the procedure
    """
    return service.get_resources_for_procedure(
        procedure_type=request.procedure_type,
        system=request.system,
        aircraft_type=request.aircraft_type,
        specific_procedure=request.specific_procedure
    )
