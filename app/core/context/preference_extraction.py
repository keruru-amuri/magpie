"""
User preference extraction for the MAGPIE platform.
"""
import logging
import re
import json
from typing import Dict, List, Optional, Union, Any, Set, Tuple

from app.models.context import UserPreference, ContextPriority
from app.models.conversation import Message, MessageRole
from app.services.llm_service import LLMService

# Configure logging
logger = logging.getLogger(__name__)


class PreferenceExtractor:
    """
    Extract user preferences from conversation messages.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize preference extractor.

        Args:
            llm_service: LLM service for preference extraction
        """
        self.llm_service = llm_service or LLMService()
        self.preference_patterns = [
            # Format preferences
            (r"(?:prefer|want|like)(?:\s+to\s+see)?\s+(\w+)\s+(?:format|style|output)", "preferred_format"),
            # Level of detail preferences
            (r"(?:prefer|want|like)\s+(\w+)\s+(?:details|information|explanation)", "detail_level"),
            # Aircraft type preferences
            (r"(?:working on|maintaining|flying)\s+(?:a|an)?\s+([A-Za-z0-9-]+)", "aircraft_type"),
            # System preferences
            (r"(?:focus on|interested in)\s+(?:the)?\s+([A-Za-z]+)\s+system", "system_focus"),
            # Role preferences
            (r"(?:I am|I'm)\s+(?:a|an)\s+([A-Za-z]+)", "user_role"),
        ]

    def extract_preferences_rule_based(self, message: Message) -> Dict[str, Tuple[str, float]]:
        """
        Extract preferences using rule-based patterns.

        Args:
            message: Message to extract preferences from

        Returns:
            Dict[str, Tuple[str, float]]: Dictionary of preference key to (value, confidence) tuples
        """
        if not message or not message.content or message.role != MessageRole.USER:
            return {}

        content = message.content.lower()
        preferences = {}

        for pattern, key in self.preference_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Use the first match
                value = matches[0].strip()
                # Simple confidence based on match length
                confidence = min(0.7, 0.5 + (len(value) / 20))
                preferences[key] = (value, confidence)

        return preferences

    async def extract_preferences_llm(self, message: Message) -> Dict[str, Tuple[str, float]]:
        """
        Extract preferences using LLM.

        Args:
            message: Message to extract preferences from

        Returns:
            Dict[str, Tuple[str, float]]: Dictionary of preference key to (value, confidence) tuples
        """
        try:
            if not message or not message.content or message.role != MessageRole.USER:
                return {}

            # Create prompt for preference extraction
            system_prompt = (
                "You are a preference extraction system for an aircraft maintenance AI assistant. "
                "Your task is to analyze user messages and extract any explicit or implicit preferences "
                "the user might have. Focus on preferences related to:\n"
                "1. Format preferences (how they want information presented)\n"
                "2. Detail level preferences (how much detail they want)\n"
                "3. Aircraft type preferences (what aircraft they're working with)\n"
                "4. System focus preferences (what aircraft systems they're interested in)\n"
                "5. User role preferences (their job or role)\n"
                "6. Any other relevant preferences\n\n"
                "Respond with a JSON object where keys are preference categories (use snake_case) and "
                "values are objects with 'value' and 'confidence' properties. The confidence should be "
                "between 0.0 and 1.0, where 1.0 is highest confidence."
            )

            user_prompt = f"Extract preferences from this user message:\n\n{message.content}"

            # Generate preferences
            response = await self.llm_service.generate_completion_raw(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4.1-mini",
                max_tokens=500,
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            if not response or not response.get("content"):
                logger.error("Failed to generate preferences with LLM")
                return {}

            # Parse JSON response
            try:
                content = response["content"]
                prefs_data = json.loads(content)

                # Convert to the expected format
                preferences = {}
                for key, data in prefs_data.items():
                    if isinstance(data, dict) and "value" in data and "confidence" in data:
                        value = str(data["value"]).lower().strip()
                        confidence = float(data["confidence"])
                        if value:
                            preferences[key] = (value, confidence)

                return preferences
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {content}")
                return {}
            except Exception as e:
                logger.error(f"Error processing LLM preferences: {str(e)}")
                return {}
        except Exception as e:
            logger.error(f"Error extracting preferences with LLM: {str(e)}")
            return {}

    async def extract_preferences(
        self,
        message: Message,
        use_llm: bool = True
    ) -> Dict[str, Tuple[str, float]]:
        """
        Extract preferences using both rule-based and LLM approaches.

        Args:
            message: Message to extract preferences from
            use_llm: Whether to use LLM for extraction

        Returns:
            Dict[str, Tuple[str, float]]: Dictionary of preference key to (value, confidence) tuples
        """
        # Start with rule-based extraction
        preferences = self.extract_preferences_rule_based(message)

        # Add LLM-based extraction if enabled
        if use_llm:
            llm_preferences = await self.extract_preferences_llm(message)

            # Merge preferences, preferring higher confidence values
            for key, (value, confidence) in llm_preferences.items():
                if key not in preferences or preferences[key][1] < confidence:
                    preferences[key] = (value, confidence)

        return preferences


class PreferenceManager:
    """
    Manage user preferences.
    """

    def __init__(
        self,
        context_service: Any,
        llm_service: Optional[LLMService] = None
    ):
        """
        Initialize preference manager.

        Args:
            context_service: Context service for storing preferences
            llm_service: LLM service for preference extraction
        """
        self.context_service = context_service
        self.extractor = PreferenceExtractor(llm_service)

    async def process_message(
        self,
        message: Message,
        use_llm: bool = True,
        add_to_context: bool = True
    ) -> List[UserPreference]:
        """
        Process a message to extract and store preferences.

        Args:
            message: Message to process
            use_llm: Whether to use LLM for extraction
            add_to_context: Whether to add preferences to context

        Returns:
            List[UserPreference]: List of extracted preferences
        """
        try:
            # Extract preferences
            preferences = await self.extractor.extract_preferences(message, use_llm)
            if not preferences:
                return []

            # Store preferences
            stored_prefs = []
            for key, (value, confidence) in preferences.items():
                preference = self.context_service.extract_user_preference(
                    message_id=message.id,
                    key=key,
                    value=value,
                    confidence=confidence
                )
                if preference:
                    stored_prefs.append(preference)

            # Add to context if requested
            if add_to_context and stored_prefs:
                self.context_service.add_user_preferences_to_context(
                    conversation_id=message.conversation_id,
                    priority=ContextPriority.HIGH
                )

            return stored_prefs
        except Exception as e:
            logger.error(f"Error processing message for preferences: {str(e)}")
            return []

    def get_user_preferences(self, user_id: int) -> Dict[str, str]:
        """
        Get all preferences for a user.

        Args:
            user_id: User ID

        Returns:
            Dict[str, str]: Dictionary of preference key to value
        """
        try:
            preferences = self.context_service.preference_repo.get_preferences_for_user(user_id)
            return {pref.preference_key: pref.preference_value for pref in preferences}
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}

    def get_preference(self, user_id: int, key: str) -> Optional[str]:
        """
        Get a specific preference for a user.

        Args:
            user_id: User ID
            key: Preference key

        Returns:
            Optional[str]: Preference value or None if not found
        """
        try:
            preference = self.context_service.preference_repo.get_preference(user_id, key)
            return preference.preference_value if preference else None
        except Exception as e:
            logger.error(f"Error getting preference: {str(e)}")
            return None

    def set_preference(
        self,
        user_id: int,
        key: str,
        value: str,
        confidence: float = 1.0,
        source_message_id: Optional[int] = None
    ) -> Optional[UserPreference]:
        """
        Set a preference for a user.

        Args:
            user_id: User ID
            key: Preference key
            value: Preference value
            confidence: Confidence level
            source_message_id: Source message ID

        Returns:
            Optional[UserPreference]: Created or updated preference
        """
        try:
            return self.context_service.preference_repo.set_preference(
                user_id=user_id,
                key=key,
                value=value,
                confidence=confidence,
                source_message_id=source_message_id
            )
        except Exception as e:
            logger.error(f"Error setting preference: {str(e)}")
            return None
