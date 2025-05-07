"""
General security utilities for the MAGPIE platform.
"""
import logging
import secrets
import string
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


def generate_random_string(length: int = 32) -> str:
    """
    Generate a random string of specified length.
    
    Args:
        length: Length of the string
        
    Returns:
        str: Random string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_password_reset_token() -> str:
    """
    Generate a token for password reset.
    
    Returns:
        str: Password reset token
    """
    return generate_random_string(64)


def generate_verification_code(length: int = 6) -> str:
    """
    Generate a numeric verification code.
    
    Args:
        length: Length of the code
        
    Returns:
        str: Verification code
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def is_valid_password(password: str, min_length: int = 8) -> bool:
    """
    Check if a password meets the minimum requirements.
    
    Args:
        password: Password to check
        min_length: Minimum password length
        
    Returns:
        bool: True if the password is valid, False otherwise
    """
    if len(password) < min_length:
        return False
    
    # Check for at least one uppercase letter
    if not any(c.isupper() for c in password):
        return False
    
    # Check for at least one lowercase letter
    if not any(c.islower() for c in password):
        return False
    
    # Check for at least one digit
    if not any(c.isdigit() for c in password):
        return False
    
    # Check for at least one special character
    special_chars = set(string.punctuation)
    if not any(c in special_chars for c in password):
        return False
    
    return True
