"""
Cache key generation strategies for the MAGPIE platform.
"""
import hashlib
import json
from typing import Any, Dict, List, Optional, Union


class CacheKeyGenerator:
    """
    Utility class for generating cache keys.
    """
    
    @staticmethod
    def generate_key(
        prefix: str, 
        *args: Any, 
        **kwargs: Any
    ) -> str:
        """
        Generate a cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            str: Generated cache key
        """
        # Start with the prefix
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
        
        # Add keyword arguments in sorted order for consistency
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for k, v in sorted_kwargs:
                if v is not None:
                    key_parts.append(f"{k}={v}")
        
        # Join parts with colon
        return ":".join(key_parts)
    
    @staticmethod
    def generate_hash_key(
        prefix: str, 
        data: Union[Dict[str, Any], List[Any], str, bytes],
        max_length: int = 64
    ) -> str:
        """
        Generate a hashed cache key from prefix and data.
        
        Args:
            prefix: Key prefix
            data: Data to hash
            max_length: Maximum key length
            
        Returns:
            str: Generated cache key
        """
        # Convert data to string if needed
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, bytes):
            data_str = data.decode('utf-8', errors='ignore')
        else:
            data_str = str(data)
        
        # Generate hash
        hash_obj = hashlib.sha256(data_str.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        
        # Truncate hash if needed
        if max_length > 0 and len(hash_str) > max_length:
            hash_str = hash_str[:max_length]
        
        # Return prefixed key
        return f"{prefix}:{hash_str}"
    
    @staticmethod
    def user_key(user_id: int, suffix: Optional[str] = None) -> str:
        """
        Generate a cache key for user data.
        
        Args:
            user_id: User ID
            suffix: Optional key suffix
            
        Returns:
            str: Generated cache key
        """
        key = f"user:{user_id}"
        if suffix:
            key = f"{key}:{suffix}"
        return key
    
    @staticmethod
    def conversation_key(conversation_id: str, suffix: Optional[str] = None) -> str:
        """
        Generate a cache key for conversation data.
        
        Args:
            conversation_id: Conversation ID
            suffix: Optional key suffix
            
        Returns:
            str: Generated cache key
        """
        key = f"conversation:{conversation_id}"
        if suffix:
            key = f"{key}:{suffix}"
        return key
    
    @staticmethod
    def agent_key(agent_type: str, suffix: Optional[str] = None) -> str:
        """
        Generate a cache key for agent data.
        
        Args:
            agent_type: Agent type
            suffix: Optional key suffix
            
        Returns:
            str: Generated cache key
        """
        key = f"agent:{agent_type}"
        if suffix:
            key = f"{key}:{suffix}"
        return key
    
    @staticmethod
    def llm_response_key(
        prompt_hash: str, 
        model: str, 
        temperature: float
    ) -> str:
        """
        Generate a cache key for LLM responses.
        
        Args:
            prompt_hash: Hash of the prompt
            model: Model name
            temperature: Temperature setting
            
        Returns:
            str: Generated cache key
        """
        return f"llm:response:{model}:{temperature}:{prompt_hash}"
