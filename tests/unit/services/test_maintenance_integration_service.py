"""
Unit tests for the maintenance integration service.
"""
import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from app.services.maintenance_integration_service import maintenance_integration_service, MaintenanceSystemType


class TestMaintenanceIntegrationService:
    """Test cases for the maintenance integration service."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset connected systems for each test
        maintenance_integration_service.connected_systems = {}
        
        # Sample connection parameters
        self.connection_params = {
            "api_key": "test_api_key",
            "endpoint": "https://example.com/api",
            "username": "test_user",
            "password": "test_password"
        }

    def test_connect_maintenance_system_success(self):
        """Test connecting to a maintenance system successfully."""
        result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        
        assert result["success"] is True
        assert "connection_id" in result
        assert "message" in result
        assert "Successfully connected" in result["message"]
        
        # Verify the connection was stored
        connection_id = result["connection_id"]
        assert connection_id in maintenance_integration_service.connected_systems
        assert maintenance_integration_service.connected_systems[connection_id]["system_type"] == MaintenanceSystemType.CAMP
        assert maintenance_integration_service.connected_systems[connection_id]["status"] == "connected"

    def test_connect_maintenance_system_unsupported(self):
        """Test connecting to an unsupported maintenance system."""
        result = maintenance_integration_service.connect_maintenance_system(
            "unsupported_system",
            self.connection_params
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "Unsupported maintenance system" in result["error"]

    def test_disconnect_maintenance_system_success(self):
        """Test disconnecting from a maintenance system successfully."""
        # First connect to a system
        connect_result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        connection_id = connect_result["connection_id"]
        
        # Then disconnect
        result = maintenance_integration_service.disconnect_maintenance_system(connection_id)
        
        assert result["success"] is True
        assert "message" in result
        assert "Successfully disconnected" in result["message"]
        
        # Verify the connection status was updated
        assert maintenance_integration_service.connected_systems[connection_id]["status"] == "disconnected"
        assert "disconnected_at" in maintenance_integration_service.connected_systems[connection_id]

    def test_disconnect_maintenance_system_invalid_id(self):
        """Test disconnecting with an invalid connection ID."""
        result = maintenance_integration_service.disconnect_maintenance_system("invalid_id")
        
        assert result["success"] is False
        assert "error" in result
        assert "Connection ID not found" in result["error"]

    def test_get_maintenance_documents_success(self):
        """Test getting maintenance documents successfully."""
        # First connect to a system
        connect_result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        connection_id = connect_result["connection_id"]
        
        # Get documents
        result = maintenance_integration_service.get_maintenance_documents(
            connection_id,
            aircraft_id="ac-001",
            document_type="manual",
            limit=2
        )
        
        assert result["success"] is True
        assert "documents" in result
        assert "count" in result
        assert "system_type" in result
        assert result["system_type"] == MaintenanceSystemType.CAMP
        
        # Verify documents were filtered correctly
        for doc in result["documents"]:
            assert doc["aircraft_id"] == "ac-001"
            assert doc["document_type"] == "manual"
            assert "system_type" in doc
            assert doc["system_type"] == MaintenanceSystemType.CAMP

    def test_get_maintenance_documents_invalid_connection(self):
        """Test getting documents with an invalid connection ID."""
        result = maintenance_integration_service.get_maintenance_documents("invalid_id")
        
        assert result["success"] is False
        assert "error" in result
        assert "Connection ID not found" in result["error"]

    def test_get_maintenance_documents_disconnected(self):
        """Test getting documents from a disconnected system."""
        # First connect to a system
        connect_result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        connection_id = connect_result["connection_id"]
        
        # Disconnect
        maintenance_integration_service.disconnect_maintenance_system(connection_id)
        
        # Try to get documents
        result = maintenance_integration_service.get_maintenance_documents(connection_id)
        
        assert result["success"] is False
        assert "error" in result
        assert "Connection is not active" in result["error"]

    def test_sync_document_with_maintenance_system_success(self):
        """Test synchronizing a document successfully."""
        # First connect to a system
        connect_result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        connection_id = connect_result["connection_id"]
        
        # Sync document
        result = maintenance_integration_service.sync_document_with_maintenance_system(
            connection_id,
            "doc-001",
            "push"
        )
        
        assert result["success"] is True
        assert "message" in result
        assert "Successfully pushed document" in result["message"]
        assert "sync_time" in result
        
        # Test pull sync
        result = maintenance_integration_service.sync_document_with_maintenance_system(
            connection_id,
            "doc-001",
            "pull"
        )
        
        assert result["success"] is True
        assert "message" in result
        assert "Successfully pulled document" in result["message"]

    def test_sync_document_invalid_sync_type(self):
        """Test synchronizing with an invalid sync type."""
        # First connect to a system
        connect_result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        connection_id = connect_result["connection_id"]
        
        # Sync with invalid type
        result = maintenance_integration_service.sync_document_with_maintenance_system(
            connection_id,
            "doc-001",
            "invalid_type"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "Invalid sync type" in result["error"]

    def test_get_aircraft_status_success(self):
        """Test getting aircraft status successfully."""
        # First connect to a system
        connect_result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        connection_id = connect_result["connection_id"]
        
        # Get aircraft status
        result = maintenance_integration_service.get_aircraft_status(
            connection_id,
            "ac-001"
        )
        
        assert result["success"] is True
        assert "aircraft_status" in result
        assert "system_type" in result
        assert result["system_type"] == MaintenanceSystemType.CAMP
        
        # Verify aircraft status
        aircraft_status = result["aircraft_status"]
        assert aircraft_status["aircraft_id"] == "ac-001"
        assert aircraft_status["aircraft_type"] == "Boeing 737-800"
        assert "status" in aircraft_status
        assert "last_maintenance" in aircraft_status
        assert "next_maintenance_due" in aircraft_status
        assert "flight_hours" in aircraft_status
        assert "cycles" in aircraft_status
        assert "location" in aircraft_status
        assert "maintenance_items_open" in aircraft_status
        assert "maintenance_items_deferred" in aircraft_status

    def test_get_maintenance_tasks_success(self):
        """Test getting maintenance tasks successfully."""
        # First connect to a system
        connect_result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        connection_id = connect_result["connection_id"]
        
        # Get tasks
        result = maintenance_integration_service.get_maintenance_tasks(
            connection_id,
            aircraft_id="ac-001",
            status="open",
            limit=2
        )
        
        assert result["success"] is True
        assert "tasks" in result
        assert "count" in result
        assert "system_type" in result
        assert result["system_type"] == MaintenanceSystemType.CAMP
        
        # Verify tasks were filtered correctly
        for task in result["tasks"]:
            assert task["aircraft_id"] == "ac-001"
            assert task["status"] == "open"
            assert "system_type" in task
            assert task["system_type"] == MaintenanceSystemType.CAMP

    def test_register_document_update_webhook_success(self):
        """Test registering a document update webhook successfully."""
        # First connect to a system
        connect_result = maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        connection_id = connect_result["connection_id"]
        
        # Register webhook
        result = maintenance_integration_service.register_document_update_webhook(
            connection_id,
            "https://example.com/webhook",
            ["document.created", "document.updated", "document.deleted"]
        )
        
        assert result["success"] is True
        assert "webhook_id" in result
        assert "message" in result
        assert "Successfully registered webhook" in result["message"]
        assert "webhook_url" in result
        assert result["webhook_url"] == "https://example.com/webhook"
        assert "event_types" in result
        assert len(result["event_types"]) == 3

    def test_get_connected_systems(self):
        """Test getting all connected systems."""
        # Connect to multiple systems
        maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.CAMP,
            self.connection_params
        )
        maintenance_integration_service.connect_maintenance_system(
            MaintenanceSystemType.AMOS,
            self.connection_params
        )
        
        # Get connected systems
        result = maintenance_integration_service.get_connected_systems()
        
        assert result["success"] is True
        assert "systems" in result
        assert "count" in result
        assert result["count"] == 2
        
        # Verify system information
        for system in result["systems"]:
            assert "connection_id" in system
            assert "system_type" in system
            assert "status" in system
            assert "connected_at" in system
            assert system["status"] == "connected"
