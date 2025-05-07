"""Safety Precautions API endpoints for MAGPIE platform."""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from app.services.safety_precautions_service import SafetyPrecautionsService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_safety_precautions_service():
    """
    Dependency for getting a SafetyPrecautionsService instance.

    Returns:
        SafetyPrecautionsService: An instance of the SafetyPrecautionsService.
    """
    return SafetyPrecautionsService()


@router.get("/safety-precautions", response_model=List[Dict[str, Any]], tags=["safety-precautions"])
def get_safety_precautions(
    precaution_type: Optional[str] = None,
    severity: Optional[str] = None,
    hazard_level: Optional[str] = None,
    service: SafetyPrecautionsService = Depends(get_safety_precautions_service)
):
    """
    Get safety precautions with optional filtering.

    Args:
        precaution_type: Optional type to filter by (precaution, warning, caution, note)
        severity: Optional severity to filter by (low, medium, high, critical)
        hazard_level: Optional hazard level to filter by (information, caution, warning, danger)
        service: SafetyPrecautionsService instance

    Returns:
        List of safety precautions
    """
    try:
        if precaution_type:
            return service.get_safety_precautions_by_type(precaution_type)
        elif severity:
            return service.get_safety_precautions_by_severity(severity)
        elif hazard_level:
            return service.get_safety_precautions_by_hazard_level(hazard_level)
        else:
            return service.get_all_safety_precautions()
    except Exception as e:
        logger.error(f"Error retrieving safety precautions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving safety precautions: {str(e)}"
        )


@router.get("/safety-precautions/{precaution_id}", response_model=Dict[str, Any], tags=["safety-precautions"])
def get_safety_precaution(
    precaution_id: str,
    service: SafetyPrecautionsService = Depends(get_safety_precautions_service)
):
    """
    Get a specific safety precaution by ID.

    Args:
        precaution_id: ID of the safety precaution to retrieve
        service: SafetyPrecautionsService instance

    Returns:
        Safety precaution details
    """
    try:
        precaution = service.get_safety_precaution(precaution_id)
        if not precaution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Safety precaution with ID {precaution_id} not found"
            )
        return precaution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving safety precaution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving safety precaution: {str(e)}"
        )


@router.get("/procedure/{procedure_type}/{system}/safety-precautions", response_model=List[Dict[str, Any]], tags=["safety-precautions"])
def get_safety_precautions_for_procedure(
    procedure_type: str,
    system: str,
    display_location: Optional[str] = None,
    service: SafetyPrecautionsService = Depends(get_safety_precautions_service)
):
    """
    Get safety precautions for a specific procedure type and system.

    Args:
        procedure_type: Type of procedure (e.g., "inspection", "repair")
        system: System being maintained (e.g., "hydraulic", "electrical")
        display_location: Optional location to filter by (e.g., "before_procedure")
        service: SafetyPrecautionsService instance

    Returns:
        List of safety precautions for the specified procedure and system
    """
    try:
        return service.get_safety_precautions_for_procedure(
            procedure_type=procedure_type,
            system=system,
            display_location=display_location
        )
    except Exception as e:
        logger.error(f"Error retrieving safety precautions for procedure: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving safety precautions for procedure: {str(e)}"
        )


@router.get("/step/{procedure_type}/{system}/{step_reference}/safety-precautions", response_model=List[Dict[str, Any]], tags=["safety-precautions"])
def get_safety_precautions_for_step(
    procedure_type: str,
    system: str,
    step_reference: str,
    service: SafetyPrecautionsService = Depends(get_safety_precautions_service)
):
    """
    Get safety precautions for a specific procedure step.

    Args:
        procedure_type: Type of procedure (e.g., "inspection", "repair")
        system: System being maintained (e.g., "hydraulic", "electrical")
        step_reference: Reference to the step (e.g., "preparation")
        service: SafetyPrecautionsService instance

    Returns:
        List of safety precautions for the specified step
    """
    try:
        return service.get_safety_precautions_for_step(
            procedure_type=procedure_type,
            system=system,
            step_reference=step_reference
        )
    except Exception as e:
        logger.error(f"Error retrieving safety precautions for step: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving safety precautions for step: {str(e)}"
        )
