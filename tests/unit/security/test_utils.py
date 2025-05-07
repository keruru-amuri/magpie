"""
Unit tests for security utilities.
"""
import pytest

from app.core.security.utils import (
    generate_random_string,
    generate_password_reset_token,
    generate_verification_code,
    is_valid_password,
)


def test_generate_random_string():
    """Test generating a random string."""
    # Generate a random string with default length
    random_string = generate_random_string()
    
    # Verify that the string has the correct length
    assert len(random_string) == 32
    
    # Verify that the string only contains letters and digits
    assert all(c.isalnum() for c in random_string)
    
    # Generate a random string with custom length
    custom_length = 16
    random_string = generate_random_string(length=custom_length)
    
    # Verify that the string has the correct length
    assert len(random_string) == custom_length
    
    # Verify that the string only contains letters and digits
    assert all(c.isalnum() for c in random_string)
    
    # Generate two random strings and verify that they are different
    random_string1 = generate_random_string()
    random_string2 = generate_random_string()
    assert random_string1 != random_string2


def test_generate_password_reset_token():
    """Test generating a password reset token."""
    # Generate a password reset token
    token = generate_password_reset_token()
    
    # Verify that the token has the correct length
    assert len(token) == 64
    
    # Verify that the token only contains letters and digits
    assert all(c.isalnum() for c in token)
    
    # Generate two tokens and verify that they are different
    token1 = generate_password_reset_token()
    token2 = generate_password_reset_token()
    assert token1 != token2


def test_generate_verification_code():
    """Test generating a verification code."""
    # Generate a verification code with default length
    code = generate_verification_code()
    
    # Verify that the code has the correct length
    assert len(code) == 6
    
    # Verify that the code only contains digits
    assert all(c.isdigit() for c in code)
    
    # Generate a verification code with custom length
    custom_length = 4
    code = generate_verification_code(length=custom_length)
    
    # Verify that the code has the correct length
    assert len(code) == custom_length
    
    # Verify that the code only contains digits
    assert all(c.isdigit() for c in code)
    
    # Generate two codes and verify that they are different
    code1 = generate_verification_code()
    code2 = generate_verification_code()
    assert code1 != code2


def test_is_valid_password():
    """Test password validation."""
    # Test valid passwords
    assert is_valid_password("Password123!")
    assert is_valid_password("Abcdef1!")
    assert is_valid_password("P@ssw0rd")
    assert is_valid_password("Complex_Password123")
    
    # Test passwords that are too short
    assert not is_valid_password("Pass1!")
    assert not is_valid_password("Abc1!")
    
    # Test passwords without uppercase letters
    assert not is_valid_password("password123!")
    assert not is_valid_password("abcdef1!")
    
    # Test passwords without lowercase letters
    assert not is_valid_password("PASSWORD123!")
    assert not is_valid_password("ABCDEF1!")
    
    # Test passwords without digits
    assert not is_valid_password("Password!")
    assert not is_valid_password("Abcdefg!")
    
    # Test passwords without special characters
    assert not is_valid_password("Password123")
    assert not is_valid_password("Abcdefg123")
    
    # Test with custom minimum length
    assert is_valid_password("Pass1!", min_length=6)
    assert not is_valid_password("Pas1!", min_length=6)
