"""
Documentation Agent for the MAGPIE platform.

This agent processes, queries, and summarizes technical aircraft maintenance documentation.
It also manages cross-references between documents and handles document updates.
It implements industry best practices for aircraft documentation management.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from app.services.llm_service import LLMService
from app.services.prompt_templates import DOCUMENTATION_SEARCH_TEMPLATE, DOCUMENTATION_SUMMARY_TEMPLATE
from app.services.document_relationship_service import document_relationship_service
from app.services.document_notification_service import document_notification_service
from app.services.document_format_service import document_format_service
from app.services.maintenance_integration_service import maintenance_integration_service
from app.models.document_relationship import ReferenceType
from app.models.document_metadata import MetadataStandard

# Configure logging
logger = logging.getLogger(__name__)


class DocumentationAgent:
    """
    Agent for handling documentation-related queries.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        documentation_service: Optional[Any] = None
    ):
        """
        Initialize documentation agent.

        Args:
            llm_service: LLM service for generating responses
            documentation_service: Service for accessing documentation
        """
        self.llm_service = llm_service or LLMService()
        self.documentation_service = documentation_service

        # Import documentation service if not provided
        if not self.documentation_service:
            from app.core.mock.service import mock_data_service
            self.documentation_service = mock_data_service

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        conversation_id: Optional[str] = None  # Kept for backward compatibility
    ) -> Dict[str, Any]:
        """
        Process a documentation query.

        Args:
            query: User query
            conversation_id: Optional conversation ID
            context: Optional context information
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            Dict[str, Any]: Response with documentation information
        """
        try:
            # Search for relevant documentation
            search_results = await self.search_documentation(query, context)

            if not search_results:
                return {
                    "response": "I couldn't find any relevant documentation for your query. Please try rephrasing your question or providing more specific details about the aircraft type, system, or document type you're interested in.",
                    "sources": []
                }

            # Generate response using LLM
            response = await self.generate_response(query, search_results, context, model, temperature, max_tokens)

            return {
                "response": response,
                "sources": search_results
            }
        except Exception as e:
            logger.error(f"Error processing documentation query: {str(e)}")
            return {
                "response": "I encountered an error while processing your query. Please try again later.",
                "sources": []
            }

    async def search_documentation(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documentation.

        Args:
            query: Search query
            context: Optional context information

        Returns:
            List[Dict[str, Any]]: List of relevant documentation
        """
        try:
            # Prepare search parameters
            search_params = {
                "text": query,  # Use the full query text for searching
                "max_results": 5  # Limit to top 5 results
            }

            # Extract filters from context
            if context:
                if "aircraft_type" in context:
                    search_params["aircraft_type"] = context["aircraft_type"]
                if "system" in context:
                    search_params["system"] = context["system"]
                if "document_type" in context:
                    search_params["document_type"] = context["document_type"]

                # Extract keywords if available
                if "keywords" in context and isinstance(context["keywords"], list):
                    search_params["keywords"] = context["keywords"]

            # Search documentation
            search_response = self.documentation_service.search_documentation(search_params)

            # Extract and format results
            results = []
            if "results" in search_response and search_response["results"]:
                for result in search_response["results"]:
                    results.append({
                        "id": result["doc_id"],
                        "title": result["document_title"] + " - " + result["title"],
                        "content": result["snippet"],
                        "relevance": result["relevance_score"],
                        "source": f"Document ID: {result['doc_id']}, Section: {result['section_id']}",
                        "document_type": result["document_type"]
                    })

            return results
        except Exception as e:
            logger.error(f"Error searching documentation: {str(e)}")
            return []

    async def generate_response(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response based on documentation search results.

        Args:
            query: User query
            search_results: Documentation search results
            context: Optional context information
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            str: Generated response
        """
        try:
            # Format search results for the prompt
            formatted_results = []

            for i, result in enumerate(search_results):
                # Format each result with detailed information
                result_str = (
                    f"SOURCE {i+1}:\n"
                    f"Title: {result['title']}\n"
                    f"Document Type: {result['document_type']}\n"
                    f"Relevance Score: {result['relevance']:.2f}\n"
                    f"Source: {result['source']}\n"
                    f"Content: {result['content']}\n"
                )
                formatted_results.append(result_str)

            # Join all formatted results
            all_results = "\n\n".join(formatted_results)

            # Create prompt variables
            prompt_variables = {
                "query": query,
                "search_results": all_results
            }

            # Add context if available
            if context:
                # Filter out keywords from context to avoid confusion
                context_for_prompt = {k: v for k, v in context.items() if k != "keywords"}
                if context_for_prompt:
                    context_str = "\n".join([f"{key}: {value}" for key, value in context_for_prompt.items()])
                    prompt_variables["context"] = context_str

            # Generate response
            response = await self.llm_service.generate_completion(
                prompt_template=DOCUMENTATION_SEARCH_TEMPLATE,
                variables=prompt_variables,
                model=model,
                temperature=temperature or 0.3,  # Use lower temperature for more factual responses
                max_tokens=max_tokens or 1000  # Ensure enough tokens for comprehensive response
            )

            if not response or not response.get("content"):
                return "I couldn't generate a response based on the available documentation."

            return response["content"]
        except Exception as e:
            logger.error(f"Error generating documentation response: {str(e)}")
            return "I encountered an error while generating a response. Please try again later."

    async def summarize_document(
        self,
        document_id: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Summarize a document.

        Args:
            document_id: Document ID
            context: Optional context information
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            Dict[str, Any]: Document summary
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)

            if not document:
                return {
                    "response": f"I couldn't find the document with ID {document_id}.",
                    "document": None
                }

            # Create prompt variables
            prompt_variables = {
                "document_title": document["title"],
                "document_content": document["content"]
            }

            # Add section information if available
            if document.get("sections"):
                sections_summary = "\n\n".join([
                    f"Section: {section['title']}\nSummary: {section['content'][:100]}..."
                    for section in document["sections"][:5]  # Limit to first 5 sections
                ])
                prompt_variables["sections"] = sections_summary

            # Add context if available
            if context:
                context_str = "\n".join([f"{key}: {value}" for key, value in context.items()])
                prompt_variables["context"] = context_str

            # Generate summary
            response = await self.llm_service.generate_completion(
                prompt_template=DOCUMENTATION_SUMMARY_TEMPLATE,
                variables=prompt_variables,
                model=model,
                temperature=temperature or 0.3,  # Use lower temperature for more factual summaries
                max_tokens=max_tokens or 1000  # Ensure enough tokens for comprehensive summary
            )

            if not response or not response.get("content"):
                return {
                    "response": "I couldn't generate a summary for this document.",
                    "document": document
                }

            return {
                "response": response["content"],
                "document": document
            }
        except Exception as e:
            logger.error(f"Error summarizing document: {str(e)}")
            return {
                "response": "I encountered an error while summarizing the document. Please try again later.",
                "document": None
            }

    async def compare_documents(
        self,
        document_ids: List[str],
        comparison_aspect: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple documents.

        Args:
            document_ids: List of document IDs to compare
            comparison_aspect: Optional aspect to focus comparison on (e.g., "procedures", "safety precautions")
            context: Optional context information
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            Dict[str, Any]: Document comparison
        """
        try:
            if not document_ids or len(document_ids) < 2:
                return {
                    "response": "I need at least two documents to perform a comparison.",
                    "documents": []
                }

            # Get documents
            documents = []
            for doc_id in document_ids:
                try:
                    document = self.documentation_service.get_documentation(doc_id)
                    if document:
                        documents.append(document)
                except Exception as e:
                    logger.warning(f"Error retrieving document {doc_id}: {str(e)}")

            if len(documents) < 2:
                return {
                    "response": "I couldn't find enough valid documents to perform a comparison.",
                    "documents": documents
                }

            # Format documents for comparison
            formatted_docs = []
            for i, doc in enumerate(documents):
                # Format basic document info
                doc_info = f"DOCUMENT {i+1}:\nTitle: {doc['title']}\nType: {doc['type']}\nVersion: {doc['version']}\nLast Updated: {doc['last_updated']}\n\nContent Summary: {doc['content'][:200]}...\n"

                # Add section information if available and relevant to comparison aspect
                if doc.get("sections") and comparison_aspect:
                    relevant_sections = []
                    for section in doc["sections"]:
                        # Check if section is relevant to comparison aspect
                        if (comparison_aspect.lower() in section["title"].lower() or
                            comparison_aspect.lower() in section["content"].lower()):
                            relevant_sections.append(f"Section: {section['title']}\nContent: {section['content'][:150]}...")

                    if relevant_sections:
                        doc_info += "\nRelevant Sections:\n" + "\n\n".join(relevant_sections)

                formatted_docs.append(doc_info)

            # Create prompt for comparison
            from app.services.prompt_templates import PromptTemplate

            DOCUMENT_COMPARISON_TEMPLATE = PromptTemplate(
                name="document_comparison",
                description="Template for comparing documents",
                system_message=(
                    "You are a Technical Documentation Assistant for aircraft maintenance. "
                    "Your role is to compare technical documentation and highlight key similarities and differences. "
                    "Be precise, accurate, and safety-focused."
                ),
                user_message_template=(
                    "I need to compare the following documents:\n\n"
                    "{documents}\n\n"
                    "Please provide a detailed comparison"
                    "{aspect_prompt}"
                    ", highlighting key similarities and differences. "
                    "Focus on technical details, procedures, safety information, and regulatory requirements."
                ),
                variables=["documents", "aspect_prompt"],
            )

            # Create prompt variables
            prompt_variables = {
                "documents": "\n\n".join(formatted_docs),
                "aspect_prompt": f" focusing on {comparison_aspect}" if comparison_aspect else ""
            }

            # Add context if available
            if context:
                context_str = "\n".join([f"{key}: {value}" for key, value in context.items()])
                prompt_variables["context"] = context_str

            # Generate comparison
            response = await self.llm_service.generate_completion(
                prompt_template=DOCUMENT_COMPARISON_TEMPLATE,
                variables=prompt_variables,
                model=model,
                temperature=temperature or 0.3,  # Use lower temperature for more factual comparison
                max_tokens=max_tokens or 1500  # Ensure enough tokens for comprehensive comparison
            )

            if not response or not response.get("content"):
                return {
                    "response": "I couldn't generate a comparison for these documents.",
                    "documents": documents
                }

            return {
                "response": response["content"],
                "documents": documents
            }
        except Exception as e:
            logger.error(f"Error comparing documents: {str(e)}")
            return {
                "response": "I encountered an error while comparing the documents. Please try again later.",
                "documents": []
            }

    async def extract_section(
        self,
        document_id: str,
        section_id: Optional[str] = None,
        section_title: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None  # Reserved for future use
    ) -> Dict[str, Any]:
        """
        Extract a specific section from a document.

        Args:
            document_id: Document ID
            section_id: Optional section ID
            section_title: Optional section title (used if section_id not provided)
            context: Optional context information

        Returns:
            Dict[str, Any]: Extracted section
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)

            if not document:
                return {
                    "response": f"I couldn't find the document with ID {document_id}.",
                    "section": None,
                    "document": None
                }

            # Find the requested section
            section = None

            # If section_id is provided, find section by ID
            if section_id:
                for s in document.get("sections", []):
                    if s["id"] == section_id:
                        section = s
                        break

            # If section not found by ID and section_title is provided, find section by title
            if not section and section_title:
                for s in document.get("sections", []):
                    if section_title.lower() in s["title"].lower():
                        section = s
                        break

            # If section still not found, return error
            if not section:
                return {
                    "response": f"I couldn't find the requested section in document {document_id}.",
                    "section": None,
                    "document": document
                }

            # Record document view in analytics
            try:
                document_relationship_service.record_document_view(document_id)
            except Exception as analytics_error:
                logger.warning(f"Error recording document view: {str(analytics_error)}")

            # Return the section
            return {
                "response": f"Here is the {section['title']} section from {document['title']}:\n\n{section['content']}",
                "section": section,
                "document": document
            }
        except Exception as e:
            logger.error(f"Error extracting section: {str(e)}")
            return {
                "response": "I encountered an error while extracting the section. Please try again later.",
                "section": None,
                "document": None
            }

    async def get_document_references(
        self,
        document_id: str,
        direction: str = "to",
        reference_type: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get references to or from a document.

        Args:
            document_id: Document ID
            direction: Direction of references ("to" or "from")
            reference_type: Optional type of reference
            version: Optional document version

        Returns:
            Dict[str, Any]: Document references
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)

            if not document:
                return {
                    "response": f"I couldn't find the document with ID {document_id}.",
                    "references": [],
                    "document": None
                }

            # Convert reference_type string to enum if provided
            ref_type_enum = None
            if reference_type:
                try:
                    ref_type_enum = ReferenceType(reference_type.lower())
                except ValueError:
                    logger.warning(f"Invalid reference type: {reference_type}")

            # Get references
            if direction.lower() == "from":
                references = document_relationship_service.get_document_references_from(
                    document_id=document_id,
                    version=version,
                    reference_type=ref_type_enum
                )
            else:  # "to" is the default
                references = document_relationship_service.get_document_references_to(
                    document_id=document_id,
                    version=version,
                    reference_type=ref_type_enum
                )

            # Format response
            if not references:
                if direction.lower() == "from":
                    response_text = f"The document '{document['title']}' does not reference any other documents."
                else:
                    response_text = f"The document '{document['title']}' is not referenced by any other documents."
            else:
                if direction.lower() == "from":
                    response_text = f"The document '{document['title']}' references the following documents:\n\n"
                else:
                    response_text = f"The document '{document['title']}' is referenced by the following documents:\n\n"

                for i, ref in enumerate(references, 1):
                    response_text += f"{i}. Document ID: {ref['target_document_id'] if direction.lower() == 'from' else ref['source_document_id']}\n"
                    response_text += f"   Reference Type: {ref['reference_type']}\n"

                    if ref.get('source_section_id') and direction.lower() == "from":
                        response_text += f"   From Section: {ref['source_section_id']}\n"

                    if ref.get('target_section_id') and direction.lower() == "to":
                        response_text += f"   To Section: {ref['target_section_id']}\n"

                    if ref.get('context'):
                        response_text += f"   Context: {ref['context']}\n"

                    response_text += f"   Relevance: {ref['relevance_score']}\n\n"

            return {
                "response": response_text,
                "references": references,
                "document": document
            }
        except Exception as e:
            logger.error(f"Error getting document references: {str(e)}")
            return {
                "response": "I encountered an error while retrieving document references. Please try again later.",
                "references": [],
                "document": None
            }

    async def add_document_reference(
        self,
        source_document_id: str,
        target_document_id: str,
        reference_type: str,
        source_section_id: Optional[str] = None,
        target_section_id: Optional[str] = None,
        context: Optional[str] = None,
        relevance_score: float = 1.0
    ) -> Dict[str, Any]:
        """
        Add a reference between two documents.

        Args:
            source_document_id: Source document ID
            target_document_id: Target document ID
            reference_type: Type of reference
            source_section_id: Optional source section ID
            target_section_id: Optional target section ID
            context: Optional context of the reference
            relevance_score: Optional relevance score

        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            # Verify source document exists
            source_document = self.documentation_service.get_documentation(source_document_id)
            if not source_document:
                return {
                    "success": False,
                    "response": f"Source document with ID {source_document_id} not found."
                }

            # Verify target document exists
            target_document = self.documentation_service.get_documentation(target_document_id)
            if not target_document:
                return {
                    "success": False,
                    "response": f"Target document with ID {target_document_id} not found."
                }

            # Verify source section exists if provided
            if source_section_id:
                source_section_exists = False
                for section in source_document.get("sections", []):
                    if section["id"] == source_section_id:
                        source_section_exists = True
                        break

                if not source_section_exists:
                    return {
                        "success": False,
                        "response": f"Source section with ID {source_section_id} not found in document {source_document_id}."
                    }

            # Verify target section exists if provided
            if target_section_id:
                target_section_exists = False
                for section in target_document.get("sections", []):
                    if section["id"] == target_section_id:
                        target_section_exists = True
                        break

                if not target_section_exists:
                    return {
                        "success": False,
                        "response": f"Target section with ID {target_section_id} not found in document {target_document_id}."
                    }

            # Convert reference_type string to enum
            try:
                ref_type_enum = ReferenceType(reference_type.lower())
            except ValueError:
                return {
                    "success": False,
                    "response": f"Invalid reference type: {reference_type}. Valid types are: {', '.join([t.value for t in ReferenceType])}"
                }

            # Add reference
            reference = document_relationship_service.add_document_reference(
                source_document_id=source_document_id,
                target_document_id=target_document_id,
                reference_type=ref_type_enum,
                source_section_id=source_section_id,
                target_section_id=target_section_id,
                context=context,
                relevance_score=relevance_score
            )

            if not reference:
                return {
                    "success": False,
                    "response": "Failed to add document reference."
                }

            return {
                "success": True,
                "response": f"Successfully added reference from document {source_document_id} to document {target_document_id}.",
                "reference": reference
            }
        except Exception as e:
            logger.error(f"Error adding document reference: {str(e)}")
            return {
                "success": False,
                "response": "I encountered an error while adding the document reference. Please try again later."
            }

    async def get_document_versions(
        self,
        document_id: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get versions of a document.

        Args:
            document_id: Document ID
            limit: Optional maximum number of versions to return

        Returns:
            Dict[str, Any]: Document versions
        """
        try:
            # Verify document exists
            document = self.documentation_service.get_documentation(document_id)
            if not document:
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "versions": [],
                    "document": None
                }

            # Get versions
            versions = document_relationship_service.get_document_versions(
                document_id=document_id,
                limit=limit
            )

            # Format response
            if not versions:
                response_text = f"No version history found for document '{document['title']}'."
            else:
                response_text = f"Version history for document '{document['title']}':\n\n"
                for i, version in enumerate(versions, 1):
                    response_text += f"{i}. Version: {version['version']}\n"
                    response_text += f"   Created: {version['created_at']}\n"

                    if version.get('changes'):
                        response_text += f"   Changes: {version['changes']}\n"

                    response_text += f"   Active: {version['is_active']}\n\n"

            return {
                "response": response_text,
                "versions": versions,
                "document": document
            }
        except Exception as e:
            logger.error(f"Error getting document versions: {str(e)}")
            return {
                "response": "I encountered an error while retrieving document versions. Please try again later.",
                "versions": [],
                "document": None
            }

    async def get_document_notifications(
        self,
        document_id: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get document update notifications.

        Args:
            document_id: Optional document ID
            is_read: Optional read status
            limit: Optional maximum number of notifications to return

        Returns:
            Dict[str, Any]: Document notifications
        """
        try:
            # Get notifications
            notifications = document_notification_service.get_notifications(
                document_id=document_id,
                is_read=is_read,
                limit=limit
            )

            # Format response
            if not notifications:
                if document_id:
                    response_text = f"No notifications found for document {document_id}."
                else:
                    response_text = "No notifications found."
            else:
                if document_id:
                    response_text = f"Notifications for document {document_id}:\n\n"
                else:
                    response_text = "Document notifications:\n\n"

                for i, notification in enumerate(notifications, 1):
                    response_text += f"{i}. {notification['title']}\n"

                    if notification.get('description'):
                        response_text += f"   Description: {notification['description']}\n"

                    response_text += f"   Severity: {notification['severity']}\n"
                    response_text += f"   Created: {notification['created_at']}\n"
                    response_text += f"   Read: {notification['is_read']}\n"

                    if notification.get('affected_documents'):
                        response_text += f"   Affected Documents: {', '.join(notification['affected_documents'])}\n"

                    response_text += "\n"

            return {
                "response": response_text,
                "notifications": notifications
            }
        except Exception as e:
            logger.error(f"Error getting document notifications: {str(e)}")
            return {
                "response": "I encountered an error while retrieving document notifications. Please try again later.",
                "notifications": []
            }

    async def get_document_analytics(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Get analytics for a document.

        Args:
            document_id: Document ID

        Returns:
            Dict[str, Any]: Document analytics
        """
        try:
            # Verify document exists
            document = self.documentation_service.get_documentation(document_id)
            if not document:
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "analytics": None,
                    "document": None
                }

            # Get analytics
            analytics = document_relationship_service.get_document_analytics(document_id)

            # Format response
            if not analytics:
                response_text = f"No analytics found for document '{document['title']}'."
            else:
                response_text = f"Analytics for document '{document['title']}':\n\n"
                response_text += f"Reference Count: {analytics['reference_count']}\n"
                response_text += f"View Count: {analytics['view_count']}\n"

                if analytics.get('last_referenced_at'):
                    response_text += f"Last Referenced: {analytics['last_referenced_at']}\n"

                if analytics.get('last_viewed_at'):
                    response_text += f"Last Viewed: {analytics['last_viewed_at']}\n"

                if analytics.get('reference_distribution'):
                    response_text += "\nReference Distribution:\n"
                    for ref_type, count in analytics['reference_distribution'].items():
                        response_text += f"- {ref_type}: {count}\n"

            return {
                "response": response_text,
                "analytics": analytics,
                "document": document
            }
        except Exception as e:
            logger.error(f"Error getting document analytics: {str(e)}")
            return {
                "response": "I encountered an error while retrieving document analytics. Please try again later.",
                "analytics": None,
                "document": None
            }

    async def get_most_referenced_documents(
        self,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get most referenced documents.

        Args:
            limit: Maximum number of documents to return

        Returns:
            Dict[str, Any]: Most referenced documents
        """
        try:
            # Get most referenced documents
            documents = document_relationship_service.get_most_referenced_documents(limit)

            # Format response
            if not documents:
                response_text = "No document reference analytics found."
            else:
                response_text = f"Top {len(documents)} most referenced documents:\n\n"
                for i, doc in enumerate(documents, 1):
                    # Get document title if available
                    try:
                        document = self.documentation_service.get_documentation(doc['document_id'])
                        title = document['title'] if document else doc['document_id']
                    except Exception:
                        title = doc['document_id']

                    response_text += f"{i}. {title} (ID: {doc['document_id']})\n"
                    response_text += f"   Reference Count: {doc['reference_count']}\n"
                    response_text += f"   View Count: {doc['view_count']}\n"

                    if doc.get('reference_distribution'):
                        ref_types = ", ".join([f"{t}: {c}" for t, c in doc['reference_distribution'].items()])
                        response_text += f"   Reference Types: {ref_types}\n"

                    response_text += "\n"

            return {
                "response": response_text,
                "documents": documents
            }
        except Exception as e:
            logger.error(f"Error getting most referenced documents: {str(e)}")
            return {
                "response": "I encountered an error while retrieving the most referenced documents. Please try again later.",
                "documents": []
            }

    # Digital Documentation Management Best Practices Methods

    # Aircraft Maintenance System Integration Methods

    async def connect_maintenance_system(
        self,
        system_type: str,
        connection_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Connect to an aircraft maintenance system.

        Args:
            system_type: Type of maintenance system
            connection_params: Connection parameters (API keys, endpoints, etc.)

        Returns:
            Dict[str, Any]: Connection result
        """
        try:
            # Connect to maintenance system
            connection_result = maintenance_integration_service.connect_maintenance_system(
                system_type=system_type,
                connection_params=connection_params
            )

            # Format response
            if connection_result["success"]:
                response_text = f"Successfully connected to {system_type} maintenance system."
                if "connection_id" in connection_result:
                    response_text += f"\nConnection ID: {connection_result['connection_id']}"
            else:
                response_text = f"Failed to connect to {system_type} maintenance system.\n\nError: {connection_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": connection_result["success"],
                "error": connection_result.get("error"),
                "connection_id": connection_result.get("connection_id")
            }
        except Exception as e:
            logger.error(f"Error connecting to maintenance system: {str(e)}")
            return {
                "response": "I encountered an error while connecting to the maintenance system. Please try again later.",
                "success": False,
                "error": str(e)
            }

    async def get_maintenance_documents(
        self,
        connection_id: str,
        aircraft_id: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get maintenance documents from a connected maintenance system.

        Args:
            connection_id: Connection ID
            aircraft_id: Optional aircraft ID to filter documents
            document_type: Optional document type to filter
            limit: Optional maximum number of documents to return

        Returns:
            Dict[str, Any]: Maintenance documents
        """
        try:
            # Get documents from maintenance system
            documents_result = maintenance_integration_service.get_maintenance_documents(
                connection_id=connection_id,
                aircraft_id=aircraft_id,
                document_type=document_type,
                limit=limit
            )

            # Format response
            if documents_result["success"]:
                system_type = documents_result.get("system_type", "maintenance")
                count = documents_result.get("count", 0)

                if count == 0:
                    response_text = f"No documents found in {system_type} system."
                else:
                    response_text = f"Found {count} documents in {system_type} system:\n\n"
                    for i, doc in enumerate(documents_result["documents"], 1):
                        response_text += f"{i}. {doc['title']} (ID: {doc['document_id']})\n"
                        response_text += f"   Type: {doc['document_type']}\n"
                        response_text += f"   Version: {doc['version']}\n"
                        response_text += f"   Last Updated: {doc['last_updated']}\n"
                        response_text += f"   Aircraft: {doc['aircraft_id']}\n\n"
            else:
                response_text = f"Failed to retrieve documents from maintenance system.\n\nError: {documents_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": documents_result["success"],
                "error": documents_result.get("error"),
                "documents": documents_result.get("documents", []),
                "count": documents_result.get("count", 0)
            }
        except Exception as e:
            logger.error(f"Error getting maintenance documents: {str(e)}")
            return {
                "response": "I encountered an error while retrieving maintenance documents. Please try again later.",
                "success": False,
                "error": str(e),
                "documents": []
            }

    async def sync_document_with_maintenance_system(
        self,
        connection_id: str,
        document_id: str,
        sync_type: str = "push"  # "push" or "pull"
    ) -> Dict[str, Any]:
        """
        Synchronize a document with a maintenance system.

        Args:
            connection_id: Connection ID
            document_id: Document ID to synchronize
            sync_type: Type of synchronization ("push" or "pull")

        Returns:
            Dict[str, Any]: Synchronization result
        """
        try:
            # Verify document exists
            document = self.documentation_service.get_documentation(document_id)
            if not document and sync_type == "push":
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "success": False,
                    "error": "Document not found"
                }

            # Sync document with maintenance system
            sync_result = maintenance_integration_service.sync_document_with_maintenance_system(
                connection_id=connection_id,
                document_id=document_id,
                sync_type=sync_type
            )

            # Format response
            if sync_result["success"]:
                if sync_type == "push":
                    response_text = f"Successfully pushed document '{document['title']}' to maintenance system."
                else:
                    response_text = f"Successfully pulled document with ID {document_id} from maintenance system."

                if "sync_time" in sync_result:
                    response_text += f"\nSync Time: {sync_result['sync_time']}"
            else:
                response_text = f"Failed to synchronize document with maintenance system.\n\nError: {sync_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": sync_result["success"],
                "error": sync_result.get("error"),
                "document": document,
                "sync_time": sync_result.get("sync_time")
            }
        except Exception as e:
            logger.error(f"Error synchronizing document with maintenance system: {str(e)}")
            return {
                "response": "I encountered an error while synchronizing the document with the maintenance system. Please try again later.",
                "success": False,
                "error": str(e)
            }

    async def get_aircraft_status(
        self,
        connection_id: str,
        aircraft_id: str
    ) -> Dict[str, Any]:
        """
        Get aircraft status from a maintenance system.

        Args:
            connection_id: Connection ID
            aircraft_id: Aircraft ID

        Returns:
            Dict[str, Any]: Aircraft status
        """
        try:
            # Get aircraft status from maintenance system
            status_result = maintenance_integration_service.get_aircraft_status(
                connection_id=connection_id,
                aircraft_id=aircraft_id
            )

            # Format response
            if status_result["success"]:
                aircraft_status = status_result["aircraft_status"]
                response_text = f"Aircraft Status for {aircraft_status['aircraft_type']} (ID: {aircraft_status['aircraft_id']}):\n\n"
                response_text += f"Status: {aircraft_status['status']}\n"
                response_text += f"Last Maintenance: {aircraft_status['last_maintenance']}\n"
                response_text += f"Next Maintenance Due: {aircraft_status['next_maintenance_due']}\n"
                response_text += f"Flight Hours: {aircraft_status['flight_hours']}\n"
                response_text += f"Cycles: {aircraft_status['cycles']}\n"
                response_text += f"Location: {aircraft_status['location']}\n"
                response_text += f"Open Maintenance Items: {aircraft_status['maintenance_items_open']}\n"
                response_text += f"Deferred Maintenance Items: {aircraft_status['maintenance_items_deferred']}\n"
            else:
                response_text = f"Failed to retrieve aircraft status.\n\nError: {status_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": status_result["success"],
                "error": status_result.get("error"),
                "aircraft_status": status_result.get("aircraft_status")
            }
        except Exception as e:
            logger.error(f"Error getting aircraft status: {str(e)}")
            return {
                "response": "I encountered an error while retrieving aircraft status. Please try again later.",
                "success": False,
                "error": str(e)
            }

    async def get_maintenance_tasks(
        self,
        connection_id: str,
        aircraft_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get maintenance tasks from a connected maintenance system.

        Args:
            connection_id: Connection ID
            aircraft_id: Optional aircraft ID to filter tasks
            status: Optional status to filter tasks
            limit: Optional maximum number of tasks to return

        Returns:
            Dict[str, Any]: Maintenance tasks
        """
        try:
            # Get tasks from maintenance system
            tasks_result = maintenance_integration_service.get_maintenance_tasks(
                connection_id=connection_id,
                aircraft_id=aircraft_id,
                status=status,
                limit=limit
            )

            # Format response
            if tasks_result["success"]:
                system_type = tasks_result.get("system_type", "maintenance")
                count = tasks_result.get("count", 0)

                if count == 0:
                    response_text = f"No maintenance tasks found in {system_type} system."
                else:
                    response_text = f"Found {count} maintenance tasks in {system_type} system:\n\n"
                    for i, task in enumerate(tasks_result["tasks"], 1):
                        response_text += f"{i}. {task['description']} (ID: {task['task_id']})\n"
                        response_text += f"   Status: {task['status']}\n"
                        response_text += f"   Priority: {task['priority']}\n"
                        response_text += f"   Aircraft: {task['aircraft_id']}\n"

                        if "due_date" in task:
                            response_text += f"   Due Date: {task['due_date']}\n"

                        if "assigned_to" in task:
                            response_text += f"   Assigned To: {task['assigned_to']}\n"

                        if "related_document_ids" in task and task["related_document_ids"]:
                            response_text += f"   Related Documents: {', '.join(task['related_document_ids'])}\n"

                        response_text += "\n"
            else:
                response_text = f"Failed to retrieve maintenance tasks.\n\nError: {tasks_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": tasks_result["success"],
                "error": tasks_result.get("error"),
                "tasks": tasks_result.get("tasks", []),
                "count": tasks_result.get("count", 0)
            }
        except Exception as e:
            logger.error(f"Error getting maintenance tasks: {str(e)}")
            return {
                "response": "I encountered an error while retrieving maintenance tasks. Please try again later.",
                "success": False,
                "error": str(e),
                "tasks": []
            }

    async def register_document_update_webhook(
        self,
        connection_id: str,
        webhook_url: str,
        event_types: List[str]
    ) -> Dict[str, Any]:
        """
        Register a webhook for document updates from a maintenance system.

        Args:
            connection_id: Connection ID
            webhook_url: URL to receive webhook notifications
            event_types: Types of events to receive notifications for

        Returns:
            Dict[str, Any]: Registration result
        """
        try:
            # Register webhook with maintenance system
            webhook_result = maintenance_integration_service.register_document_update_webhook(
                connection_id=connection_id,
                webhook_url=webhook_url,
                event_types=event_types
            )

            # Format response
            if webhook_result["success"]:
                response_text = f"Successfully registered webhook for document updates."
                if "webhook_id" in webhook_result:
                    response_text += f"\nWebhook ID: {webhook_result['webhook_id']}"
                response_text += f"\nEvents: {', '.join(event_types)}"
            else:
                response_text = f"Failed to register webhook for document updates.\n\nError: {webhook_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": webhook_result["success"],
                "error": webhook_result.get("error"),
                "webhook_id": webhook_result.get("webhook_id")
            }
        except Exception as e:
            logger.error(f"Error registering document update webhook: {str(e)}")
            return {
                "response": "I encountered an error while registering the document update webhook. Please try again later.",
                "success": False,
                "error": str(e)
            }

    async def validate_document_format(
        self,
        document_id: str,
        format_type: str
    ) -> Dict[str, Any]:
        """
        Validate that a document conforms to the specified format.

        Args:
            document_id: Document ID
            format_type: Format type to validate against

        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)
            if not document:
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "valid": False,
                    "errors": ["Document not found"]
                }

            # Validate document format
            validation_result = document_format_service.validate_document_format(document, format_type)

            # Format response
            if validation_result["valid"]:
                response_text = f"Document '{document['title']}' is valid according to {format_type} format."
            else:
                response_text = f"Document '{document['title']}' is not valid according to {format_type} format.\n\nErrors:\n"
                for error in validation_result["errors"]:
                    response_text += f"- {error}\n"

            return {
                "response": response_text,
                "valid": validation_result["valid"],
                "errors": validation_result.get("errors", []),
                "document": document
            }
        except Exception as e:
            logger.error(f"Error validating document format: {str(e)}")
            return {
                "response": "I encountered an error while validating the document format. Please try again later.",
                "valid": False,
                "errors": [str(e)]
            }

    async def validate_document_standard(
        self,
        document_id: str,
        standard: str
    ) -> Dict[str, Any]:
        """
        Validate that a document conforms to the specified industry standard.

        Args:
            document_id: Document ID
            standard: Industry standard to validate against

        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)
            if not document:
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "valid": False,
                    "errors": ["Document not found"]
                }

            # Validate document standard
            validation_result = document_format_service.validate_document_standard(document, standard)

            # Format response
            if validation_result["valid"]:
                response_text = f"Document '{document['title']}' is valid according to {standard} standard."
            else:
                response_text = f"Document '{document['title']}' is not valid according to {standard} standard.\n\nErrors:\n"
                for error in validation_result["errors"]:
                    response_text += f"- {error}\n"

            return {
                "response": response_text,
                "valid": validation_result["valid"],
                "errors": validation_result.get("errors", []),
                "document": document
            }
        except Exception as e:
            logger.error(f"Error validating document standard: {str(e)}")
            return {
                "response": "I encountered an error while validating the document standard. Please try again later.",
                "valid": False,
                "errors": [str(e)]
            }

    async def convert_document_format(
        self,
        document_id: str,
        target_format: str
    ) -> Dict[str, Any]:
        """
        Convert a document to the specified format.

        Args:
            document_id: Document ID
            target_format: Target format

        Returns:
            Dict[str, Any]: Conversion results
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)
            if not document:
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "success": False,
                    "error": "Document not found"
                }

            # Determine source format (assume JSON for mock data)
            source_format = "json"

            # Convert document format
            conversion_result = document_format_service.convert_document_format(
                document,
                source_format,
                target_format
            )

            # Format response
            if conversion_result["success"]:
                response_text = f"Document '{document['title']}' was successfully converted to {target_format} format."

                # Add preview if available
                if "document" in conversion_result:
                    if target_format == "markdown":
                        preview = conversion_result["document"].get("content", "")
                        if len(preview) > 500:
                            preview = preview[:500] + "..."
                        response_text += f"\n\nPreview:\n\n{preview}"
            else:
                response_text = f"Failed to convert document '{document['title']}' to {target_format} format.\n\nError: {conversion_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": conversion_result["success"],
                "error": conversion_result.get("error"),
                "document": document,
                "converted_document": conversion_result.get("document")
            }
        except Exception as e:
            logger.error(f"Error converting document format: {str(e)}")
            return {
                "response": "I encountered an error while converting the document format. Please try again later.",
                "success": False,
                "error": str(e)
            }

    async def apply_metadata_schema(
        self,
        document_id: str,
        schema_type: str
    ) -> Dict[str, Any]:
        """
        Apply a metadata schema to a document.

        Args:
            document_id: Document ID
            schema_type: Type of schema to apply

        Returns:
            Dict[str, Any]: Schema application results
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)
            if not document:
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "success": False,
                    "error": "Document not found"
                }

            # Apply metadata schema
            schema_result = document_format_service.apply_metadata_schema(document, schema_type)

            # Format response
            if schema_result["success"]:
                response_text = f"Successfully applied {schema_type} metadata schema to document '{document['title']}'."

                # Add metadata preview
                if "document" in schema_result and "metadata" in schema_result["document"]:
                    metadata = schema_result["document"]["metadata"]
                    response_text += "\n\nMetadata Preview:\n"
                    for key, value in metadata.items():
                        response_text += f"- {key}: {value}\n"
            else:
                response_text = f"Failed to apply {schema_type} metadata schema to document '{document['title']}'.\n\nError: {schema_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": schema_result["success"],
                "error": schema_result.get("error"),
                "document": schema_result.get("document", document)
            }
        except Exception as e:
            logger.error(f"Error applying metadata schema: {str(e)}")
            return {
                "response": "I encountered an error while applying the metadata schema. Please try again later.",
                "success": False,
                "error": str(e)
            }

    async def validate_document_completeness(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Validate that a document is complete according to industry standards.

        Args:
            document_id: Document ID

        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)
            if not document:
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "valid": False,
                    "errors": ["Document not found"]
                }

            # Validate document completeness
            validation_result = document_format_service.validate_document_completeness(document)

            # Format response
            if validation_result["valid"]:
                response_text = f"Document '{document['title']}' is complete according to industry standards."

                # Add warnings if any
                if validation_result.get("warnings"):
                    response_text += "\n\nWarnings:\n"
                    for warning in validation_result["warnings"]:
                        response_text += f"- {warning}\n"
            else:
                response_text = f"Document '{document['title']}' is not complete according to industry standards.\n\nErrors:\n"
                for error in validation_result["errors"]:
                    response_text += f"- {error}\n"

                # Add warnings if any
                if validation_result.get("warnings"):
                    response_text += "\n\nWarnings:\n"
                    for warning in validation_result["warnings"]:
                        response_text += f"- {warning}\n"

            return {
                "response": response_text,
                "valid": validation_result["valid"],
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "document": document
            }
        except Exception as e:
            logger.error(f"Error validating document completeness: {str(e)}")
            return {
                "response": "I encountered an error while validating the document completeness. Please try again later.",
                "valid": False,
                "errors": [str(e)]
            }

    async def generate_document_metadata(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Generate standardized metadata for a document.

        Args:
            document_id: Document ID

        Returns:
            Dict[str, Any]: Generated metadata
        """
        try:
            # Get document
            document = self.documentation_service.get_documentation(document_id)
            if not document:
                return {
                    "response": f"Document with ID {document_id} not found.",
                    "success": False,
                    "error": "Document not found"
                }

            # Generate document metadata
            metadata_result = document_format_service.generate_document_metadata(document)

            # Format response
            if metadata_result["success"]:
                response_text = f"Successfully generated metadata for document '{document['title']}'."

                # Add metadata preview
                if "metadata" in metadata_result:
                    metadata = metadata_result["metadata"]
                    response_text += "\n\nMetadata:\n"
                    for key, value in metadata.items():
                        if isinstance(value, list):
                            response_text += f"- {key}: {', '.join(value)}\n"
                        else:
                            response_text += f"- {key}: {value}\n"
            else:
                response_text = f"Failed to generate metadata for document '{document['title']}'.\n\nError: {metadata_result.get('error', 'Unknown error')}"

            return {
                "response": response_text,
                "success": metadata_result["success"],
                "error": metadata_result.get("error"),
                "metadata": metadata_result.get("metadata"),
                "document": document
            }
        except Exception as e:
            logger.error(f"Error generating document metadata: {str(e)}")
            return {
                "response": "I encountered an error while generating document metadata. Please try again later.",
                "success": False,
                "error": str(e)
            }
