"""
Integration tests for orchestrator endpoints.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.integration.base import BaseAPIIntegrationTest


class TestOrchestratorEndpoints(BaseAPIIntegrationTest):
    """
    Tests for orchestrator endpoints.
    """

    def test_process_query_endpoint(self):
        """
        Test the process query endpoint.
        """
        # Create test request
        request_data = {
            "query": "Where can I find information about landing gear maintenance?",
            "user_id": "test-user",
            "conversation_id": "test-conversation-id"
        }
        
        # Send request
        response = self.client.post(
            f"{settings.API_V1_STR}/orchestrator/query",
            json=request_data
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert "agent_type" in data
        assert "agent_name" in data
        assert "confidence" in data
        assert "conversation_id" in data
        assert data["conversation_id"] == "test-conversation-id"

    def test_process_query_with_context(self):
        """
        Test the process query endpoint with additional context.
        """
        # Create test request with context
        request_data = {
            "query": "Where can I find information about landing gear maintenance?",
            "user_id": "test-user",
            "conversation_id": "test-conversation-id",
            "context": {
                "aircraft_type": "Boeing 737",
                "manual_section": "Landing Gear"
            }
        }
        
        # Send request
        response = self.client.post(
            f"{settings.API_V1_STR}/orchestrator/query",
            json=request_data
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert "agent_type" in data
        assert "agent_name" in data
        assert "confidence" in data
        assert "conversation_id" in data

    def test_process_query_without_conversation_id(self):
        """
        Test the process query endpoint without a conversation ID.
        """
        # Create test request without conversation ID
        request_data = {
            "query": "Where can I find information about landing gear maintenance?",
            "user_id": "test-user"
        }
        
        # Send request
        response = self.client.post(
            f"{settings.API_V1_STR}/orchestrator/query",
            json=request_data
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert "agent_type" in data
        assert "agent_name" in data
        assert "confidence" in data
        assert "conversation_id" in data
        assert data["conversation_id"] is not None  # Should generate a UUID

    def test_process_query_with_metadata(self):
        """
        Test the process query endpoint with metadata.
        """
        # Create test request with metadata
        request_data = {
            "query": "Where can I find information about landing gear maintenance?",
            "user_id": "test-user",
            "conversation_id": "test-conversation-id",
            "metadata": {
                "source": "test",
                "session_id": "test-session"
            }
        }
        
        # Send request
        response = self.client.post(
            f"{settings.API_V1_STR}/orchestrator/query",
            json=request_data
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert "agent_type" in data
        assert "agent_name" in data
        assert "confidence" in data
        assert "conversation_id" in data
        assert "metadata" in data
        assert data["metadata"] is not None

    def test_process_query_invalid_request(self):
        """
        Test the process query endpoint with an invalid request.
        """
        # Create invalid test request (missing required field)
        request_data = {
            "query": "Where can I find information about landing gear maintenance?"
            # Missing user_id
        }
        
        # Send request
        response = self.client.post(
            f"{settings.API_V1_STR}/orchestrator/query",
            json=request_data
        )
        
        # Verify response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
