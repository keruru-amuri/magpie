"""
Security module for the MAGPIE platform.
"""

from app.core.security.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security.password import get_password_hash, verify_password
from app.core.security.permissions import (
    Permission,
    get_permissions_for_role,
    has_permission,
    require_permissions,
)
from app.core.security.utils import (
    generate_random_string,
    generate_password_reset_token,
    generate_verification_code,
    is_valid_password,
)

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_password_hash",
    "verify_password",
    "generate_random_string",
    "generate_password_reset_token",
    "generate_verification_code",
    "is_valid_password",
    "Permission",
    "get_permissions_for_role",
    "has_permission",
    "require_permissions",
]
