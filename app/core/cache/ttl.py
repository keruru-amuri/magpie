"""
TTL (Time-To-Live) policies for different data types in Redis cache.
"""
from enum import Enum
from typing import Dict, Optional

from app.core.config import settings


class CacheTTLPolicy(str, Enum):
    """
    Enum for cache TTL policies.
    """
    
    DEFAULT = "default"  # Default TTL (1 hour)
    SHORT = "short"      # Short TTL (5 minutes)
    MEDIUM = "medium"    # Medium TTL (30 minutes)
    LONG = "long"        # Long TTL (24 hours)
    PERMANENT = "permanent"  # No expiration


class CacheTTLManager:
    """
    Manager for cache TTL policies.
    """
    
    # TTL values in seconds
    TTL_VALUES: Dict[CacheTTLPolicy, int] = {
        CacheTTLPolicy.DEFAULT: settings.CACHE_TTL_DEFAULT,
        CacheTTLPolicy.SHORT: settings.CACHE_TTL_SHORT,
        CacheTTLPolicy.MEDIUM: settings.CACHE_TTL_MEDIUM,
        CacheTTLPolicy.LONG: settings.CACHE_TTL_LONG,
        CacheTTLPolicy.PERMANENT: -1,  # No expiration
    }
    
    # Default TTL policies for different data types
    DEFAULT_POLICIES: Dict[str, CacheTTLPolicy] = {
        "user": CacheTTLPolicy.MEDIUM,
        "conversation": CacheTTLPolicy.MEDIUM,
        "message": CacheTTLPolicy.MEDIUM,
        "agent": CacheTTLPolicy.LONG,
        "llm_response": CacheTTLPolicy.LONG,
        "token_count": CacheTTLPolicy.LONG,
        "embedding": CacheTTLPolicy.LONG,
        "health_check": CacheTTLPolicy.SHORT,
        "rate_limit": CacheTTLPolicy.SHORT,
    }
    
    @classmethod
    def get_ttl(cls, data_type: str, policy: Optional[CacheTTLPolicy] = None) -> int:
        """
        Get TTL value for data type.
        
        Args:
            data_type: Type of data
            policy: TTL policy (overrides default policy for data type)
            
        Returns:
            int: TTL value in seconds
        """
        # Use provided policy or get default policy for data type
        if policy is None:
            policy = cls.DEFAULT_POLICIES.get(
                data_type, 
                CacheTTLPolicy.DEFAULT
            )
        
        # Get TTL value for policy
        return cls.TTL_VALUES.get(policy, settings.CACHE_TTL_DEFAULT)
    
    @classmethod
    def get_ttl_for_key(cls, key: str) -> int:
        """
        Get TTL value based on key prefix.
        
        Args:
            key: Cache key
            
        Returns:
            int: TTL value in seconds
        """
        # Extract data type from key prefix
        parts = key.split(":", 1)
        data_type = parts[0] if parts else ""
        
        return cls.get_ttl(data_type)
