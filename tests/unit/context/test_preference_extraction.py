"""
Unit tests for user preference extraction.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock

from app.core.context.preference_extraction import PreferenceExtractor, PreferenceManager
from app.models.conversation import Message, MessageRole
from app.models.context import UserPreference, ContextPriority
from app.services.llm_service import LLMService
from app.services.context_service import ContextService


class TestPreferenceExtractor:
    """
    Test preference extractor.
    """
    
    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        service = MagicMock(spec=LLMService)
        service.generate_completion_raw = AsyncMock(return_value={
            "content": json.dumps({
                "preferred_format": {"value": "detailed", "confidence": 0.9},
                "aircraft_type": {"value": "boeing 737", "confidence": 0.8},
                "system_focus": {"value": "hydraulic", "confidence": 0.7}
            })
        })
        return service
    
    @pytest.fixture
    def extractor(self, mock_llm_service):
        """
        Create a preference extractor.
        """
        return PreferenceExtractor(mock_llm_service)
    
    @pytest.fixture
    def mock_user_message(self):
        """
        Create a mock user message.
        """
        return MagicMock(
            spec=Message,
            id=1,
            conversation_id=1,
            role=MessageRole.USER,
            content="I prefer detailed information when working on a Boeing 737 hydraulic system."
        )
    
    @pytest.fixture
    def mock_assistant_message(self):
        """
        Create a mock assistant message.
        """
        return MagicMock(
            spec=Message,
            id=2,
            conversation_id=1,
            role=MessageRole.ASSISTANT,
            content="I'll provide detailed information about the Boeing 737 hydraulic system."
        )
    
    def test_extract_preferences_rule_based(self, extractor, mock_user_message, mock_assistant_message):
        """
        Test extracting preferences using rule-based patterns.
        """
        # Test with user message
        preferences = extractor.extract_preferences_rule_based(mock_user_message)
        assert len(preferences) > 0
        assert "preferred_format" in preferences
        assert preferences["preferred_format"][0] == "detailed"
        assert "aircraft_type" in preferences
        assert "system_focus" in preferences
        
        # Test with assistant message (should return empty dict)
        preferences = extractor.extract_preferences_rule_based(mock_assistant_message)
        assert preferences == {}
        
        # Test with empty message
        empty_message = MagicMock(spec=Message, content=None, role=MessageRole.USER)
        preferences = extractor.extract_preferences_rule_based(empty_message)
        assert preferences == {}
    
    @pytest.mark.asyncio
    async def test_extract_preferences_llm(self, extractor, mock_user_message, mock_llm_service):
        """
        Test extracting preferences using LLM.
        """
        # Test with user message
        preferences = await extractor.extract_preferences_llm(mock_user_message)
        assert len(preferences) == 3
        assert "preferred_format" in preferences
        assert preferences["preferred_format"][0] == "detailed"
        assert preferences["preferred_format"][1] == 0.9
        assert "aircraft_type" in preferences
        assert "system_focus" in preferences
        
        # Verify LLM service was called
        mock_llm_service.generate_completion_raw.assert_called_once()
        
        # Test with empty message
        empty_message = MagicMock(spec=Message, content=None, role=MessageRole.USER)
        preferences = await extractor.extract_preferences_llm(empty_message)
        assert preferences == {}
    
    @pytest.mark.asyncio
    async def test_extract_preferences(self, extractor, mock_user_message):
        """
        Test extracting preferences using both rule-based and LLM approaches.
        """
        # Mock extract_preferences_rule_based
        with patch.object(PreferenceExtractor, 'extract_preferences_rule_based') as mock_rule_based:
            mock_rule_based.return_value = {
                "preferred_format": ("detailed", 0.6),
                "aircraft_type": ("boeing 737", 0.7)
            }
            
            # Mock extract_preferences_llm
            with patch.object(PreferenceExtractor, 'extract_preferences_llm') as mock_llm:
                mock_llm.return_value = {
                    "preferred_format": ("detailed", 0.9),
                    "system_focus": ("hydraulic", 0.8)
                }
                
                # Test with both methods
                preferences = await extractor.extract_preferences(mock_user_message, use_llm=True)
                assert len(preferences) == 3
                assert preferences["preferred_format"][0] == "detailed"
                assert preferences["preferred_format"][1] == 0.9  # Higher confidence from LLM
                assert "aircraft_type" in preferences
                assert "system_focus" in preferences
                
                # Test with rule-based only
                preferences = await extractor.extract_preferences(mock_user_message, use_llm=False)
                assert len(preferences) == 2
                assert "preferred_format" in preferences
                assert "aircraft_type" in preferences
                assert "system_focus" not in preferences


class TestPreferenceManager:
    """
    Test preference manager.
    """
    
    @pytest.fixture
    def mock_context_service(self):
        """
        Create a mock context service.
        """
        service = MagicMock(spec=ContextService)
        service.extract_user_preference = MagicMock(return_value=MagicMock(spec=UserPreference))
        service.add_user_preferences_to_context = MagicMock(return_value=[MagicMock()])
        service.preference_repo = MagicMock()
        service.preference_repo.get_preferences_for_user = MagicMock(return_value=[
            MagicMock(spec=UserPreference, preference_key="preferred_format", preference_value="detailed"),
            MagicMock(spec=UserPreference, preference_key="aircraft_type", preference_value="boeing 737")
        ])
        service.preference_repo.get_preference = MagicMock(return_value=MagicMock(
            spec=UserPreference, preference_key="preferred_format", preference_value="detailed"
        ))
        service.preference_repo.set_preference = MagicMock(return_value=MagicMock(spec=UserPreference))
        return service
    
    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        service = MagicMock(spec=LLMService)
        return service
    
    @pytest.fixture
    def preference_manager(self, mock_context_service, mock_llm_service):
        """
        Create a preference manager.
        """
        return PreferenceManager(mock_context_service, mock_llm_service)
    
    @pytest.fixture
    def mock_message(self):
        """
        Create a mock message.
        """
        return MagicMock(
            spec=Message,
            id=1,
            conversation_id=1,
            role=MessageRole.USER,
            content="I prefer detailed information when working on a Boeing 737 hydraulic system."
        )
    
    @pytest.mark.asyncio
    async def test_process_message(self, preference_manager, mock_message, mock_context_service):
        """
        Test processing a message to extract and store preferences.
        """
        # Mock extract_preferences
        with patch.object(PreferenceExtractor, 'extract_preferences') as mock_extract:
            mock_extract.return_value = {
                "preferred_format": ("detailed", 0.9),
                "aircraft_type": ("boeing 737", 0.8)
            }
            
            # Test processing message
            preferences = await preference_manager.process_message(mock_message)
            assert len(preferences) == 2
            
            # Verify context_service methods were called
            assert mock_context_service.extract_user_preference.call_count == 2
            mock_context_service.add_user_preferences_to_context.assert_called_once_with(
                conversation_id=mock_message.conversation_id,
                priority=ContextPriority.HIGH
            )
            
            # Test without adding to context
            mock_context_service.reset_mock()
            preferences = await preference_manager.process_message(mock_message, add_to_context=False)
            assert len(preferences) == 2
            assert mock_context_service.extract_user_preference.call_count == 2
            mock_context_service.add_user_preferences_to_context.assert_not_called()
    
    def test_get_user_preferences(self, preference_manager, mock_context_service):
        """
        Test getting all preferences for a user.
        """
        # Test getting preferences
        preferences = preference_manager.get_user_preferences(user_id=1)
        assert len(preferences) == 2
        assert preferences["preferred_format"] == "detailed"
        assert preferences["aircraft_type"] == "boeing 737"
        
        # Verify preference_repo.get_preferences_for_user was called
        mock_context_service.preference_repo.get_preferences_for_user.assert_called_once_with(1)
    
    def test_get_preference(self, preference_manager, mock_context_service):
        """
        Test getting a specific preference for a user.
        """
        # Test getting preference
        preference = preference_manager.get_preference(user_id=1, key="preferred_format")
        assert preference == "detailed"
        
        # Verify preference_repo.get_preference was called
        mock_context_service.preference_repo.get_preference.assert_called_once_with(1, "preferred_format")
    
    def test_set_preference(self, preference_manager, mock_context_service):
        """
        Test setting a preference for a user.
        """
        # Test setting preference
        preference = preference_manager.set_preference(
            user_id=1,
            key="preferred_format",
            value="detailed",
            confidence=0.9,
            source_message_id=1
        )
        assert preference is not None
        
        # Verify preference_repo.set_preference was called
        mock_context_service.preference_repo.set_preference.assert_called_once_with(
            user_id=1,
            key="preferred_format",
            value="detailed",
            confidence=0.9,
            source_message_id=1
        )
