"""
Unit tests for cache TTL policies.
"""
import pytest
from unittest.mock import patch

from app.core.cache.ttl import CacheTTLPolicy, CacheTTLManager
from app.core.config import settings


class TestCacheTTLManager:
    """
    Test cache TTL manager functionality.
    """
    
    def test_ttl_values(self):
        """
        Test TTL values.
        """
        # Verify TTL values
        assert CacheTTLManager.TTL_VALUES[CacheTTLPolicy.DEFAULT] == settings.CACHE_TTL_DEFAULT
        assert CacheTTLManager.TTL_VALUES[CacheTTLPolicy.SHORT] == settings.CACHE_TTL_SHORT
        assert CacheTTLManager.TTL_VALUES[CacheTTLPolicy.MEDIUM] == settings.CACHE_TTL_MEDIUM
        assert CacheTTLManager.TTL_VALUES[CacheTTLPolicy.LONG] == settings.CACHE_TTL_LONG
        assert CacheTTLManager.TTL_VALUES[CacheTTLPolicy.PERMANENT] == -1
    
    def test_default_policies(self):
        """
        Test default policies.
        """
        # Verify default policies
        assert CacheTTLManager.DEFAULT_POLICIES["user"] == CacheTTLPolicy.MEDIUM
        assert CacheTTLManager.DEFAULT_POLICIES["conversation"] == CacheTTLPolicy.MEDIUM
        assert CacheTTLManager.DEFAULT_POLICIES["message"] == CacheTTLPolicy.MEDIUM
        assert CacheTTLManager.DEFAULT_POLICIES["agent"] == CacheTTLPolicy.LONG
        assert CacheTTLManager.DEFAULT_POLICIES["llm_response"] == CacheTTLPolicy.LONG
        assert CacheTTLManager.DEFAULT_POLICIES["token_count"] == CacheTTLPolicy.LONG
        assert CacheTTLManager.DEFAULT_POLICIES["embedding"] == CacheTTLPolicy.LONG
        assert CacheTTLManager.DEFAULT_POLICIES["health_check"] == CacheTTLPolicy.SHORT
        assert CacheTTLManager.DEFAULT_POLICIES["rate_limit"] == CacheTTLPolicy.SHORT
    
    def test_get_ttl_with_policy(self):
        """
        Test get_ttl method with policy.
        """
        # Get TTL with policy
        ttl = CacheTTLManager.get_ttl("user", CacheTTLPolicy.SHORT)
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_SHORT
    
    def test_get_ttl_with_default_policy(self):
        """
        Test get_ttl method with default policy.
        """
        # Get TTL with default policy
        ttl = CacheTTLManager.get_ttl("user")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_MEDIUM
    
    def test_get_ttl_with_unknown_data_type(self):
        """
        Test get_ttl method with unknown data type.
        """
        # Get TTL with unknown data type
        ttl = CacheTTLManager.get_ttl("unknown")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_DEFAULT
    
    def test_get_ttl_with_unknown_policy(self):
        """
        Test get_ttl method with unknown policy.
        """
        # Get TTL with unknown policy
        ttl = CacheTTLManager.get_ttl("user", "unknown")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_DEFAULT
    
    def test_get_ttl_for_key_user(self):
        """
        Test get_ttl_for_key method with user key.
        """
        # Get TTL for user key
        ttl = CacheTTLManager.get_ttl_for_key("user:123")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_MEDIUM
    
    def test_get_ttl_for_key_conversation(self):
        """
        Test get_ttl_for_key method with conversation key.
        """
        # Get TTL for conversation key
        ttl = CacheTTLManager.get_ttl_for_key("conversation:abc123")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_MEDIUM
    
    def test_get_ttl_for_key_agent(self):
        """
        Test get_ttl_for_key method with agent key.
        """
        # Get TTL for agent key
        ttl = CacheTTLManager.get_ttl_for_key("agent:documentation")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_LONG
    
    def test_get_ttl_for_key_llm_response(self):
        """
        Test get_ttl_for_key method with LLM response key.
        """
        # Get TTL for LLM response key
        ttl = CacheTTLManager.get_ttl_for_key("llm_response:abc123")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_LONG
    
    def test_get_ttl_for_key_unknown(self):
        """
        Test get_ttl_for_key method with unknown key.
        """
        # Get TTL for unknown key
        ttl = CacheTTLManager.get_ttl_for_key("unknown:123")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_DEFAULT
    
    def test_get_ttl_for_key_empty(self):
        """
        Test get_ttl_for_key method with empty key.
        """
        # Get TTL for empty key
        ttl = CacheTTLManager.get_ttl_for_key("")
        
        # Verify TTL
        assert ttl == settings.CACHE_TTL_DEFAULT
