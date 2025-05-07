"""
Context tagging utilities for the MAGPIE platform.
"""
import logging
import re
import json
import asyncio
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from app.models.context import ContextItem, ContextTag, ContextType
from app.repositories.context import ContextTagRepository
from app.services.llm_service import LLMService

# Configure logging
logger = logging.getLogger(__name__)


class TagExtractor:
    """
    Base class for tag extractors.
    """

    def extract_tags(self, content: str) -> Dict[str, str]:
        """
        Extract tags from content.

        Args:
            content: Content to extract tags from

        Returns:
            Dict[str, str]: Dictionary of extracted tags
        """
        return {}


class EntityTagExtractor(TagExtractor):
    """
    Extract entity tags from content.

    Identifies entities like aircraft models, part numbers, etc.
    """

    # Common aircraft models
    AIRCRAFT_MODELS = {
        "737": "boeing",
        "747": "boeing",
        "757": "boeing",
        "767": "boeing",
        "777": "boeing",
        "787": "boeing",
        "a320": "airbus",
        "a330": "airbus",
        "a340": "airbus",
        "a350": "airbus",
        "a380": "airbus",
        "crj": "bombardier",
        "embraer": "embraer",
        "e-jet": "embraer",
        "dash 8": "bombardier",
        "cessna": "cessna",
        "beechcraft": "beechcraft",
        "gulfstream": "gulfstream"
    }

    # Part number patterns
    PART_NUMBER_PATTERNS = [
        r'\b[A-Z]{2,3}-\d{4,6}\b',  # XX-12345
        r'\b\d{3}-\d{4,6}\b',       # 123-12345
        r'\b[A-Z]\d{4,6}\b',        # A12345
        r'\b[A-Z]{2}\d{4,6}\b'      # AB12345
    ]

    def extract_tags(self, content: str) -> Dict[str, str]:
        """
        Extract entity tags from content.

        Args:
            content: Content to extract tags from

        Returns:
            Dict[str, str]: Dictionary of extracted tags
        """
        tags = {}

        # Extract aircraft models
        for model, manufacturer in self.AIRCRAFT_MODELS.items():
            if re.search(r'\b' + re.escape(model) + r'\b', content.lower()):
                tags["aircraft_model"] = model
                tags["manufacturer"] = manufacturer
                break

        # Extract part numbers
        for pattern in self.PART_NUMBER_PATTERNS:
            match = re.search(pattern, content)
            if match:
                tags["part_number"] = match.group(0)
                break

        return tags


class KeywordTagExtractor(TagExtractor):
    """
    Extract keyword tags from content.

    Identifies important keywords and topics.
    """

    # Common maintenance topics
    MAINTENANCE_TOPICS = {
        "inspection": ["inspect", "inspection", "check", "examine"],
        "repair": ["repair", "fix", "restore", "mend"],
        "replacement": ["replace", "swap", "substitute", "exchange"],
        "troubleshooting": ["troubleshoot", "diagnose", "debug", "fault"],
        "installation": ["install", "mount", "fit", "attach"],
        "removal": ["remove", "detach", "disconnect", "uninstall"],
        "testing": ["test", "verify", "validate", "check"],
        "calibration": ["calibrate", "adjust", "tune", "align"],
        "lubrication": ["lubricate", "oil", "grease", "lubricant"],
        "cleaning": ["clean", "wash", "flush", "purge"]
    }

    # Aircraft systems
    AIRCRAFT_SYSTEMS = {
        "hydraulic": ["hydraulic", "fluid", "pressure", "actuator"],
        "electrical": ["electrical", "circuit", "wiring", "power"],
        "avionics": ["avionics", "instrument", "display", "computer"],
        "fuel": ["fuel", "tank", "pump", "line"],
        "landing_gear": ["landing gear", "wheel", "brake", "strut"],
        "engine": ["engine", "turbine", "compressor", "combustion"],
        "pneumatic": ["pneumatic", "air", "pressure", "valve"],
        "environmental": ["environmental", "air conditioning", "pressurization", "temperature"]
    }

    def extract_tags(self, content: str) -> Dict[str, str]:
        """
        Extract keyword tags from content.

        Args:
            content: Content to extract tags from

        Returns:
            Dict[str, str]: Dictionary of extracted tags
        """
        tags = {}
        content_lower = content.lower()

        # Extract maintenance topics
        for topic, keywords in self.MAINTENANCE_TOPICS.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower):
                    tags["maintenance_topic"] = topic
                    break
            if "maintenance_topic" in tags:
                break

        # Extract aircraft systems
        for system, keywords in self.AIRCRAFT_SYSTEMS.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower):
                    tags["aircraft_system"] = system
                    break
            if "aircraft_system" in tags:
                break

        return tags


