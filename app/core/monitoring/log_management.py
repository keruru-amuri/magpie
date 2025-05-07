"""
Log management for the MAGPIE platform.

This module provides functionality for log rotation, archiving, and audit logging.
It ensures that logs are properly managed, stored, and accessible for analysis.
"""

import hashlib
import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set

from loguru import logger
from pydantic import BaseModel, Field

from app.core.cache.connection import RedisCache
from app.core.config import settings


# Configure logger
logger = logger.bind(name=__name__)


class LogLevel(str, Enum):
    """Log level enum."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogRetentionPolicy(BaseModel):
    """
    Log retention policy.
    
    Attributes:
        max_age_days: Maximum age of logs in days
        max_size_mb: Maximum size of log files in MB
        archive_enabled: Whether to archive logs before deletion
        archive_path: Path to archive logs
    """
    
    max_age_days: int = 30
    max_size_mb: int = 1000  # 1 GB
    archive_enabled: bool = True
    archive_path: Optional[str] = None


class AuditLogEvent(str, Enum):
    """Audit log event types."""
    
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    RESOURCE_CREATED = "resource_created"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    SECURITY_ALERT = "security_alert"


class AuditLogRecord(BaseModel):
    """
    Audit log record.
    
    Attributes:
        id: Unique identifier for the audit log record
        timestamp: Time when the event occurred
        event_type: Type of event
        user_id: ID of the user who performed the action
        resource_type: Type of resource affected
        resource_id: ID of the resource affected
        action: Action performed
        details: Additional details about the event
        ip_address: IP address of the user
        user_agent: User agent of the user
        status: Status of the action (success, failure)
        hash: Hash of the record for tamper detection
    """
    
    id: str = Field(default_factory=lambda: f"audit_{int(time.time() * 1000)}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditLogEvent
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"
    hash: Optional[str] = None
    
    def __init__(self, **data):
        """
        Initialize the audit log record.
        
        Args:
            **data: Data for the audit log record
        """
        super().__init__(**data)
        
        # Generate hash if not provided
        if not self.hash:
            self.hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """
        Generate a hash of the record for tamper detection.
        
        Returns:
            str: Hash of the record
        """
        # Create a dictionary with all fields except hash
        data = self.model_dump(exclude={"hash"})
        
        # Convert to JSON string
        json_str = json.dumps(data, sort_keys=True, default=str)
        
        # Generate SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """
        Verify the integrity of the record.
        
        Returns:
            bool: True if the record is intact, False if tampered
        """
        # Generate hash from current data
        current_hash = self._generate_hash()
        
        # Compare with stored hash
        return current_hash == self.hash


class LogManager:
    """
    Log manager for the MAGPIE platform.
    
    This class provides functionality for log rotation, archiving, and audit logging.
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        audit_log_dir: str = "logs/audit",
        retention_policy: Optional[LogRetentionPolicy] = None,
        prefix: str = "logs",
        ttl: int = 2592000,  # 30 days
    ):
        """
        Initialize the log manager.
        
        Args:
            log_dir: Directory for application logs
            audit_log_dir: Directory for audit logs
            retention_policy: Log retention policy
            prefix: Prefix for Redis keys
            ttl: Time-to-live for audit logs in Redis
        """
        self.log_dir = Path(log_dir)
        self.audit_log_dir = Path(audit_log_dir)
        self.retention_policy = retention_policy or LogRetentionPolicy()
        self.prefix = prefix
        self.ttl = ttl
        self.logger = logger.bind(name=__name__)
        
        # Create log directories if they don't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Redis cache if not in testing mode
        if settings.ENVIRONMENT != "testing":
            try:
                self.redis = RedisCache(prefix=prefix)
                self.enabled = True
            except Exception as e:
                self.logger.warning(f"Failed to initialize Redis for log management: {e}")
                self.enabled = False
        else:
            self.enabled = False
    
    def rotate_logs(self) -> bool:
        """
        Rotate logs based on retention policy.
        
        Returns:
            bool: True if logs were rotated successfully, False otherwise
        """
        try:
            # Get current time
            now = datetime.now(timezone.utc)
            
            # Get all log files
            log_files = list(self.log_dir.glob("*.log"))
            log_files.extend(self.log_dir.glob("*.log.zip"))
            
            # Check each log file
            for log_file in log_files:
                # Skip audit logs
                if "audit" in log_file.name:
                    continue
                
                # Get file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
                
                # Check if file is older than retention policy
                if (now - mtime).days > self.retention_policy.max_age_days:
                    # Archive if enabled
                    if self.retention_policy.archive_enabled:
                        self._archive_log(log_file)
                    
                    # Delete the file
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file}")
            
            # Check total size of log directory
            total_size_mb = sum(f.stat().st_size for f in self.log_dir.glob("*.log")) / (1024 * 1024)
            
            # If total size exceeds limit, delete oldest logs
            if total_size_mb > self.retention_policy.max_size_mb:
                # Get all log files sorted by modification time (oldest first)
                log_files = sorted(
                    self.log_dir.glob("*.log"),
                    key=lambda f: f.stat().st_mtime
                )
                
                # Delete oldest logs until size is below limit
                for log_file in log_files:
                    # Skip audit logs
                    if "audit" in log_file.name:
                        continue
                    
                    # Archive if enabled
                    if self.retention_policy.archive_enabled:
                        self._archive_log(log_file)
                    
                    # Delete the file
                    log_file.unlink()
                    self.logger.info(f"Deleted log file due to size limit: {log_file}")
                    
                    # Recalculate total size
                    total_size_mb = sum(f.stat().st_size for f in self.log_dir.glob("*.log")) / (1024 * 1024)
                    
                    # Stop if size is below limit
                    if total_size_mb <= self.retention_policy.max_size_mb:
                        break
            
            self.logger.info("Log rotation completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to rotate logs: {e}")
            return False
    
    def _archive_log(self, log_file: Path) -> bool:
        """
        Archive a log file.
        
        Args:
            log_file: Log file to archive
            
        Returns:
            bool: True if the file was archived successfully, False otherwise
        """
        try:
            # Create archive directory if it doesn't exist
            archive_dir = Path(self.retention_policy.archive_path or "logs/archive")
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Create archive filename with timestamp
            timestamp = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
            archive_filename = f"{log_file.stem}_{timestamp.strftime('%Y%m%d%H%M%S')}.zip"
            archive_path = archive_dir / archive_filename
            
            # Create a zip archive
            shutil.make_archive(
                base_name=str(archive_path.with_suffix("")),
                format="zip",
                root_dir=str(log_file.parent),
                base_dir=log_file.name,
            )
            
            self.logger.info(f"Archived log file: {log_file} -> {archive_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to archive log file {log_file}: {e}")
            return False
    
    def record_audit_log(self, audit_log: AuditLogRecord) -> bool:
        """
        Record an audit log.
        
        Args:
            audit_log: Audit log record
            
        Returns:
            bool: True if the audit log was recorded successfully, False otherwise
        """
        try:
            # Store in Redis if enabled
            if self.enabled:
                # Store the audit log record
                audit_log_key = f"audit:{audit_log.id}"
                self.redis.redis.set(
                    audit_log_key,
                    audit_log.model_dump_json(),
                    ex=self.ttl
                )
            
            # Store in file system
            audit_log_file = self.audit_log_dir / f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
            
            # Append to file
            with open(audit_log_file, "a") as f:
                f.write(audit_log.model_dump_json() + "\n")
            
            self.logger.debug(
                f"Recorded audit log: {audit_log.event_type} - {audit_log.action}",
                audit_log=audit_log.model_dump()
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to record audit log: {e}")
            return False
    
    def get_audit_logs(
        self,
        event_type: Optional[AuditLogEvent] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLogRecord]:
        """
        Get audit logs.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of records to return
            
        Returns:
            List[AuditLogRecord]: List of audit log records
        """
        if not self.enabled:
            return self._get_audit_logs_from_files(
                event_type, user_id, resource_type, resource_id,
                start_date, end_date, limit
            )
        
        try:
            # Get all audit log keys
            pattern = f"{self.prefix}:audit:*"
            keys = self.redis.redis.keys(pattern)
            
            # Sort keys by timestamp (newest first)
            keys = sorted(keys, reverse=True)[:limit * 2]  # Get more than needed for filtering
            
            # Get values for keys
            if not keys:
                return []
            
            values = self.redis.redis.mget(keys)
            
            # Parse values into audit log records
            records = []
            for value in values:
                if value:
                    try:
                        record_dict = json.loads(value.decode("utf-8"))
                        record = AuditLogRecord.model_validate(record_dict)
                        
                        # Apply filters
                        if event_type and record.event_type != event_type:
                            continue
                        if user_id and record.user_id != user_id:
                            continue
                        if resource_type and record.resource_type != resource_type:
                            continue
                        if resource_id and record.resource_id != resource_id:
                            continue
                        if start_date and record.timestamp < start_date:
                            continue
                        if end_date and record.timestamp > end_date:
                            continue
                        
                        # Verify integrity
                        if not record.verify_integrity():
                            self.logger.warning(
                                f"Audit log record integrity check failed: {record.id}",
                                record=record.model_dump()
                            )
                            continue
                        
                        records.append(record)
                        
                        # Check limit after filtering
                        if len(records) >= limit:
                            break
                    except Exception as e:
                        self.logger.error(f"Failed to parse audit log record: {e}")
            
            return records
        except Exception as e:
            self.logger.error(f"Failed to get audit logs from Redis: {e}")
            return self._get_audit_logs_from_files(
                event_type, user_id, resource_type, resource_id,
                start_date, end_date, limit
            )
    
    def _get_audit_logs_from_files(
        self,
        event_type: Optional[AuditLogEvent] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLogRecord]:
        """
        Get audit logs from files.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of records to return
            
        Returns:
            List[AuditLogRecord]: List of audit log records
        """
        try:
            # Get all audit log files
            audit_log_files = list(self.audit_log_dir.glob("audit_*.log"))
            
            # Sort files by name (newest first)
            audit_log_files = sorted(audit_log_files, reverse=True)
            
            # Filter files by date if start_date or end_date is provided
            if start_date or end_date:
                filtered_files = []
                for file in audit_log_files:
                    try:
                        # Extract date from filename
                        date_str = file.stem.split("_")[1]
                        file_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
                        
                        # Apply date filters
                        if start_date and file_date < start_date.replace(hour=0, minute=0, second=0, microsecond=0):
                            continue
                        if end_date and file_date > end_date.replace(hour=23, minute=59, second=59, microsecond=999999):
                            continue
                        
                        filtered_files.append(file)
                    except Exception:
                        # Include file if date parsing fails
                        filtered_files.append(file)
                
                audit_log_files = filtered_files
            
            # Read records from files
            records = []
            for file in audit_log_files:
                if len(records) >= limit:
                    break
                
                try:
                    with open(file, "r") as f:
                        for line in f:
                            try:
                                record_dict = json.loads(line.strip())
                                record = AuditLogRecord.model_validate(record_dict)
                                
                                # Apply filters
                                if event_type and record.event_type != event_type:
                                    continue
                                if user_id and record.user_id != user_id:
                                    continue
                                if resource_type and record.resource_type != resource_type:
                                    continue
                                if resource_id and record.resource_id != resource_id:
                                    continue
                                if start_date and record.timestamp < start_date:
                                    continue
                                if end_date and record.timestamp > end_date:
                                    continue
                                
                                # Verify integrity
                                if not record.verify_integrity():
                                    self.logger.warning(
                                        f"Audit log record integrity check failed: {record.id}",
                                        record=record.model_dump()
                                    )
                                    continue
                                
                                records.append(record)
                                
                                # Check limit after filtering
                                if len(records) >= limit:
                                    break
                            except Exception as e:
                                self.logger.error(f"Failed to parse audit log record from file: {e}")
                except Exception as e:
                    self.logger.error(f"Failed to read audit log file {file}: {e}")
            
            # Sort records by timestamp (newest first)
            records.sort(key=lambda r: r.timestamp, reverse=True)
            
            return records[:limit]
        except Exception as e:
            self.logger.error(f"Failed to get audit logs from files: {e}")
            return []
    
    def verify_audit_logs(self) -> Dict[str, Any]:
        """
        Verify the integrity of all audit logs.
        
        Returns:
            Dict[str, Any]: Verification results
        """
        try:
            # Get all audit log files
            audit_log_files = list(self.audit_log_dir.glob("audit_*.log"))
            
            # Initialize counters
            total_records = 0
            valid_records = 0
            invalid_records = 0
            invalid_record_ids = []
            
            # Check each file
            for file in audit_log_files:
                try:
                    with open(file, "r") as f:
                        for line in f:
                            try:
                                total_records += 1
                                
                                record_dict = json.loads(line.strip())
                                record = AuditLogRecord.model_validate(record_dict)
                                
                                # Verify integrity
                                if record.verify_integrity():
                                    valid_records += 1
                                else:
                                    invalid_records += 1
                                    invalid_record_ids.append(record.id)
                                    self.logger.warning(
                                        f"Audit log record integrity check failed: {record.id}",
                                        record=record.model_dump()
                                    )
                            except Exception as e:
                                invalid_records += 1
                                self.logger.error(f"Failed to parse audit log record from file: {e}")
                except Exception as e:
                    self.logger.error(f"Failed to read audit log file {file}: {e}")
            
            return {
                "total_records": total_records,
                "valid_records": valid_records,
                "invalid_records": invalid_records,
                "integrity_percentage": (valid_records / total_records * 100) if total_records > 0 else 100,
                "invalid_record_ids": invalid_record_ids,
            }
        except Exception as e:
            self.logger.error(f"Failed to verify audit logs: {e}")
            return {
                "error": str(e),
                "total_records": 0,
                "valid_records": 0,
                "invalid_records": 0,
                "integrity_percentage": 0,
                "invalid_record_ids": [],
            }


# Create a global log manager instance
log_manager = LogManager()


def record_audit_log(
    event_type: AuditLogEvent,
    action: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
) -> Optional[AuditLogRecord]:
    """
    Record an audit log.
    
    Args:
        event_type: Type of event
        action: Action performed
        user_id: ID of the user who performed the action
        resource_type: Type of resource affected
        resource_id: ID of the resource affected
        details: Additional details about the event
        ip_address: IP address of the user
        user_agent: User agent of the user
        status: Status of the action (success, failure)
        
    Returns:
        Optional[AuditLogRecord]: Audit log record if recorded successfully, None otherwise
    """
    # Create audit log record
    audit_log = AuditLogRecord(
        event_type=event_type,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
    )
    
    # Record audit log
    success = log_manager.record_audit_log(audit_log)
    
    return audit_log if success else None


def get_audit_logs(
    event_type: Optional[AuditLogEvent] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> List[AuditLogRecord]:
    """
    Get audit logs.
    
    Args:
        event_type: Filter by event type
        user_id: Filter by user ID
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        start_date: Start date for filtering
        end_date: End date for filtering
        limit: Maximum number of records to return
        
    Returns:
        List[AuditLogRecord]: List of audit log records
    """
    return log_manager.get_audit_logs(
        event_type, user_id, resource_type, resource_id,
        start_date, end_date, limit
    )


def verify_audit_logs() -> Dict[str, Any]:
    """
    Verify the integrity of all audit logs.
    
    Returns:
        Dict[str, Any]: Verification results
    """
    return log_manager.verify_audit_logs()


def rotate_logs() -> bool:
    """
    Rotate logs based on retention policy.
    
    Returns:
        bool: True if logs were rotated successfully, False otherwise
    """
    return log_manager.rotate_logs()
