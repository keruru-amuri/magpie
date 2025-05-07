"""Troubleshooting Advisor endpoints for MAGPIE platform."""

import logging
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.mock.service import mock_data_service

logger = logging.getLogger(__name__)
router = APIRouter()


class TroubleshootingRequest(BaseModel):
    """Troubleshooting request model."""

    system: str
    symptoms: List[str]
    context: str = ""


@router.get("/troubleshooting/systems", summary="Get Available Systems", tags=["troubleshooting"])
async def get_systems():
    """
    Get a list of available systems for troubleshooting.

    Returns:
        dict: List of available systems with metadata.
    """
    try:
        # Get systems list from mock data service
        systems = mock_data_service.get_troubleshooting_systems()

        return {
            "status": "success",
            "message": "Systems retrieved successfully",
            "data": systems,
        }
    except ValueError as e:
        # Mock data is disabled
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        return {
            "status": "success",
            "message": "Systems retrieved successfully",
            "data": [
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
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error retrieving systems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving systems",
        )


@router.get("/troubleshooting/symptoms/{system_id}", summary="Get Symptoms for System", tags=["troubleshooting"])
async def get_symptoms(system_id: str):
    """
    Get a list of common symptoms for a specific system.

    Args:
        system_id: The ID of the system to get symptoms for.

    Returns:
        dict: List of common symptoms for the specified system.

    Raises:
        HTTPException: If system is not found.
    """
    try:
        # Get symptoms for system from mock data service
        system_data = mock_data_service.get_troubleshooting_symptoms(system_id)

        return {
            "status": "success",
            "message": f"Symptoms for system {system_id} retrieved successfully",
            "data": system_data,
        }
    except FileNotFoundError:
        # System not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System with ID {system_id} not found",
        )
    except ValueError as e:
        # Mock data is disabled
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        if system_id not in ["sys-001", "sys-002", "sys-003"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System with ID {system_id} not found",
            )

        return {
            "status": "success",
            "message": f"Symptoms for system {system_id} retrieved successfully",
            "data": {
                "system_id": system_id,
                "system_name": "Hydraulic System" if system_id == "sys-001" else "Electrical System",
                "symptoms": [
                    {
                        "id": "sym-001",
                        "description": "Pressure fluctuation",
                        "severity": "medium",
                    } if system_id == "sys-001" else {
                        "id": "sym-004",
                        "description": "Circuit breaker tripping",
                        "severity": "high",
                    },
                    {
                        "id": "sym-002",
                        "description": "Fluid leakage",
                        "severity": "high",
                    } if system_id == "sys-001" else {
                        "id": "sym-005",
                        "description": "Intermittent power loss",
                        "severity": "medium",
                    },
                    {
                        "id": "sym-003",
                        "description": "Slow actuator response",
                        "severity": "low",
                    } if system_id == "sys-001" else {
                        "id": "sym-006",
                        "description": "Unusual noise from electrical components",
                        "severity": "low",
                    },
                ],
            },
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error retrieving symptoms for system {system_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving symptoms for system {system_id}",
        )


@router.post("/troubleshooting/analyze", summary="Analyze Troubleshooting Case", tags=["troubleshooting"])
async def analyze_troubleshooting(request: TroubleshootingRequest):
    """
    Analyze a troubleshooting case based on system and symptoms.

    Args:
        request: Troubleshooting request with system, symptoms, and context.

    Returns:
        dict: Analysis results with potential causes and solutions.
    """
    try:
        # Convert request to dictionary
        request_dict = {
            "system": request.system,
            "symptoms": request.symptoms,
            "context": request.context,
        }

        # Analyze troubleshooting case using mock data service
        analysis_results = mock_data_service.analyze_troubleshooting(request_dict)

        return {
            "status": "success",
            "message": "Troubleshooting analysis completed successfully",
            "data": analysis_results,
        }
    except FileNotFoundError:
        # System not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System with ID {request.system} not found",
        )
    except ValueError as e:
        # Mock data is disabled or invalid request
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        return {
            "status": "success",
            "message": "Troubleshooting analysis completed successfully",
            "data": {
                "request": {
                    "system": request.system,
                    "symptoms": request.symptoms,
                    "context": request.context,
                },
                "analysis": {
                    "potential_causes": [
                        {
                            "id": "cause-001",
                            "description": "Faulty component",
                            "probability": 0.75,
                            "evidence": "Based on the symptoms provided, this is likely caused by a faulty component.",
                        },
                        {
                            "id": "cause-002",
                            "description": "Improper maintenance",
                            "probability": 0.45,
                            "evidence": "The symptoms may also indicate improper maintenance procedures.",
                        },
                    ],
                    "recommended_solutions": [
                        {
                            "id": "sol-001",
                            "description": "Replace component",
                            "difficulty": "medium",
                            "estimated_time": "2 hours",
                            "steps": [
                                "Step 1: Prepare necessary tools and replacement parts",
                                "Step 2: Remove access panels",
                                "Step 3: Disconnect electrical connections",
                                "Step 4: Remove faulty component",
                                "Step 5: Install new component",
                                "Step 6: Reconnect electrical connections",
                                "Step 7: Perform functional test",
                            ],
                        },
                        {
                            "id": "sol-002",
                            "description": "Perform maintenance procedure",
                            "difficulty": "low",
                            "estimated_time": "1 hour",
                            "steps": [
                                "Step 1: Prepare necessary tools",
                                "Step 2: Inspect component for damage",
                                "Step 3: Clean component",
                                "Step 4: Adjust settings as needed",
                                "Step 5: Perform functional test",
                            ],
                        },
                    ],
                    "additional_resources": [
                        {
                            "id": "res-001",
                            "type": "documentation",
                            "title": "Component Maintenance Manual",
                            "reference": "CMM-123-456",
                        },
                        {
                            "id": "res-002",
                            "type": "video",
                            "title": "Troubleshooting Tutorial",
                            "reference": "VID-789-012",
                        },
                    ],
                },
            },
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error analyzing troubleshooting case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing troubleshooting case",
        )
