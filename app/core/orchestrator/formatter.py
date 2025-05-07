"""
Response formatter for the MAGPIE platform.

This module provides functionality for standardizing responses from
different agents into a consistent format and facilitating inter-agent
communication.
"""
import logging
import re
import random
from typing import Dict, List, Optional

from app.models.conversation import AgentType
from app.models.orchestrator import OrchestratorResponse, RoutingResult

# Configure logging
logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Formatter for standardizing agent responses and handling inter-agent communication.
    """

    def __init__(self):
        """
        Initialize the response formatter.
        """
        # Templates for different agent types
        self._response_templates = {
            AgentType.DOCUMENTATION: (
                "Based on the technical documentation, {response}"
            ),
            AgentType.TROUBLESHOOTING: (
                "Based on troubleshooting analysis, {response}"
            ),
            AgentType.MAINTENANCE: (
                "For maintenance procedures, {response}"
            )
        }

        # Templates for multi-agent responses
        self._multi_agent_template = (
            "{primary_response}\n\n"
            "Additional information:\n"
            "{secondary_responses}"
        )

        # Templates for confidence indicators
        self._confidence_phrases = {
            "high": [
                "I'm confident that",
                "It's clear that",
                "The documentation clearly states that",
                "According to the maintenance manual,"
            ],
            "medium": [
                "I believe that",
                "It appears that",
                "Based on the available information,",
                "The documentation suggests that"
            ],
            "low": [
                "It's possible that",
                "I'm not entirely certain, but",
                "The documentation is unclear, but",
                "This is my best guess, but"
            ]
        }

    def format_response(
        self,
        response_content: str,
        agent_type: AgentType,
        agent_name: str,
        confidence: float,
        conversation_id: str,
        metadata: Optional[Dict[str, str]] = None,
        source_references: Optional[List[Dict[str, str]]] = None,
    ) -> OrchestratorResponse:
        """
        Format an agent response into a standardized format.

        Args:
            response_content: Raw response content from the agent
            agent_type: Type of agent that generated the response
            agent_name: Name of the agent that generated the response
            confidence: Confidence score for the response
            conversation_id: Conversation ID
            metadata: Optional metadata
            source_references: Optional list of source references

        Returns:
            OrchestratorResponse: Formatted response
        """
        try:
            # Clean and standardize the response
            cleaned_response = self._clean_response(response_content)

            # Extract potential followup questions
            followup_questions = self._extract_followup_questions(cleaned_response)

            # Add source references if provided
            if source_references:
                cleaned_response = self._add_source_references(cleaned_response, source_references)

            # Create the formatted response
            return OrchestratorResponse(
                response=cleaned_response,
                agent_type=agent_type,
                agent_name=agent_name,
                confidence=confidence,
                conversation_id=conversation_id,
                metadata=metadata,
                followup_questions=followup_questions
            )

        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            # Return a simple error response
            return OrchestratorResponse(
                response="I apologize, but there was an error processing your request. Please try again.",
                agent_type=agent_type,
                agent_name=agent_name,
                confidence=0.0,
                conversation_id=conversation_id,
                metadata={"error": str(e)} if metadata is None else {**metadata, "error": str(e)},
                followup_questions=None
            )

    def format_multi_agent_response(
        self,
        primary_response: OrchestratorResponse,
        secondary_responses: List[OrchestratorResponse],
        routing_result: RoutingResult,
    ) -> OrchestratorResponse:
        """
        Format responses from multiple agents into a single coherent response.

        Args:
            primary_response: Primary agent response
            secondary_responses: List of secondary agent responses
            routing_result: Routing result that led to these responses

        Returns:
            OrchestratorResponse: Combined response
        """
        try:
            # Format secondary responses
            secondary_formatted = []
            for resp in secondary_responses:
                agent_prefix = f"From {resp.agent_name} ({resp.agent_type.value}):"
                # Truncate long responses from secondary agents
                content = self._truncate_response(resp.response, max_length=500)
                secondary_formatted.append(f"{agent_prefix} {content}")

            # Combine responses
            combined_content = self._multi_agent_template.format(
                primary_response=primary_response.response,
                secondary_responses="\n\n".join(secondary_formatted)
            )

            # Combine followup questions
            all_followups = []
            if primary_response.followup_questions:
                all_followups.extend(primary_response.followup_questions)

            for resp in secondary_responses:
                if resp.followup_questions:
                    # Add agent type to followup questions from secondary agents
                    agent_followups = [f"[{resp.agent_type.value}] {q}" for q in resp.followup_questions]
                    all_followups.extend(agent_followups)

            # Limit to a reasonable number of followup questions
            if len(all_followups) > 5:
                all_followups = all_followups[:5]

            # Combine metadata
            combined_metadata = primary_response.metadata or {}
            for resp in secondary_responses:
                if resp.metadata:
                    # Add agent type prefix to metadata keys from secondary agents
                    for key, value in resp.metadata.items():
                        combined_metadata[f"{resp.agent_type.value}_{key}"] = value

            # Create combined response
            return OrchestratorResponse(
                response=combined_content,
                agent_type=primary_response.agent_type,
                agent_name=primary_response.agent_name,
                confidence=primary_response.confidence,
                conversation_id=primary_response.conversation_id,
                metadata=combined_metadata,
                followup_questions=all_followups if all_followups else None
            )

        except Exception as e:
            logger.error(f"Error formatting multi-agent response: {str(e)}")
            # Return the primary response as fallback
            return primary_response

    def create_inter_agent_prompt(
        self,
        query: str,
        primary_agent_type: AgentType,
        secondary_agent_type: AgentType,
        primary_response: Optional[str] = None,
    ) -> str:
        """
        Create a prompt for inter-agent communication.

        Args:
            query: Original user query
            primary_agent_type: Type of the primary agent
            secondary_agent_type: Type of the secondary agent
            primary_response: Optional response from the primary agent

        Returns:
            str: Prompt for the secondary agent
        """
        # Base prompt template
        base_template = (
            "You are a specialized {agent_type} agent in the MAGPIE platform. "
            "You are being consulted to provide additional information for a user query. "
            "The primary agent handling this query is a {primary_agent_type} agent.\n\n"
            "User query: {query}\n\n"
        )

        # Add primary response if available
        if primary_response:
            base_template += (
                "The {primary_agent_type} agent has provided the following response:\n"
                "{primary_response}\n\n"
                "Please provide additional information from your {agent_type} perspective "
                "that complements the primary response. Focus on aspects that the primary "
                "agent might have missed or areas where your expertise can add value.\n\n"
                "Keep your response concise and focused on adding new information rather than "
                "repeating what the primary agent has already covered."
            )
        else:
            base_template += (
                "Please provide information from your {agent_type} perspective "
                "that would be helpful for answering this query. Focus on aspects "
                "where your specialized knowledge can add value.\n\n"
                "Keep your response concise and focused on providing relevant information."
            )

        # Format the prompt
        prompt = base_template.format(
            agent_type=secondary_agent_type.value,
            primary_agent_type=primary_agent_type.value,
            query=query,
            primary_response=primary_response
        )

        return prompt

    def _clean_response(self, response_content: str) -> str:
        """
        Clean and standardize a response.

        Args:
            response_content: Raw response content

        Returns:
            str: Cleaned response
        """
        # Remove any system instructions or formatting that might have leaked
        cleaned = re.sub(r'^\s*As an AI assistant.*?$', '', response_content, flags=re.MULTILINE)
        cleaned = re.sub(r'^\s*As a helpful assistant.*?$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^\s*I am a.*?assistant.*?$', '', cleaned, flags=re.MULTILINE)

        # Remove any JSON formatting that might have leaked
        cleaned = re.sub(r'```json.*?```', '', cleaned, flags=re.DOTALL)

        # Remove any markdown code blocks that might have leaked
        cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)

        # Remove any excessive newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        # Trim whitespace
        cleaned = cleaned.strip()

        return cleaned

    def _extract_followup_questions(self, response_content: str) -> Optional[List[str]]:
        """
        Extract potential followup questions from a response.

        Args:
            response_content: Response content

        Returns:
            Optional[List[str]]: List of followup questions or None
        """
        followup_questions = []

        # Look for sections that might contain followup questions
        followup_sections = [
            r'(?:Follow-up Questions|Followup Questions|Additional Questions|Questions to Consider):(.*?)(?:\n\n|$)',
            r'(?:You might want to ask|You may want to ask|Consider asking):(.*?)(?:\n\n|$)',
        ]

        for pattern in followup_sections:
            matches = re.search(pattern, response_content, re.IGNORECASE | re.DOTALL)
            if matches:
                section = matches.group(1).strip()
                # Extract individual questions
                questions = re.findall(r'(?:^|\n)[-*]?\s*(.+?\?)', section)
                followup_questions.extend(questions)

        # If no structured sections found, look for individual questions
        if not followup_questions:
            # Look for sentences ending with question marks
            questions = re.findall(r'(?<=\n).*?\?', response_content)

            # Filter to likely followup questions (those that start with certain phrases)
            followup_indicators = [
                'would you like', 'do you want', 'do you need', 'would you need',
                'are you interested', 'should i', 'shall i', 'can i', 'may i'
            ]

            for question in questions:
                question = question.strip()
                lower_q = question.lower()
                if any(lower_q.startswith(indicator) for indicator in followup_indicators):
                    followup_questions.append(question)

        # Deduplicate and limit the number of followup questions
        if followup_questions:
            # Remove duplicates while preserving order
            seen = set()
            unique_questions = []
            for q in followup_questions:
                q_lower = q.lower()
                if q_lower not in seen:
                    seen.add(q_lower)
                    unique_questions.append(q)

            # Limit to 5 questions
            followup_questions = unique_questions[:5]

        return followup_questions if followup_questions else None

    def _add_source_references(
        self, response_content: str, source_references: List[Dict[str, str]]
    ) -> str:
        """
        Add source references to a response.

        Args:
            response_content: Response content
            source_references: List of source references

        Returns:
            str: Response with source references
        """
        if not source_references:
            return response_content

        # Format source references
        references_section = "\n\nSources:\n"
        for i, ref in enumerate(source_references, 1):
            title = ref.get("title", "Source")
            url = ref.get("url", "")
            doc_id = ref.get("document_id", "")

            if url:
                references_section += f"{i}. {title}: {url}\n"
            elif doc_id:
                references_section += f"{i}. {title} (Document ID: {doc_id})\n"
            else:
                references_section += f"{i}. {title}\n"

        # Add references to response
        return response_content + references_section

    def _truncate_response(self, response: str, max_length: int = 500) -> str:
        """
        Truncate a response to a maximum length while preserving sentence boundaries.

        Args:
            response: Response to truncate
            max_length: Maximum length in characters

        Returns:
            str: Truncated response
        """
        if len(response) <= max_length:
            return response

        # Find the last sentence boundary before max_length
        truncated = response[:max_length]
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclamation = truncated.rfind('!')

        # Find the last sentence boundary
        last_boundary = max(last_period, last_question, last_exclamation)

        if last_boundary > 0:
            truncated = truncated[:last_boundary + 1]

        return truncated + " [...]"

    def add_confidence_indicator(
        self, response: str, confidence: float, agent_type: AgentType
    ) -> str:
        """
        Add a confidence indicator to a response.

        Args:
            response: Response content
            confidence: Confidence score
            agent_type: Agent type

        Returns:
            str: Response with confidence indicator
        """
        # Determine confidence level
        confidence_level = "high" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "low"

        # Get confidence phrases for this level
        phrases = self._confidence_phrases[confidence_level]

        # Select a phrase based on confidence
        phrase = random.choice(phrases)

        # Check if the response already starts with a confidence phrase
        for level_phrases in self._confidence_phrases.values():
            if any(response.startswith(p) for p in level_phrases):
                return response

        # Add the confidence phrase
        first_sentence_end = response.find('.')
        if first_sentence_end > 0:
            # Insert after the first sentence
            modified_response = response[:first_sentence_end + 1] + f" {phrase}" + response[first_sentence_end + 1:]
            return modified_response
        else:
            # Prepend to the response
            return f"{phrase} {response}"

    def format_response_with_template(
        self, response: str, agent_type: AgentType, confidence: float
    ) -> str:
        """
        Format a response using a template for the agent type.

        Args:
            response: Response content
            agent_type: Agent type
            confidence: Confidence score

        Returns:
            str: Formatted response
        """
        # Get template for this agent type
        template = self._response_templates.get(agent_type)

        if not template:
            # No template for this agent type, return as is
            return response

        # Format the response
        formatted = template.format(response=response)

        # Add confidence indicator
        return self.add_confidence_indicator(formatted, confidence, agent_type)
