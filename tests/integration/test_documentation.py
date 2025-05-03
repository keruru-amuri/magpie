"""Integration tests for documentation endpoints."""

import pytest
from fastapi import status

from app.core.config import settings
from tests.integration.base import BaseAPIIntegrationTest


class TestDocumentationEndpoints(BaseAPIIntegrationTest):
    """Tests for documentation endpoints."""

    def test_get_documentation_list(self):
        """Test getting the list of available documentation."""
        response = self.client.get(f"{settings.API_V1_STR}/documentation/documentation")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Documentation list retrieved successfully"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        
        # Verify structure of documentation items
        doc_item = data["data"][0]
        assert "id" in doc_item
        assert "title" in doc_item
        assert "type" in doc_item
        assert "version" in doc_item
        assert "last_updated" in doc_item

    def test_get_documentation_by_id_valid(self):
        """Test getting documentation by valid ID."""
        valid_doc_id = "doc-001"
        response = self.client.get(f"{settings.API_V1_STR}/documentation/documentation/{valid_doc_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == f"Documentation {valid_doc_id} retrieved successfully"
        assert "data" in data
        
        # Verify structure of documentation data
        doc_data = data["data"]
        assert doc_data["id"] == valid_doc_id
        assert "title" in doc_data
        assert "type" in doc_data
        assert "version" in doc_data
        assert "last_updated" in doc_data
        assert "content" in doc_data
        assert "sections" in doc_data
        assert isinstance(doc_data["sections"], list)
        assert len(doc_data["sections"]) > 0

    def test_get_documentation_by_id_invalid(self):
        """Test getting documentation by invalid ID."""
        invalid_doc_id = "invalid-doc-id"
        response = self.client.get(f"{settings.API_V1_STR}/documentation/documentation/{invalid_doc_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert f"Documentation with ID {invalid_doc_id} not found" in data["detail"]

    def test_search_documentation(self):
        """Test searching documentation."""
        search_query = {"keywords": ["maintenance", "safety"], "doc_type": "manual"}
        response = self.client.post(
            f"{settings.API_V1_STR}/documentation/documentation/search", 
            json=search_query
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Search completed successfully"
        assert "data" in data
        
        # Verify structure of search results
        search_data = data["data"]
        assert "query" in search_data
        assert search_data["query"] == search_query
        assert "results_count" in search_data
        assert "results" in search_data
        assert isinstance(search_data["results"], list)
        assert len(search_data["results"]) > 0
        
        # Verify structure of search result items
        result_item = search_data["results"][0]
        assert "doc_id" in result_item
        assert "section_id" in result_item
        assert "title" in result_item
        assert "relevance_score" in result_item
        assert "snippet" in result_item