class SentimentTagExtractor(TagExtractor):
    """
    Extract sentiment tags from content.

    Identifies positive, negative, or neutral sentiment.
    """

    # Sentiment keywords
    POSITIVE_KEYWORDS = [
        "good", "great", "excellent", "perfect", "successful", "resolved",
        "fixed", "working", "operational", "functional", "effective",
        "efficient", "reliable", "stable", "improved", "enhanced"
    ]

    NEGATIVE_KEYWORDS = [
        "bad", "poor", "failed", "broken", "damaged", "faulty", "defective",
        "error", "issue", "problem", "malfunction", "failure", "incorrect",
        "unstable", "unreliable", "degraded", "compromised"
    ]

    NEUTRAL_KEYWORDS = [
        "normal", "standard", "typical", "regular", "routine", "common",
        "usual", "expected", "nominal", "average", "moderate", "acceptable"
    ]

    def extract_tags(self, content: str) -> Dict[str, str]:
        """
        Extract sentiment tags from content.

        Args:
            content: Content to extract tags from

        Returns:
            Dict[str, str]: Dictionary of extracted tags
        """
        tags = {}
        content_lower = content.lower()

        # Count sentiment keywords
        positive_count = sum(1 for keyword in self.POSITIVE_KEYWORDS
                            if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower))

        negative_count = sum(1 for keyword in self.NEGATIVE_KEYWORDS
                            if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower))

        neutral_count = sum(1 for keyword in self.NEUTRAL_KEYWORDS
                           if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower))

        # Determine overall sentiment
        if positive_count > negative_count and positive_count > neutral_count:
            tags["sentiment"] = "positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            tags["sentiment"] = "negative"
        elif neutral_count > 0:
            tags["sentiment"] = "neutral"

        return tags


class LLMTagExtractor(TagExtractor):
    """
    Extract tags using LLM.

    Uses an LLM to identify topics, entities, and other relevant tags.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize LLM tag extractor.

        Args:
            llm_service: LLM service for tag extraction
        """
        self.llm_service = llm_service or LLMService()

    async def extract_tags_async(self, content: str) -> Dict[str, str]:
        """
        Extract tags from content using LLM.

        Args:
            content: Content to extract tags from

        Returns:
            Dict[str, str]: Dictionary of extracted tags
        """
        try:
            # Truncate content if too long
            if len(content) > 2000:
                content = content[:2000] + "..."

            # Create prompt for tag extraction
            system_prompt = (
                "You are a metadata tagging system for an aircraft maintenance AI assistant. "
                "Your task is to analyze text and extract relevant tags in the following categories:\n"
                "1. Topics: The main subjects discussed (e.g., hydraulic system, engine maintenance)\n"
                "2. Aircraft: Any mentioned aircraft models or types\n"
                "3. Components: Specific parts or components mentioned\n"
                "4. Maintenance: Types of maintenance activities discussed\n"
                "5. Technical: Technical concepts or procedures mentioned\n\n"
                "Respond with a JSON object containing these categories as keys and the extracted tags as values. "
                "Keep tags concise (1-3 words) and relevant to aircraft maintenance."
            )

            user_prompt = f"Extract relevant tags from this text:\n\n{content}"

            # Generate tags
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
                logger.error("Failed to generate tags with LLM")
                return {}

            # Parse JSON response
            try:
                content = response["content"]
                tags_data = json.loads(content)

                # Flatten the tags
                tags = {}
                for category, values in tags_data.items():
                    if isinstance(values, list):
                        for i, value in enumerate(values):
                            if value and isinstance(value, str):
                                tags[f"{category.lower()}_{i+1}"] = value.lower()
                    elif isinstance(values, str) and values:
                        tags[category.lower()] = values.lower()

                return tags
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {content}")
                return {}
            except Exception as e:
                logger.error(f"Error processing LLM tags: {str(e)}")
                return {}
        except Exception as e:
            logger.error(f"Error extracting tags with LLM: {str(e)}")
            return {}

    def extract_tags(self, content: str) -> Dict[str, str]:
        """
        Synchronous wrapper for extract_tags_async.

        Note: This will return an empty dict. Use extract_tags_async for actual tag extraction.

        Args:
            content: Content to extract tags from

        Returns:
            Dict[str, str]: Empty dictionary (async method should be used instead)
        """
        logger.warning("LLMTagExtractor.extract_tags called synchronously, which is not supported")
        return {}


