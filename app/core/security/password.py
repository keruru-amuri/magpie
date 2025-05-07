"""
Password hashing and verification utilities for the MAGPIE platform.
"""
import logging
from typing import Optional

import bcrypt

# Configure logging
logger = logging.getLogger(__name__)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    # Generate a salt and hash the password
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)  # 12 is a good default for security/performance
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    
    # Return the hashed password as a string
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if the password matches the hash, False otherwise
    """
    try:
        # Convert strings to bytes for bcrypt
        plain_password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        
        # Check if the password matches the hash
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False
