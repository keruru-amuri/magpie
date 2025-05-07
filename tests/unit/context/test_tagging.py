"""
Unit tests for context tagging.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock

from app.core.context.tagging import (
    TagExtractor, EntityTagExtractor, KeywordTagExtractor,
    SentimentTagExtractor, LLMTagExtractor, TagManager
)
from app.models.context import ContextItem, ContextTag
from app.repositories.context import ContextTagRepository
from app.services.llm_service import LLMService


class TestTagExtractors:
    """
    Test tag extractors.
    """
    
    def test_entity_tag_extractor(self):
        """
        Test entity tag extractor.
        """
        extractor = EntityTagExtractor()
        
        # Test with aircraft model
        content = "I'm working on a Boeing 737 and need help with the hydraulic system."
        tags = extractor.extract_tags(content)
        assert "aircraft_model" in tags
        assert tags["aircraft_model"] == "737"
        assert "manufacturer" in tags
        assert tags["manufacturer"] == "boeing"
        
        # Test with part number
        content = "The part number is ABC-12345 and I need to replace it."
        tags = extractor.extract_tags(content)
        assert "part_number" in tags
        assert tags["part_number"] == "ABC-12345"
    
    def test_keyword_tag_extractor(self):
        """
        Test keyword tag extractor.
        """
        extractor = KeywordTagExtractor()
        
        # Test with maintenance topic
        content = "I need to inspect the landing gear before the next flight."
        tags = extractor.extract_tags(content)
        assert "maintenance_topic" in tags
        assert tags["maintenance_topic"] == "inspection"
        
        # Test with aircraft system
        content = "The hydraulic pressure is dropping during operation."
        tags = extractor.extract_tags(content)
        assert "aircraft_system" in tags
        assert tags["aircraft_system"] == "hydraulic"
    
    def test_sentiment_tag_extractor(self):
        """
        Test sentiment tag extractor.
        """
        extractor = SentimentTagExtractor()
        
        # Test with positive sentiment
        content = "The repair was successful and the system is now working perfectly."
        tags = extractor.extract_tags(content)
        assert "sentiment" in tags
        assert tags["sentiment"] == "positive"
        
        # Test with negative sentiment
        content = "The component is broken and needs to be replaced."
        tags = extractor.extract_tags(content)
        assert "sentiment" in tags
        assert tags["sentiment"] == "negative"
        
        # Test with neutral sentiment
        content = "This is a standard maintenance procedure for the aircraft."
        tags = extractor.extract_tags(content)
        assert "sentiment" in tags
        assert tags["sentiment"] == "neutral"


class TestLLMTagExtractor:
    """
    Test LLM tag extractor.
    """
    
    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        service = MagicMock(spec=LLMService)
        service.generate_completion_raw = AsyncMock(return_value={
            "content": json.dumps({
                "Topics": ["hydraulic system", "pressure drop"],
                "Aircraft": "Boeing 737",
                "Components": ["hydraulic pump", "pressure valve"],
                "Maintenance": "troubleshooting",
                "Technical": "pressure regulation"
            })
        })
        return service
    
    @pytest.fixture
    def llm_extractor(self, mock_llm_service):
        """
        Create an LLM tag extractor.
        """
        return LLMTagExtractor(mock_llm_service)
    
    @pytest.mark.asyncio
    async def test_extract_tags_async(self, llm_extractor, mock_llm_service):
        """
        Test extracting tags asynchronously.
        """
        # Call extract_tags_async
        content = "I'm experiencing a pressure drop in the hydraulic system of a Boeing 737."
        tags = await llm_extractor.extract_tags_async(content)
        
        # Verify result
        assert "topics_1" in tags
        assert "aircraft" in tags
        assert "components_1" in tags
        assert "maintenance" in tags
        assert "technical" in tags
        
        # Verify LLM service was called
        mock_llm_service.generate_completion_raw.assert_called_once()
    
    def test_extract_tags(self, llm_extractor):
        """
        Test extracting tags synchronously.
        """
        # Call extract_tags
        content = "I'm experiencing a pressure drop in the hydraulic system of a Boeing 737."
        tags = llm_extractor.extract_tags(content)
        
        # Verify result is empty (synchronous method returns empty dict)
        assert tags == {}


class TestTagManager:
    """
    Test tag manager.
    """
    
    @pytest.fixture
    def mock_tag_repo(self):
        """
        Create a mock tag repository.
        """
        repo = MagicMock(spec=ContextTagRepository)
        repo.add_tag = MagicMock(return_value=MagicMock(spec=ContextTag))
        repo.get_tags_for_item = MagicMock(return_value=[
            MagicMock(spec=ContextTag, tag_key="aircraft_model", tag_value="737"),
            MagicMock(spec=ContextTag, tag_key="manufacturer", tag_value="boeing")
        ])
        return repo
    
    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        service = MagicMock(spec=LLMService)
        service.generate_completion_raw = AsyncMock(return_value={
            "content": json.dumps({
                "Topics": ["hydraulic system"],
                "Aircraft": "Boeing 737"
            })
        })
        return service
    
    @pytest.fixture
    def tag_manager(self, mock_tag_repo, mock_llm_service):
        """
        Create a tag manager.
        """
        return TagManager(mock_tag_repo, mock_llm_service)
    
    @pytest.fixture
    def mock_item(self):
        """
        Create a mock context item.
        """
        return MagicMock(
            spec=ContextItem,
            id=1,
            content="I'm experiencing a pressure drop in the hydraulic system of a Boeing 737.",
            message_id=None
        )
    
    def test_tag_item(self, tag_manager, mock_item, mock_tag_repo):
        """
        Test tagging an item.
        """
        # Call tag_item
        tags = tag_manager.tag_item(mock_item)
        
        # Verify result
        assert len(tags) > 0
        
        # Verify tag_repo.add_tag was called
        assert mock_tag_repo.add_tag.call_count > 0
    
    @pytest.mark.asyncio
    async def test_tag_item_with_llm(self, tag_manager, mock_item, mock_tag_repo):
        """
        Test tagging an item with LLM.
        """
        # Call tag_item_with_llm
        tags = await tag_manager.tag_item_with_llm(mock_item)
        
        # Verify result
        assert len(tags) > 0
        
        # Verify tag_repo.add_tag was called
        assert mock_tag_repo.add_tag.call_count > 0
    
    def test_tag_item_complete(self, tag_manager, mock_item):
        """
        Test complete tagging of an item.
        """
        # Mock tag_item
        with patch.object(TagManager, 'tag_item', return_value=[MagicMock(spec=ContextTag)]):
            # Mock tag_item_with_llm
            with patch.object(TagManager, 'tag_item_with_llm', AsyncMock(return_value=[MagicMock(spec=ContextTag)])):
                # Call tag_item_complete
                tags = tag_manager.tag_item_complete(mock_item)
                
                # Verify result
                assert len(tags) > 0
    
    def test_get_tags(self, tag_manager, mock_tag_repo):
        """
        Test getting tags.
        """
        # Call get_tags
        tags = tag_manager.get_tags(1)
        
        # Verify result
        assert "aircraft_model" in tags
        assert tags["aircraft_model"] == "737"
        assert "manufacturer" in tags
        assert tags["manufacturer"] == "boeing"
        
        # Verify tag_repo.get_tags_for_item was called
        mock_tag_repo.get_tags_for_item.assert_called_once_with(1)