class TagManager:
    """
    Manager for context item tagging.
    """

    def __init__(self, tag_repo: ContextTagRepository, llm_service: Optional[LLMService] = None):
        """
        Initialize tag manager.

        Args:
            tag_repo: Context tag repository
            llm_service: LLM service for tag extraction
        """
        self.tag_repo = tag_repo
        self.llm_service = llm_service or LLMService()
        self.extractors = [
            EntityTagExtractor(),
            KeywordTagExtractor(),
            SentimentTagExtractor()
        ]
        self.llm_extractor = LLMTagExtractor(self.llm_service)

    def tag_item(self, item: ContextItem) -> List[ContextTag]:
        """
        Tag a context item.

        Args:
            item: Context item to tag

        Returns:
            List[ContextTag]: List of created tags
        """
        try:
            # Get content
            content = item.content
            if not content and item.message_id:
                # Get content from message
                from app.core.db.connection import DatabaseConnectionFactory
                with DatabaseConnectionFactory.session_context() as session:
                    from app.models.conversation import Message
                    message = session.get(Message, item.message_id)
                    if message:
                        content = message.content

            if not content:
                logger.warning(f"No content to tag for item {item.id}")
                return []

            # Extract tags using rule-based extractors
            all_tags = {}
            for extractor in self.extractors:
                tags = extractor.extract_tags(content)
                all_tags.update(tags)

            # Add tags to item
            created_tags = []
            for key, value in all_tags.items():
                tag = self.tag_repo.add_tag(
                    item_id=item.id,
                    key=key,
                    value=value
                )
                if tag:
                    created_tags.append(tag)

            return created_tags
        except Exception as e:
            logger.error(f"Error tagging item: {str(e)}")
            return []

    async def tag_item_with_llm(self, item: ContextItem) -> List[ContextTag]:
        """
        Tag a context item using LLM.

        Args:
            item: Context item to tag

        Returns:
            List[ContextTag]: List of created tags
        """
        try:
            # Get content
            content = item.content
            if not content and item.message_id:
                # Get content from message
                from app.core.db.connection import DatabaseConnectionFactory
                with DatabaseConnectionFactory.session_context() as session:
                    from app.models.conversation import Message
                    message = session.get(Message, item.message_id)
                    if message:
                        content = message.content

            if not content:
                logger.warning(f"No content to tag for item {item.id}")
                return []

            # Extract tags using LLM
            llm_tags = await self.llm_extractor.extract_tags_async(content)

            # Add tags to item
            created_tags = []
            for key, value in llm_tags.items():
                tag = self.tag_repo.add_tag(
                    item_id=item.id,
                    key=key,
                    value=value
                )
                if tag:
                    created_tags.append(tag)

            return created_tags
        except Exception as e:
            logger.error(f"Error tagging item with LLM: {str(e)}")
            return []

    def tag_item_complete(self, item: ContextItem, use_llm: bool = True) -> List[ContextTag]:
        """
        Tag a context item using both rule-based and LLM-based extractors.

        Args:
            item: Context item to tag
            use_llm: Whether to use LLM-based tagging

        Returns:
            List[ContextTag]: List of created tags
        """
        # First use rule-based tagging
        tags = self.tag_item(item)

        # If LLM tagging is enabled, run it asynchronously
        if use_llm:
            try:
                # Create event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Run LLM tagging
                llm_tags = loop.run_until_complete(self.tag_item_with_llm(item))
                tags.extend(llm_tags)
            except Exception as e:
                logger.error(f"Error running LLM tagging: {str(e)}")

        return tags

    def get_tags(self, item_id: int) -> Dict[str, str]:
        """
        Get tags for a context item.

        Args:
            item_id: Context item ID

        Returns:
            Dict[str, str]: Dictionary of tags
        """
        try:
            tags = self.tag_repo.get_tags_for_item(item_id)
            return {tag.tag_key: tag.tag_value for tag in tags}
        except Exception as e:
            logger.error(f"Error getting tags: {str(e)}")
            return {}
