"""
Integration tests for the maintenance system integration.

These tests verify the functionality of the aircraft maintenance system integration,
including document synchronization, maintenance task retrieval, and aircraft status tracking.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from app.services.maintenance_integration_service import maintenance_integration_service, MaintenanceSystemType
from app.core.agents.documentation_agent import DocumentationAgent


@pytest.fixture
def mock_documentation_service():
    """Create a mock documentation service."""
    mock_service = MagicMock()
    
    # Sample document
    sample_document = {
        "id": "doc-001",
        "title": "Boeing 737-800 Aircraft Maintenance Manual",
        "type": "manual",
        "version": "2.1",
        "last_updated": "2025-02-15",
        "content": "This Aircraft Maintenance Manual (AMM) provides detailed procedures for maintaining the Boeing 737-800 aircraft.",
        "sections": [
            {
                "id": "doc-001-section-1",
                "title": "Introduction",
                "content": "This manual contains essential information for maintenance personnel."
            },
            {
                "id": "doc-001-section-2",
                "title": "Chapter 29: Hydraulic Power",
                "content": "This chapter covers the hydraulic power system of the Boeing 737-800 aircraft."
            }
        ]
    }
    
    # Configure mock to return the sample document
    mock_service.get_documentation.return_value = sample_document
    
    return mock_service


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    mock_service = MagicMock()
    mock_service.generate_completion = AsyncMock(return_value={"content": "Generated content"})
    return mock_service


@pytest.fixture
def agent(mock_documentation_service, mock_llm_service):
    """Create a DocumentationAgent instance with mock services."""
    return DocumentationAgent(
        llm_service=mock_llm_service,
        documentation_service=mock_documentation_service
    )


@pytest.fixture
def connection_id():
    """Create a test connection ID."""
    # Connect to a maintenance system and return the connection ID
    connection_result = maintenance_integration_service.connect_maintenance_system(
        MaintenanceSystemType.CAMP,
        {
            "api_key": "test_api_key",
            "endpoint": "https://example.com/api",
            "username": "test_user",
            "password": "test_password"
        }
    )
    return connection_result["connection_id"]


class TestMaintenanceIntegration:
    """Integration tests for maintenance system integration features."""

    @pytest.mark.asyncio
    async def test_connect_maintenance_system_integration(self, agent):
        """Test connecting to a maintenance system integration."""
        # Test successful connection
        connection_params = {
            "api_key": "test_api_key",
            "endpoint": "https://example.com/api",
            "username": "test_user",
            "password": "test_password"
        }
        
        result = await agent.connect_maintenance_system(MaintenanceSystemType.CAMP, connection_params)
        
        assert result["success"] is True
        assert "Successfully connected" in result["response"]
        assert "connection_id" in result
        
        # Test connection to unsupported system
        result = await agent.connect_maintenance_system("unsupported_system", connection_params)
        
        assert result["success"] is False
        assert "Failed to connect" in result["response"]
        assert "Unsupported maintenance system" in result["error"]

    @pytest.mark.asyncio
    async def test_get_maintenance_documents_integration(self, agent, connection_id):
        """Test getting maintenance documents integration."""
        # Test getting documents
        result = await agent.get_maintenance_documents(
            connection_id,
            aircraft_id="ac-001",
            document_type="manual"
        )
        
        assert result["success"] is True
        assert "Found" in result["response"]
        assert "documents" in result
        assert "count" in result
        assert result["count"] > 0
        
        # Verify document filtering
        for doc in result["documents"]:
            assert doc["aircraft_id"] == "ac-001"
            assert doc["document_type"] == "manual"
        
        # Test with invalid connection ID
        result = await agent.get_maintenance_documents("invalid_id")
        
        assert result["success"] is False
        assert "Failed to retrieve documents" in result["response"]
        assert "Connection ID not found" in result["error"]

    @pytest.mark.asyncio
    async def test_sync_document_with_maintenance_system_integration(self, agent, connection_id):
        """Test document synchronization integration."""
        # Test push synchronization
        result = await agent.sync_document_with_maintenance_system(
            connection_id,
            "doc-001",
            "push"
        )
        
        assert result["success"] is True
        assert "Successfully pushed document" in result["response"]
        assert "document" in result
        assert "sync_time" in result
        
        # Test pull synchronization
        result = await agent.sync_document_with_maintenance_system(
            connection_id,
            "doc-001",
            "pull"
        )
        
        assert result["success"] is True
        assert "Successfully pulled document" in result["response"]
        
        # Test with invalid sync type
        result = await agent.sync_document_with_maintenance_system(
            connection_id,
            "doc-001",
            "invalid_type"
        )
        
        assert result["success"] is False
        assert "Failed to synchronize document" in result["response"]
        assert "Invalid sync type" in result["error"]
        
        # Test with invalid document ID
        agent.documentation_service.get_documentation.return_value = None
        result = await agent.sync_document_with_maintenance_system(
            connection_id,
            "invalid-id",
            "push"
        )
        
        assert result["success"] is False
        assert "Document with ID invalid-id not found" in result["response"]

    @pytest.mark.asyncio
    async def test_get_aircraft_status_integration(self, agent, connection_id):
        """Test getting aircraft status integration."""
        # Test getting aircraft status
        result = await agent.get_aircraft_status(
            connection_id,
            "ac-001"
        )
        
        assert result["success"] is True
        assert "Aircraft Status for Boeing 737-800" in result["response"]
        assert "aircraft_status" in result
        assert result["aircraft_status"]["aircraft_id"] == "ac-001"
        assert result["aircraft_status"]["aircraft_type"] == "Boeing 737-800"
        assert "status" in result["aircraft_status"]
        assert "flight_hours" in result["aircraft_status"]
        assert "cycles" in result["aircraft_status"]
        
        # Test with invalid connection ID
        result = await agent.get_aircraft_status("invalid_id", "ac-001")
        
        assert result["success"] is False
        assert "Failed to retrieve aircraft status" in result["response"]
        assert "Connection ID not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_maintenance_tasks_integration(self, agent, connection_id):
        """Test getting maintenance tasks integration."""
        # Test getting tasks
        result = await agent.get_maintenance_tasks(
            connection_id,
            aircraft_id="ac-001",
            status="open"
        )
        
        assert result["success"] is True
        assert "Found" in result["response"]
        assert "tasks" in result
        assert "count" in result
        assert result["count"] > 0
        
        # Verify task filtering
        for task in result["tasks"]:
            assert task["aircraft_id"] == "ac-001"
            assert task["status"] == "open"
        
        # Test with invalid connection ID
        result = await agent.get_maintenance_tasks("invalid_id")
        
        assert result["success"] is False
        assert "Failed to retrieve maintenance tasks" in result["response"]
        assert "Connection ID not found" in result["error"]

    @pytest.mark.asyncio
    async def test_register_document_update_webhook_integration(self, agent, connection_id):
        """Test registering document update webhook integration."""
        # Test registering webhook
        event_types = ["document.created", "document.updated", "document.deleted"]
        result = await agent.register_document_update_webhook(
            connection_id,
            "https://example.com/webhook",
            event_types
        )
        
        assert result["success"] is True
        assert "Successfully registered webhook" in result["response"]
        assert "webhook_id" in result
        assert "Events:" in result["response"]
        
        # Test with invalid connection ID
        result = await agent.register_document_update_webhook(
            "invalid_id",
            "https://example.com/webhook",
            event_types
        )
        
        assert result["success"] is False
        assert "Failed to register webhook" in result["response"]
        assert "Connection ID not found" in result["error"]
