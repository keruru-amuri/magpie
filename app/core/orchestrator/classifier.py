"""
Request classifier for the MAGPIE platform.

This module provides functionality for classifying user requests
to determine the appropriate agent type based on the content and intent.
"""
import hashlib
import json
import logging
import re
from enum import Enum
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from app.models.conversation import AgentType
from app.models.orchestrator import AgentMetadata, RequestClassification
from app.services.llm_service import LLMService, ModelSize

# Configure logging
logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """
    Enum for content types in user queries.
    """

    TEXT = "text"
    CODE = "code"
    STRUCTURED_DATA = "structured_data"
    MIXED = "mixed"


class RequestClassifier:
    """
    Classifier for determining the appropriate agent type for a request.
    """

    def __init__(self, llm_service: LLMService, cache_size: int = 100):
        """
        Initialize the request classifier.

        Args:
            llm_service: LLM service for classification
            cache_size: Size of the classification cache
        """
        self.llm_service = llm_service
        self._cache_size = cache_size
        self._classification_cache = {}
        self._keyword_patterns = self._initialize_keyword_patterns()

    def _initialize_keyword_patterns(self) -> Dict[AgentType, List[re.Pattern]]:
        """
        Initialize keyword patterns for quick classification.

        Returns:
            Dict[AgentType, List[re.Pattern]]: Mapping of agent types to keyword patterns
        """
        patterns = {
            AgentType.DOCUMENTATION: [
                re.compile(r'\b(document|manual|guide|instruction|reference|find|search|where|how to find|locate)\b', re.IGNORECASE),
                re.compile(r'\b(what does|what is|definition|explain|meaning|information about)\b', re.IGNORECASE),
            ],
            AgentType.TROUBLESHOOTING: [
                re.compile(r'\b(troubleshoot|problem|issue|error|fault|diagnose|fix|repair|resolve|not working|fails|failed)\b', re.IGNORECASE),
                re.compile(r'\b(why is|why does|what causes|how to fix|how to solve|debug|symptom)\b', re.IGNORECASE),
            ],
            AgentType.MAINTENANCE: [
                re.compile(r'\b(maintenance|procedure|step|process|replace|install|remove|overhaul|service|inspection)\b', re.IGNORECASE),
                re.compile(r'\b(how to perform|how to do|how to replace|how to install|how to remove|how to service)\b', re.IGNORECASE),
            ]
        }
        return patterns

    @lru_cache(maxsize=100)
    def _detect_content_type(self, query: str) -> ContentType:
        """
        Detect the content type of a query.

        Args:
            query: User query

        Returns:
            ContentType: Detected content type
        """
        # Check for code blocks
        code_patterns = [
            r'```[\s\S]*?```',  # Markdown code blocks
            r'<code>[\s\S]*?</code>',  # HTML code tags
            r'\b(function|def|class|import|from|var|const|let)\b.*[{(:;]',  # Programming keywords
            r'[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\(.*\)',  # Method calls
        ]

        for pattern in code_patterns:
            if re.search(pattern, query):
                return ContentType.CODE

        # Check for structured data
        structured_data_patterns = [
            r'{[\s\S]*?}',  # JSON-like objects
            r'\[[\s\S]*?\]',  # Arrays
            r'<[a-zA-Z0-9]+>[\s\S]*?</[a-zA-Z0-9]+>',  # XML-like tags
            r'[a-zA-Z0-9_]+=["\'][^"\']*["\']',  # Key-value pairs
            r'\|[\s\S]*?\|',  # Table-like structures
        ]

        for pattern in structured_data_patterns:
            if re.search(pattern, query):
                return ContentType.STRUCTURED_DATA

        # Default to text
        return ContentType.TEXT

    def _quick_classify(self, query: str) -> Tuple[Optional[AgentType], float]:
        """
        Perform a quick classification based on keywords.

        Args:
            query: User query

        Returns:
            Tuple[Optional[AgentType], float]: Agent type and confidence score, or (None, 0.0) if no match
        """
        scores = {agent_type: 0 for agent_type in AgentType}

        # Count matches for each agent type
        for agent_type, patterns in self._keyword_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(query)
                scores[agent_type] += len(matches)

        # Find the agent type with the highest score
        max_score = max(scores.values())
        if max_score == 0:
            return None, 0.0

        # Check if there's a clear winner
        max_agent_types = [agent_type for agent_type, score in scores.items() if score == max_score]
        if len(max_agent_types) == 1:
            # Calculate confidence based on the difference between the highest and second highest scores
            sorted_scores = sorted(scores.values(), reverse=True)
            if len(sorted_scores) > 1 and sorted_scores[0] > 0:
                # Normalize confidence between 0.5 and 0.8
                confidence = 0.5 + min(0.3, (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0] * 0.3)
            else:
                confidence = 0.5

            return max_agent_types[0], confidence

        return None, 0.0

    def _get_cache_key(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a cache key for a query and conversation history.

        Args:
            query: User query
            conversation_history: Optional conversation history

        Returns:
            str: Cache key
        """
        # Use only the last few messages from conversation history to avoid cache misses
        if conversation_history:
            # Take only the last 3 messages
            recent_history = conversation_history[-3:]
            history_str = json.dumps(recent_history)
        else:
            history_str = ""

        # Create a hash of the query and history
        key_str = f"{query}|{history_str}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def classify_request(
        self,
        query: str,
        available_agents: List[AgentMetadata],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RequestClassification:
        """
        Classify a user request to determine the appropriate agent type.

        Args:
            query: User query
            available_agents: List of available agent metadata
            conversation_history: Optional conversation history for context

        Returns:
            RequestClassification: Classification result
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, conversation_history)
            if cache_key in self._classification_cache:
                logger.info(f"Using cached classification for query: {query[:50]}...")
                return self._classification_cache[cache_key]

            # Detect content type
            content_type = self._detect_content_type(query)
            logger.debug(f"Detected content type: {content_type}")

            # Try quick classification first
            agent_type, confidence = self._quick_classify(query)

            # If quick classification is confident enough, use it
            if agent_type and confidence >= 0.7:
                logger.info(f"Quick classification: {agent_type} with confidence {confidence}")
                classification = RequestClassification(
                    agent_type=agent_type,
                    confidence=confidence,
                    reasoning=f"Classified based on keyword matching with confidence {confidence:.2f}"
                )

                # Cache the result
                self._classification_cache[cache_key] = classification

                # Trim cache if it gets too large
                if len(self._classification_cache) > self._cache_size:
                    # Remove a random key (simple approach)
                    self._classification_cache.pop(next(iter(self._classification_cache)))

                return classification

            # Create a prompt for the LLM to classify the request
            system_prompt = self._create_classification_prompt(available_agents, content_type)

            # Prepare conversation history if provided
            messages = [{"role": "system", "content": system_prompt}]

            if conversation_history:
                for message in conversation_history:
                    messages.append(message)

            # Add the current query
            messages.append({"role": "user", "content": query})

            # Get classification from LLM
            response = await self.llm_service.generate_custom_response_async(
                messages=messages,
                model_size=ModelSize.SMALL,  # Use small model for efficiency
                temperature=0.3,  # Low temperature for more deterministic results
                max_tokens=500,
            )

            # Parse the response to extract classification
            classification = self._parse_classification_response(response["content"])

            # Cache the result
            self._classification_cache[cache_key] = classification

            # Trim cache if it gets too large
            if len(self._classification_cache) > self._cache_size:
                # Remove a random key (simple approach)
                self._classification_cache.pop(next(iter(self._classification_cache)))

            logger.info(f"Request classified as {classification.agent_type} with confidence {classification.confidence}")
            return classification

        except Exception as e:
            logger.error(f"Error classifying request: {str(e)}")
            # Default to documentation agent if classification fails
            return RequestClassification(
                agent_type=AgentType.DOCUMENTATION,
                confidence=0.3,
                reasoning="Classification failed, defaulting to documentation agent."
            )

    def _create_classification_prompt(
        self, available_agents: List[AgentMetadata], content_type: ContentType = ContentType.TEXT
    ) -> str:
        """
        Create a prompt for the LLM to classify the request.

        Args:
            available_agents: List of available agent metadata
            content_type: Detected content type of the query

        Returns:
            str: Classification prompt
        """
        agent_descriptions = []
        for agent in available_agents:
            capabilities = "\n".join([f"- {cap.name}: {cap.description}" for cap in agent.capabilities])
            keywords = "\n".join([f"- {', '.join(cap.keywords)}" for cap in agent.capabilities if cap.keywords])
            examples = "\n".join([f"- {ex}" for cap in agent.capabilities for ex in cap.examples])

            agent_descriptions.append(
                f"Agent Type: {agent.agent_type.value}\n"
                f"Description: {agent.description}\n"
                f"Capabilities:\n{capabilities}\n"
                f"Keywords:\n{keywords}\n"
                f"Example Queries:\n{examples}\n"
            )

        content_type_guidance = ""
        if content_type == ContentType.CODE:
            content_type_guidance = (
                "The user query contains code or code-like content. "
                "This might indicate a troubleshooting or maintenance request related to software or systems. "
                "Consider this in your classification."
            )
        elif content_type == ContentType.STRUCTURED_DATA:
            content_type_guidance = (
                "The user query contains structured data (like JSON, tables, or key-value pairs). "
                "This might indicate a request that involves specific data processing or analysis. "
                "Consider this in your classification."
            )

        content_type_section = f"{content_type_guidance}\n\n" if content_type_guidance else ""

        # Build the prompt in parts to avoid f-string issues
        base_prompt = (
            "You are a request classifier for the MAGPIE platform, which routes user queries to specialized agents. "
            "Your task is to analyze the user's query and determine which agent would be most appropriate to handle it. "
            "You must consider the content, intent, and context of the query.\n\n"
        )

        agents_section = "Available agents:\n\n" + "\n".join(agent_descriptions) + "\n\n"

        instructions = (
            "Instructions:\n"
            "1. Analyze the user's query carefully, considering both explicit and implicit needs.\n"
            "2. Consider any conversation history to maintain context continuity.\n"
            "3. Determine which agent type would be most appropriate based on the query content and intent.\n"
            "4. Provide a confidence score between 0.0 and 1.0, where 1.0 is absolute certainty.\n"
            "   - Score 0.9-1.0 for queries that clearly match an agent's capabilities\n"
            "   - Score 0.7-0.9 for queries that strongly align with an agent's domain\n"
            "   - Score 0.5-0.7 for queries that somewhat align but could be ambiguous\n"
            "   - Score 0.3-0.5 for queries where you're uncertain but have a best guess\n"
            "   - Score below 0.3 for highly ambiguous queries\n"
            "5. Explain your reasoning briefly, mentioning specific keywords or patterns that influenced your decision.\n\n"
        )

        response_format = (
            "Respond in the following JSON format only:\n"
            "{\n"
            '  "agent_type": "documentation|troubleshooting|maintenance",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "reasoning": "Brief explanation of why this agent is appropriate"\n'
            "}\n"
        )

        # Combine all parts
        prompt = base_prompt + content_type_section + agents_section + instructions + response_format

        return prompt

    def _parse_classification_response(
        self, response_content: str
    ) -> RequestClassification:
        """
        Parse the LLM response to extract classification.

        Args:
            response_content: LLM response content

        Returns:
            RequestClassification: Classification result
        """
        try:
            # Extract JSON from response
            import json
            import re

            # Find JSON pattern in the response
            json_match = re.search(r'({.*})', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                classification_data = json.loads(json_str)

                # Validate agent type
                agent_type_str = classification_data.get("agent_type", "").lower()
                agent_type = None

                if agent_type_str == "documentation":
                    agent_type = AgentType.DOCUMENTATION
                elif agent_type_str == "troubleshooting":
                    agent_type = AgentType.TROUBLESHOOTING
                elif agent_type_str == "maintenance":
                    agent_type = AgentType.MAINTENANCE
                else:
                    # Default to documentation if invalid agent type
                    agent_type = AgentType.DOCUMENTATION

                # Validate confidence
                confidence = float(classification_data.get("confidence", 0.5))
                confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1

                # Get reasoning
                reasoning = classification_data.get("reasoning", "No reasoning provided.")

                return RequestClassification(
                    agent_type=agent_type,
                    confidence=confidence,
                    reasoning=reasoning
                )
            else:
                # If no JSON found, default to documentation agent
                return RequestClassification(
                    agent_type=AgentType.DOCUMENTATION,
                    confidence=0.3,
                    reasoning="Failed to parse classification response, defaulting to documentation agent."
                )

        except Exception as e:
            logger.error(f"Error parsing classification response: {str(e)}")
            # Default to documentation agent if parsing fails
            return RequestClassification(
                agent_type=AgentType.DOCUMENTATION,
                confidence=0.3,
                reasoning="Failed to parse classification response, defaulting to documentation agent."
            )
