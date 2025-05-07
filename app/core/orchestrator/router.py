"""
Request router for the MAGPIE platform.

This module provides functionality for routing user requests to the
appropriate agent based on classification results.
"""
import logging
import re
from typing import Dict, List, Optional

from app.models.conversation import AgentType
from app.models.orchestrator import (
    ClassificationConfidence,
    RequestClassification,
    RoutingResult,
)
from app.core.orchestrator.registry import AgentRegistry

# Configure logging
logger = logging.getLogger(__name__)


class Router:
    """
    Router for directing requests to appropriate agents.
    """

    def __init__(self, agent_registry: AgentRegistry):
        """
        Initialize the router.

        Args:
            agent_registry: Registry of available agents
        """
        self.agent_registry = agent_registry
        self._routing_history: Dict[str, List[RoutingResult]] = {}  # Conversation ID -> routing history

    async def route_request(
        self,
        classification: RequestClassification,
        conversation_id: Optional[str] = None,
        query: Optional[str] = None,
        context: Optional[Dict[str, str]] = None
    ) -> RoutingResult:
        """
        Route a request based on classification results.

        Args:
            classification: Classification result
            conversation_id: Optional conversation ID for context
            query: Optional original query text for advanced routing
            context: Optional additional context for routing decisions

        Returns:
            RoutingResult: Routing result
        """
        try:
            agent_type = classification.agent_type
            confidence_level = classification.confidence_level

            # Extract keywords from query if available
            keywords = self._extract_keywords(query) if query else []

            # Try to find the best agent based on capabilities if we have keywords
            primary_agent = None
            if keywords:
                matching_agents = self.agent_registry.find_agents_by_capability(keywords)
                if matching_agents and matching_agents[0][1] > 0:  # If we have matches with positive score
                    # Filter to agents of the classified type
                    type_matches = [(agent, score) for agent, score in matching_agents
                                   if agent.agent_type == agent_type]

                    if type_matches:
                        primary_agent = type_matches[0][0]
                        logger.info(f"Selected agent {primary_agent.name} based on capability matching")

            # If no agent found by capability matching, get the default agent
            if not primary_agent:
                primary_agent = self.agent_registry.get_default_agent(agent_type)

            if not primary_agent:
                logger.warning(f"No agent found for type {agent_type}. Using documentation agent as fallback.")
                fallback_agent = self.agent_registry.get_default_agent(AgentType.DOCUMENTATION)

                if not fallback_agent:
                    raise ValueError("No fallback agent available")

                return RoutingResult(
                    agent_type=AgentType.DOCUMENTATION,
                    agent_config_id=fallback_agent.config_id,
                    classification=classification,
                    requires_followup=False,
                    requires_multiple_agents=False
                )

            # Determine if we need a fallback agent based on confidence
            fallback_agent_config_id = None
            requires_followup = False

            if confidence_level == ClassificationConfidence.LOW:
                # For low confidence, prepare a fallback agent
                fallback_agent = self._get_fallback_agent(agent_type, keywords)
                if fallback_agent:
                    fallback_agent_config_id = fallback_agent.config_id
                    requires_followup = True

            # Determine if multiple agents are needed
            requires_multiple_agents = False
            additional_agent_types = None

            # Check if this is a complex query that might need multiple agents
            if self._is_complex_query(classification, query):
                requires_multiple_agents = True
                additional_agent_types = self._determine_additional_agents(classification, keywords)

            # Check conversation history for context continuity if available
            if conversation_id and conversation_id in self._routing_history:
                # Get the most recent routing result for this conversation
                prev_routing = self._routing_history[conversation_id][-1]

                # If the confidence is medium or low and the previous agent type is different,
                # consider maintaining continuity by using the previous agent
                if (confidence_level in [ClassificationConfidence.LOW, ClassificationConfidence.MEDIUM] and
                    prev_routing.agent_type != agent_type and
                    self._is_followup_query(query)):

                    logger.info(f"Maintaining conversation continuity with agent type {prev_routing.agent_type}")

                    # Use the previous agent type but keep the current classification
                    prev_agent_type = prev_routing.agent_type
                    prev_agent = self.agent_registry.get_default_agent(prev_agent_type)

                    if prev_agent:
                        # Create a routing result that maintains continuity
                        continuity_result = RoutingResult(
                            agent_type=prev_agent_type,
                            agent_config_id=prev_agent.config_id,
                            classification=classification,  # Keep current classification
                            fallback_agent_config_id=primary_agent.config_id,  # Use classified agent as fallback
                            requires_followup=True,  # We might need to follow up with the classified agent
                            requires_multiple_agents=requires_multiple_agents,
                            additional_agent_types=additional_agent_types
                        )

                        # Store in routing history
                        self._add_to_routing_history(conversation_id, continuity_result)

                        return continuity_result

            # Create the routing result
            result = RoutingResult(
                agent_type=agent_type,
                agent_config_id=primary_agent.config_id,
                classification=classification,
                fallback_agent_config_id=fallback_agent_config_id,
                requires_followup=requires_followup,
                requires_multiple_agents=requires_multiple_agents,
                additional_agent_types=additional_agent_types
            )

            # Store in routing history if conversation ID is provided
            if conversation_id:
                self._add_to_routing_history(conversation_id, result)

            return result

        except Exception as e:
            logger.error(f"Error routing request: {str(e)}")
            # Default to documentation agent if routing fails
            fallback_agent = self.agent_registry.get_default_agent(AgentType.DOCUMENTATION)

            if not fallback_agent:
                raise ValueError("No fallback agent available")

            result = RoutingResult(
                agent_type=AgentType.DOCUMENTATION,
                agent_config_id=fallback_agent.config_id,
                classification=classification,
                requires_followup=False,
                requires_multiple_agents=False
            )

            # Store in routing history if conversation ID is provided
            if conversation_id:
                self._add_to_routing_history(conversation_id, result)

            return result

    def _add_to_routing_history(self, conversation_id: str, routing_result: RoutingResult) -> None:
        """
        Add a routing result to the routing history for a conversation.

        Args:
            conversation_id: Conversation ID
            routing_result: Routing result to add
        """
        if conversation_id not in self._routing_history:
            self._routing_history[conversation_id] = []

        # Limit history size to prevent memory issues
        if len(self._routing_history[conversation_id]) >= 10:
            self._routing_history[conversation_id].pop(0)

        self._routing_history[conversation_id].append(routing_result)

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from a query for capability matching.

        Args:
            query: User query

        Returns:
            List[str]: List of extracted keywords
        """
        if not query:
            return []

        # Remove common stop words
        stop_words = {
            "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
            "when", "where", "how", "why", "which", "who", "whom", "this", "that",
            "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "having", "do", "does", "did", "doing", "can", "could",
            "should", "would", "shall", "will", "may", "might", "must", "to", "for", "with",
            "about", "against", "between", "into", "through", "during", "before", "after",
            "above", "below", "from", "up", "down", "in", "out", "on", "off", "over", "under",
            "again", "further", "then", "once", "here", "there", "all", "any", "both", "each",
            "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "just", "don", "don't", "should've", "now"
        }

        # Tokenize and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        # Add bigrams (pairs of adjacent words)
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in stop_words or words[i+1] not in stop_words:
                bigram = f"{words[i]} {words[i+1]}"
                bigrams.append(bigram)

        # Combine and return unique keywords
        all_keywords = keywords + bigrams
        return list(set(all_keywords))

    def _get_fallback_agent(self, primary_agent_type: AgentType, keywords: Optional[List[str]] = None):
        """
        Get a fallback agent for a primary agent type.

        Args:
            primary_agent_type: Primary agent type
            keywords: Optional list of keywords for capability matching

        Returns:
            Optional[AgentMetadata]: Fallback agent metadata or None
        """
        # Try to find a fallback agent based on capabilities if we have keywords
        if keywords:
            # Get all agents except those of the primary type
            all_agents = self.agent_registry.get_all_agents()
            other_agents = [agent for agent in all_agents if agent.agent_type != primary_agent_type]

            # Create a temporary capability index
            capability_index = {}
            for agent in other_agents:
                if not agent.config_id:
                    continue

                for capability in agent.capabilities:
                    for keyword in capability.keywords:
                        keyword_lower = keyword.lower()
                        if keyword_lower not in capability_index:
                            capability_index[keyword_lower] = []
                        capability_index[keyword_lower].append(agent)

            # Find matching agents
            matches = {}
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in capability_index:
                    for agent in capability_index[keyword_lower]:
                        if agent.config_id not in matches:
                            matches[agent.config_id] = 0
                        matches[agent.config_id] += 1

            # Get the agent with the highest match count
            if matches:
                best_agent_id = max(matches.items(), key=lambda x: x[1])[0]
                for agent in other_agents:
                    if agent.config_id == best_agent_id:
                        return agent

        # Default fallback logic
        if primary_agent_type == AgentType.DOCUMENTATION:
            # For documentation, try troubleshooting as fallback
            return self.agent_registry.get_default_agent(AgentType.TROUBLESHOOTING)

        # For all other types, fallback to documentation
        return self.agent_registry.get_default_agent(AgentType.DOCUMENTATION)

    def _is_complex_query(self, classification: RequestClassification, query: Optional[str] = None) -> bool:
        """
        Determine if a query is complex and might need multiple agents.

        Args:
            classification: Classification result
            query: Optional original query text for additional analysis

        Returns:
            bool: True if the query is complex, False otherwise
        """
        # Check confidence level
        if classification.confidence_level == ClassificationConfidence.MEDIUM:
            return True

        # If we have the query text, check for complexity indicators
        if query:
            # Check query length (long queries are often complex)
            if len(query) > 150:
                return True

            # Check for multiple questions
            question_marks = query.count('?')
            if question_marks > 1:
                return True

            # Check for conjunctions that might indicate multiple parts
            conjunctions = ['and', 'also', 'additionally', 'moreover', 'furthermore', 'as well as', 'plus']
            if any(conj in query.lower() for conj in conjunctions):
                return True

            # Check for phrases that indicate complex requests
            complex_indicators = [
                'compare', 'difference between', 'pros and cons', 'advantages and disadvantages',
                'step by step', 'procedure', 'troubleshoot', 'diagnose', 'both', 'multiple'
            ]
            if any(indicator in query.lower() for indicator in complex_indicators):
                return True

        return False

    def _determine_additional_agents(
        self, classification: RequestClassification, keywords: Optional[List[str]] = None
    ) -> List[AgentType]:
        """
        Determine additional agents that might be needed for a complex query.

        Args:
            classification: Classification result
            keywords: Optional list of keywords for capability matching

        Returns:
            List[AgentType]: List of additional agent types
        """
        primary_type = classification.agent_type
        additional_types = []

        # Try to find additional agents based on capabilities if we have keywords
        if keywords:
            # Get matching agents from all types except the primary type
            matching_agents = self.agent_registry.find_agents_by_capability(keywords)

            # Filter out the primary type and get the top 2 other types
            other_types = set()
            for agent, _ in matching_agents:
                if agent.agent_type != primary_type:
                    other_types.add(agent.agent_type)
                    if len(other_types) >= 2:  # Limit to 2 additional types
                        break

            additional_types = list(other_types)

        # If no additional types found through capability matching, use default logic
        if not additional_types:
            if primary_type == AgentType.DOCUMENTATION:
                # Documentation queries might also need troubleshooting
                additional_types.append(AgentType.TROUBLESHOOTING)

            elif primary_type == AgentType.TROUBLESHOOTING:
                # Troubleshooting queries might also need documentation and maintenance
                additional_types.append(AgentType.DOCUMENTATION)
                additional_types.append(AgentType.MAINTENANCE)

            elif primary_type == AgentType.MAINTENANCE:
                # Maintenance queries might also need documentation
                additional_types.append(AgentType.DOCUMENTATION)

        return additional_types

    def _is_followup_query(self, query: Optional[str] = None) -> bool:
        """
        Determine if a query is likely a followup to a previous query.

        Args:
            query: Optional query text to analyze

        Returns:
            bool: True if the query is likely a followup, False otherwise
        """
        if not query:
            return False

        # Check for pronouns and references that indicate a followup
        followup_indicators = [
            r'\b(it|this|that|these|those|they|them|their|he|she|his|her)\b',
            r'\b(the same|the above|the previous|the earlier)\b',
            r'^(and|but|so|also|what about|how about)\b',
            r'^(can you|could you|would you|will you)\b',
            r'\b(more|additional|further|else|another|again)\b'
        ]

        for pattern in followup_indicators:
            if re.search(pattern, query.lower()):
                return True

        # Check for very short queries (often followups)
        if len(query.split()) <= 3:
            return True

        return False

    def clear_routing_history(self, conversation_id: Optional[str] = None) -> None:
        """
        Clear routing history for a conversation or all conversations.

        Args:
            conversation_id: Optional conversation ID to clear history for.
                            If None, clears history for all conversations.
        """
        if conversation_id:
            if conversation_id in self._routing_history:
                del self._routing_history[conversation_id]
        else:
            self._routing_history.clear()

    def get_routing_history(self, conversation_id: str) -> List[RoutingResult]:
        """
        Get routing history for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List[RoutingResult]: List of routing results for the conversation
        """
        return self._routing_history.get(conversation_id, [])
