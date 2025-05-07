"""
Monitoring API endpoints for the MAGPIE platform.

This module provides API endpoints for monitoring, tracing, and log management.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel

from app.core.monitoring import (
    AuditLogEvent,
    AuditLogRecord,
    get_audit_logs,
    verify_audit_logs,
    rotate_logs,
    trace_function,
)
# For testing purposes, we'll create a dummy dependency
from fastapi import Security
from fastapi.security import APIKeyHeader

# Create a dummy dependency for testing
api_key_header = APIKeyHeader(name="X-API-Key")

def get_current_superuser(api_key: str = Security(api_key_header)):
    """Dummy function for testing."""
    return {"id": "test-user", "is_superuser": True}


router = APIRouter()


class AuditLogResponse(BaseModel):
    """Audit log response model."""

    id: str
    timestamp: datetime
    event_type: str
    action: str
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str
    details: Dict[str, Any] = {}


class AuditLogListResponse(BaseModel):
    """Audit log list response model."""

    logs: List[AuditLogResponse]
    total: int


class AuditLogVerificationResponse(BaseModel):
    """Audit log verification response model."""

    total_records: int
    valid_records: int
    invalid_records: int
    integrity_percentage: float
    invalid_record_ids: List[str] = []


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="Get audit logs",
    description="Get audit logs with optional filtering",
    dependencies=[Depends(get_current_superuser)],
)
@trace_function(name="get_audit_logs_endpoint")
async def get_audit_logs_endpoint(
    event_type: Optional[AuditLogEvent] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> AuditLogListResponse:
    """
    Get audit logs with optional filtering.

    Args:
        event_type: Filter by event type
        user_id: Filter by user ID
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        start_date: Start date for filtering
        end_date: End date for filtering
        limit: Maximum number of records to return

    Returns:
        AuditLogListResponse: List of audit logs
    """
    # Get audit logs
    logs = get_audit_logs(
        event_type=event_type,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    # Convert to response model
    response_logs = [
        AuditLogResponse(
            id=log.id,
            timestamp=log.timestamp,
            event_type=log.event_type,
            action=log.action,
            user_id=log.user_id,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            status=log.status,
            details=log.details,
        )
        for log in logs
    ]

    return AuditLogListResponse(
        logs=response_logs,
        total=len(logs),
    )


@router.get(
    "/audit-logs/verify",
    response_model=AuditLogVerificationResponse,
    summary="Verify audit logs",
    description="Verify the integrity of audit logs",
    dependencies=[Depends(get_current_superuser)],
)
@trace_function(name="verify_audit_logs_endpoint")
async def verify_audit_logs_endpoint() -> AuditLogVerificationResponse:
    """
    Verify the integrity of audit logs.

    Returns:
        AuditLogVerificationResponse: Verification results
    """
    # Verify audit logs
    result = verify_audit_logs()

    return AuditLogVerificationResponse(
        total_records=result["total_records"],
        valid_records=result["valid_records"],
        invalid_records=result["invalid_records"],
        integrity_percentage=result["integrity_percentage"],
        invalid_record_ids=result["invalid_record_ids"],
    )


@router.post(
    "/logs/rotate",
    summary="Rotate logs",
    description="Rotate logs based on retention policy",
    dependencies=[Depends(get_current_superuser)],
)
@trace_function(name="rotate_logs_endpoint")
async def rotate_logs_endpoint() -> Dict[str, Any]:
    """
    Rotate logs based on retention policy.

    Returns:
        Dict[str, Any]: Result of log rotation
    """
    # Rotate logs
    success = rotate_logs()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to rotate logs",
        )

    return {
        "message": "Logs rotated successfully",
        "timestamp": datetime.now(timezone.utc),
    }
