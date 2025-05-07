"""
Unit tests for cache key generation.
"""
import pytest
import json
import hashlib

from app.core.cache.keys import CacheKeyGenerator


class TestCacheKeyGenerator:
    """
    Test cache key generation functionality.
    """
    
    def test_generate_key_simple(self):
        """
        Test generate_key method with simple arguments.
        """
        # Generate key
        key = CacheKeyGenerator.generate_key("test", "arg1", "arg2")
        
        # Verify key
        assert key == "test:arg1:arg2"
    
    def test_generate_key_with_kwargs(self):
        """
        Test generate_key method with keyword arguments.
        """
        # Generate key
        key = CacheKeyGenerator.generate_key("test", "arg1", param1="value1", param2="value2")
        
        # Verify key
        assert key == "test:arg1:param1=value1:param2=value2"
    
    def test_generate_key_with_none(self):
        """
        Test generate_key method with None values.
        """
        # Generate key
        key = CacheKeyGenerator.generate_key("test", "arg1", None, param1="value1", param2=None)
        
        # Verify key
        assert key == "test:arg1:param1=value1"
    
    def test_generate_key_sorted_kwargs(self):
        """
        Test generate_key method with unsorted keyword arguments.
        """
        # Generate key with unsorted kwargs
        key1 = CacheKeyGenerator.generate_key("test", param2="value2", param1="value1")
        
        # Generate key with sorted kwargs
        key2 = CacheKeyGenerator.generate_key("test", param1="value1", param2="value2")
        
        # Verify keys are the same
        assert key1 == key2
    
    def test_generate_hash_key_dict(self):
        """
        Test generate_hash_key method with dictionary.
        """
        # Generate hash key
        data = {"name": "Test", "value": 42}
        key = CacheKeyGenerator.generate_hash_key("test", data)
        
        # Verify key
        assert key.startswith("test:")
        assert len(key) <= 64 + 5  # prefix + colon + hash
        
        # Verify hash is correct
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.sha256(data_str.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        assert key == f"test:{hash_str}"
    
    def test_generate_hash_key_list(self):
        """
        Test generate_hash_key method with list.
        """
        # Generate hash key
        data = ["Test", 42, True]
        key = CacheKeyGenerator.generate_hash_key("test", data)
        
        # Verify key
        assert key.startswith("test:")
        assert len(key) <= 64 + 5  # prefix + colon + hash
        
        # Verify hash is correct
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.sha256(data_str.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        assert key == f"test:{hash_str}"
    
    def test_generate_hash_key_string(self):
        """
        Test generate_hash_key method with string.
        """
        # Generate hash key
        data = "Test string"
        key = CacheKeyGenerator.generate_hash_key("test", data)
        
        # Verify key
        assert key.startswith("test:")
        assert len(key) <= 64 + 5  # prefix + colon + hash
        
        # Verify hash is correct
        hash_obj = hashlib.sha256(data.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        assert key == f"test:{hash_str}"
    
    def test_generate_hash_key_bytes(self):
        """
        Test generate_hash_key method with bytes.
        """
        # Generate hash key
        data = b"Test bytes"
        key = CacheKeyGenerator.generate_hash_key("test", data)
        
        # Verify key
        assert key.startswith("test:")
        assert len(key) <= 64 + 5  # prefix + colon + hash
        
        # Verify hash is correct
        hash_obj = hashlib.sha256(data)
        hash_str = hash_obj.hexdigest()
        assert key == f"test:{hash_str}"
    
    def test_generate_hash_key_max_length(self):
        """
        Test generate_hash_key method with max_length.
        """
        # Generate hash key with max_length
        data = "Test string"
        key = CacheKeyGenerator.generate_hash_key("test", data, max_length=16)
        
        # Verify key
        assert key.startswith("test:")
        assert len(key) == 16 + 5  # prefix + colon + hash
        
        # Verify hash is truncated
        hash_obj = hashlib.sha256(data.encode('utf-8'))
        hash_str = hash_obj.hexdigest()[:16]
        assert key == f"test:{hash_str}"
    
    def test_generate_hash_key_no_max_length(self):
        """
        Test generate_hash_key method with no max_length.
        """
        # Generate hash key with no max_length
        data = "Test string"
        key = CacheKeyGenerator.generate_hash_key("test", data, max_length=0)
        
        # Verify key
        assert key.startswith("test:")
        
        # Verify hash is not truncated
        hash_obj = hashlib.sha256(data.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        assert key == f"test:{hash_str}"
    
    def test_user_key(self):
        """
        Test user_key method.
        """
        # Generate user key
        key = CacheKeyGenerator.user_key(123)
        
        # Verify key
        assert key == "user:123"
    
    def test_user_key_with_suffix(self):
        """
        Test user_key method with suffix.
        """
        # Generate user key with suffix
        key = CacheKeyGenerator.user_key(123, "profile")
        
        # Verify key
        assert key == "user:123:profile"
    
    def test_conversation_key(self):
        """
        Test conversation_key method.
        """
        # Generate conversation key
        key = CacheKeyGenerator.conversation_key("abc123")
        
        # Verify key
        assert key == "conversation:abc123"
    
    def test_conversation_key_with_suffix(self):
        """
        Test conversation_key method with suffix.
        """
        # Generate conversation key with suffix
        key = CacheKeyGenerator.conversation_key("abc123", "messages")
        
        # Verify key
        assert key == "conversation:abc123:messages"
    
    def test_agent_key(self):
        """
        Test agent_key method.
        """
        # Generate agent key
        key = CacheKeyGenerator.agent_key("documentation")
        
        # Verify key
        assert key == "agent:documentation"
    
    def test_agent_key_with_suffix(self):
        """
        Test agent_key method with suffix.
        """
        # Generate agent key with suffix
        key = CacheKeyGenerator.agent_key("documentation", "config")
        
        # Verify key
        assert key == "agent:documentation:config"
    
    def test_llm_response_key(self):
        """
        Test llm_response_key method.
        """
        # Generate LLM response key
        key = CacheKeyGenerator.llm_response_key("abc123", "gpt-4.1", 0.7)
        
        # Verify key
        assert key == "llm:response:gpt-4.1:0.7:abc123"
