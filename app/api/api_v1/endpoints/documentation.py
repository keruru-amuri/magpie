"""Technical Documentation Assistant endpoints for MAGPIE platform."""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.mock.service import mock_data_service
from app.core.agents.documentation_agent import DocumentationAgent
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
llm_service = LLMService()
documentation_agent = DocumentationAgent(llm_service=llm_service, documentation_service=mock_data_service)


# Request and response models
class DocumentQueryRequest(BaseModel):
    """Request model for document queries."""

    query: str = Field(..., description="User query about documentation")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")
    model: Optional[str] = Field(None, description="Optional model to use")
    temperature: Optional[float] = Field(None, description="Optional temperature")
    max_tokens: Optional[int] = Field(None, description="Optional max tokens")


class DocumentComparisonRequest(BaseModel):
    """Request model for document comparison."""

    document_ids: List[str] = Field(..., description="List of document IDs to compare")
    comparison_aspect: Optional[str] = Field(None, description="Optional aspect to focus comparison on")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")
    model: Optional[str] = Field(None, description="Optional model to use")
    temperature: Optional[float] = Field(None, description="Optional temperature")
    max_tokens: Optional[int] = Field(None, description="Optional max tokens")


class SectionExtractionRequest(BaseModel):
    """Request model for section extraction."""

    document_id: str = Field(..., description="Document ID")
    section_id: Optional[str] = Field(None, description="Optional section ID")
    section_title: Optional[str] = Field(None, description="Optional section title")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")


@router.get("/documentation", summary="Get Documentation List", tags=["documentation"])
async def get_documentation_list():
    """
    Get a list of available technical documentation.

    Returns:
        dict: List of available documentation with metadata.
    """
    try:
        # Get documentation list from mock data service
        documentation_list = mock_data_service.get_documentation_list()

        return {
            "status": "success",
            "message": "Documentation list retrieved successfully",
            "data": documentation_list,
        }
    except ValueError as e:
        # Mock data is disabled
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        return {
            "status": "success",
            "message": "Documentation list retrieved successfully",
            "data": [
                {
                    "id": "doc-001",
                    "title": "Aircraft Maintenance Manual",
                    "type": "manual",
                    "version": "1.0",
                    "last_updated": "2025-01-15",
                },
                {
                    "id": "doc-002",
                    "title": "Component Maintenance Manual",
                    "type": "manual",
                    "version": "2.1",
                    "last_updated": "2025-02-20",
                },
                {
                    "id": "doc-003",
                    "title": "Illustrated Parts Catalog",
                    "type": "catalog",
                    "version": "1.5",
                    "last_updated": "2025-03-10",
                },
            ],
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error retrieving documentation list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving documentation list",
        )


