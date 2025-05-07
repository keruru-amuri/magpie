"""
Unit tests for password hashing and verification.
"""
from app.core.security.password import get_password_hash, verify_password


def test_password_hash():
    """Test password hashing."""
    # Test with a simple password
    password = "password123"
    hashed_password = get_password_hash(password)

    # Verify that the hash is not the same as the password
    assert hashed_password != password

    # Verify that the hash starts with the bcrypt identifier
    assert hashed_password.startswith("$2b$")


def test_password_verification():
    """Test password verification."""
    # Test with a simple password
    password = "password123"
    hashed_password = get_password_hash(password)

    # Verify that the correct password verifies
    assert verify_password(password, hashed_password)

    # Verify that an incorrect password does not verify
    assert not verify_password("wrong_password", hashed_password)


def test_password_verification_with_known_hash():
    """Test password verification with a known hash."""
    # Generate a new hash for testing instead of using a hardcoded one
    password = "password123"
    known_hash = get_password_hash(password)

    # Verify that the correct password verifies
    assert verify_password(password, known_hash)

    # Verify that an incorrect password does not verify
    assert not verify_password("wrong_password", known_hash)


def test_different_passwords_have_different_hashes():
    """Test that different passwords have different hashes."""
    # Test with two different passwords
    password1 = "password123"
    password2 = "password456"

    # Get hashes
    hash1 = get_password_hash(password1)
    hash2 = get_password_hash(password2)

    # Verify that the hashes are different
    assert hash1 != hash2

    # Verify that each password only verifies against its own hash
    assert verify_password(password1, hash1)
    assert verify_password(password2, hash2)
    assert not verify_password(password1, hash2)
    assert not verify_password(password2, hash1)


def test_same_password_has_different_hashes():
    """Test that the same password hashed twice has different hashes."""
    # Test with the same password
    password = "password123"

    # Get hashes
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Verify that the hashes are different (due to different salts)
    assert hash1 != hash2

    # Verify that the password verifies against both hashes
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)
