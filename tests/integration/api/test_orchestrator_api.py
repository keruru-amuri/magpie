"""
Integration tests for the orchestrator API endpoints.
"""
import pytest
from httpx import AsyncClient

# Import the orchestrator fixtures
pytest_plugins = ["tests.conftest_orchestrator"]


class TestOrchestratorAPI:

    def test_process_query(self, orchestrator_client, mock_orchestrator):
        """
        Test processing a query.
        """
        # Test request data
        request_data = {
            "query": "What is the maintenance procedure for landing gear?",
            "user_id": "test-user",
            "conversation_id": "test-conversation-id",
            "context": {"aircraft_type": "Boeing 737"},
            "metadata": {"source": "test"}
        }

        # Send request
        response = orchestrator_client.post("/api/v1/orchestrator/query", json=request_data)

        # Print response for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "This is a test response"
        assert data["agent_type"] == "documentation"
        assert data["agent_name"] == "Documentation Assistant"
        assert data["confidence"] == 0.9
        assert data["conversation_id"] == "test-conversation-id"

        # Verify orchestrator was called correctly
        mock_orchestrator.process_request.assert_called_once()
        call_args = mock_orchestrator.process_request.call_args[0][0]
        assert call_args.query == request_data["query"]
        assert call_args.user_id == request_data["user_id"]
        assert call_args.conversation_id == request_data["conversation_id"]
        assert call_args.context == request_data["context"]
        assert "source" in call_args.metadata
        assert call_args.metadata["source"] == "test"

    def test_process_query_with_force_agent_type(self, orchestrator_client, mock_orchestrator):
        """
        Test processing a query with forced agent type.
        """
        # Test request data with force_agent_type
        request_data = {
            "query": "What is the maintenance procedure for landing gear?",
            "user_id": "test-user",
            "force_agent_type": "maintenance"
        }

        # Send request
        response = orchestrator_client.post("/api/v1/orchestrator/query", json=request_data)

        # Verify response
        assert response.status_code == 200

        # Verify orchestrator was called correctly
        mock_orchestrator.process_request.assert_called_once()
        call_args = mock_orchestrator.process_request.call_args[0][0]
        assert call_args.metadata is not None
        assert "force_agent_type" in call_args.metadata
        assert call_args.metadata["force_agent_type"] == "maintenance"

    def test_process_query_with_multi_agent_disabled(self, orchestrator_client, mock_orchestrator):
        """
        Test processing a query with multi-agent disabled.
        """
        # Test request data with enable_multi_agent=False
        request_data = {
            "query": "What is the maintenance procedure for landing gear?",
            "user_id": "test-user",
            "enable_multi_agent": False
        }

        # Send request
        response = orchestrator_client.post("/api/v1/orchestrator/query", json=request_data)

        # Verify response
        assert response.status_code == 200

        # Verify orchestrator was called correctly
        mock_orchestrator.process_request.assert_called_once()
        call_args = mock_orchestrator.process_request.call_args[0][0]
        assert call_args.metadata is not None
        assert "enable_multi_agent" in call_args.metadata
        assert call_args.metadata["enable_multi_agent"] == "False"

    def test_get_routing_info(self, orchestrator_client, mock_orchestrator):
        """
        Test getting routing information.
        """
        # Send request
        response = orchestrator_client.get("/api/v1/orchestrator/routing-info?query=What%20is%20the%20maintenance%20procedure%20for%20landing%20gear?")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "documentation"
        assert data["confidence"] == 0.9
        assert data["reasoning"] == "This is a documentation request"
        assert data["requires_followup"] is False
        assert data["requires_multiple_agents"] is False
        assert data["additional_agent_types"] is None

        # Verify orchestrator methods were called correctly
        mock_orchestrator.classifier.classify_request.assert_called_once()
        mock_orchestrator.router.route_request.assert_called_once()

    def test_get_routing_info_with_conversation_id(self, orchestrator_client, mock_orchestrator):
        """
        Test getting routing information with a conversation ID.
        """
        # Send request with conversation_id
        response = orchestrator_client.get(
            "/api/v1/orchestrator/routing-info?query=What%20is%20the%20maintenance%20procedure%20for%20landing%20gear?&conversation_id=test-conversation-id"
        )

        # Verify response
        assert response.status_code == 200

        # Verify conversation history was retrieved
        mock_orchestrator._get_conversation_history.assert_called_once_with("test-conversation-id")

    def test_get_conversation_history(self, orchestrator_client, mock_orchestrator):
        """
        Test getting conversation history.
        """
        # Send request
        response = orchestrator_client.get("/api/v1/orchestrator/conversation/test-conversation-id")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test-conversation-id"
        assert len(data["messages"]) == 2

        # Verify first message (user)
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Test message"

        # Verify second message (assistant)
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "Test response"
        assert data["messages"][1]["agent_type"] == "documentation"

        # Verify conversation repository was called correctly
        mock_orchestrator.conversation_repository.get_messages.assert_called_once_with("test-conversation-id")

    def test_get_conversation_history_not_found(self, orchestrator_client, mock_orchestrator):
        """
        Test getting conversation history when not found.
        """
        # Configure mock to return empty list (conversation not found)
        mock_orchestrator.conversation_repository.get_messages.return_value = []

        # Send request
        response = orchestrator_client.get("/api/v1/orchestrator/conversation/nonexistent-conversation-id")

        # Verify response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_conversation_history(self, orchestrator_client, mock_orchestrator):
        """
        Test deleting conversation history.
        """
        # Send request
        response = orchestrator_client.delete("/api/v1/orchestrator/conversation/test-conversation-id")

        # Verify response
        assert response.status_code == 204

        # Verify conversation repository and router were called correctly
        mock_orchestrator.conversation_repository.delete_conversation.assert_called_once_with("test-conversation-id")
        mock_orchestrator.router.clear_routing_history.assert_called_once_with("test-conversation-id")

    def test_delete_conversation_history_not_found(self, orchestrator_client, mock_orchestrator):
        """
        Test deleting conversation history when not found.
        """
        # Configure mock to return False (conversation not found)
        mock_orchestrator.conversation_repository.delete_conversation.return_value = False

        # Send request
        response = orchestrator_client.delete("/api/v1/orchestrator/conversation/nonexistent-conversation-id")

        # Verify response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_error_handling(self, orchestrator_client, mock_orchestrator):
        """
        Test error handling.
        """
        # Configure mock to raise an exception
        mock_orchestrator.process_request.side_effect = Exception("Test error")

        # Test request data
        request_data = {
            "query": "What is the maintenance procedure for landing gear?",
            "user_id": "test-user"
        }

        # Send request
        response = orchestrator_client.post("/api/v1/orchestrator/query", json=request_data)

        # Verify response
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