@router.get("/documentation/{doc_id}", summary="Get Documentation", tags=["documentation"])
async def get_documentation(doc_id: str):
    """
    Get specific technical documentation by ID.

    Args:
        doc_id: The ID of the documentation to retrieve.

    Returns:
        dict: Documentation content and metadata.

    Raises:
        HTTPException: If documentation is not found.
    """
    try:
        # Get documentation from mock data service
        documentation = mock_data_service.get_documentation(doc_id)

        return {
            "status": "success",
            "message": f"Documentation {doc_id} retrieved successfully",
            "data": documentation,
        }
    except FileNotFoundError:
        # Documentation not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documentation with ID {doc_id} not found",
        )
    except ValueError as e:
        # Mock data is disabled
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        if doc_id not in ["doc-001", "doc-002", "doc-003"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documentation with ID {doc_id} not found",
            )

        return {
            "status": "success",
            "message": f"Documentation {doc_id} retrieved successfully",
            "data": {
                "id": doc_id,
                "title": "Aircraft Maintenance Manual" if doc_id == "doc-001" else "Component Maintenance Manual",
                "type": "manual",
                "version": "1.0" if doc_id == "doc-001" else "2.1",
                "last_updated": "2025-01-15" if doc_id == "doc-001" else "2025-02-20",
                "content": "This is a placeholder for the actual documentation content.",
                "sections": [
                    {
                        "id": "section-1",
                        "title": "Introduction",
                        "content": "Introduction content placeholder.",
                    },
                    {
                        "id": "section-2",
                        "title": "Safety Precautions",
                        "content": "Safety precautions content placeholder.",
                    },
                    {
                        "id": "section-3",
                        "title": "Maintenance Procedures",
                        "content": "Maintenance procedures content placeholder.",
                    },
                ],
            },
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error retrieving documentation {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documentation {doc_id}",
        )


@router.post("/documentation/search", summary="Search Documentation", tags=["documentation"])
async def search_documentation(query: Dict[str, Any]):
    """
    Search technical documentation.

    Args:
        query: Search parameters including keywords, document types, etc.

    Returns:
        dict: Search results with matching documentation sections.
    """
    try:
        # Search documentation using mock data service
        search_results = mock_data_service.search_documentation(query)

        return {
            "status": "success",
            "message": "Search completed successfully",
            "data": search_results,
        }
    except ValueError as e:
        # Mock data is disabled
        logger.warning(f"Mock data error: {e}")
        # Fallback to placeholder data
        return {
            "status": "success",
            "message": "Search completed successfully",
            "data": {
                "query": query,
                "results_count": 2,
                "results": [
                    {
                        "doc_id": "doc-001",
                        "section_id": "section-3",
                        "title": "Maintenance Procedures",
                        "relevance_score": 0.95,
                        "snippet": "This is a placeholder for a matching snippet from the documentation.",
                    },
                    {
                        "doc_id": "doc-002",
                        "section_id": "section-2",
                        "title": "Safety Precautions",
                        "relevance_score": 0.82,
                        "snippet": "This is another placeholder for a matching snippet from the documentation.",
                    },
                ],
            },
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error searching documentation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching documentation",
        )


@router.post("/documentation/query", summary="Query Documentation", tags=["documentation"])
async def query_documentation(request: DocumentQueryRequest):
    """
    Query technical documentation using natural language.

    This endpoint uses the DocumentationAgent to process natural language queries
    about technical documentation. It searches for relevant documentation and
    generates a response based on the search results.

    Args:
        request: Query request including the query text and optional parameters

    Returns:
        dict: Response with answer and source documents
    """
    try:
        # Process query using documentation agent
        result = await documentation_agent.process_query(
            query=request.query,
            context=request.context,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return {
            "status": "success",
            "message": "Query processed successfully",
            "data": result,
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error processing documentation query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing documentation query",
        )


@router.post("/documentation/compare", summary="Compare Documents", tags=["documentation"])
async def compare_documents(request: DocumentComparisonRequest):
    """
    Compare multiple technical documents.

    This endpoint uses the DocumentationAgent to compare multiple documents
    and highlight key similarities and differences.

    Args:
        request: Comparison request including document IDs and optional parameters

    Returns:
        dict: Response with comparison and source documents
    """
    try:
        # Compare documents using documentation agent
        result = await documentation_agent.compare_documents(
            document_ids=request.document_ids,
            comparison_aspect=request.comparison_aspect,
            context=request.context,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return {
            "status": "success",
            "message": "Documents compared successfully",
            "data": result,
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error comparing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error comparing documents",
        )


@router.post("/documentation/extract-section", summary="Extract Document Section", tags=["documentation"])
async def extract_section(request: SectionExtractionRequest):
    """
    Extract a specific section from a document.

    This endpoint uses the DocumentationAgent to extract a specific section
    from a document based on section ID or title.

    Args:
        request: Section extraction request including document ID and section identifiers

    Returns:
        dict: Response with extracted section and source document
    """
    try:
        # Extract section using documentation agent
        result = await documentation_agent.extract_section(
            document_id=request.document_id,
            section_id=request.section_id,
            section_title=request.section_title,
            context=request.context
        )

        return {
            "status": "success",
            "message": "Section extracted successfully",
            "data": result,
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error extracting section: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error extracting section",
        )


@router.post("/documentation/summarize", summary="Summarize Document", tags=["documentation"])
async def summarize_document(document_id: str, model: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
    """
    Generate a summary of a document.

    This endpoint uses the DocumentationAgent to generate a concise summary
    of a document, highlighting key information.

    Args:
        document_id: ID of the document to summarize
        model: Optional model to use
        temperature: Optional temperature
        max_tokens: Optional max tokens

    Returns:
        dict: Response with summary and source document
    """
    try:
        # Summarize document using documentation agent
        result = await documentation_agent.summarize_document(
            document_id=document_id,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return {
            "status": "success",
            "message": "Document summarized successfully",
            "data": result,
        }
    except Exception as e:
        # Unexpected error
        logger.error(f"Error summarizing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error summarizing document",
        )
