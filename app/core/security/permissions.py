"""
Permission checking utilities for role-based access control.
"""
import logging
from enum import Enum
from typing import List, Set, Union

from fastapi import Depends, HTTPException, status

# Import User model directly to avoid circular imports
from app.models.user import User, UserRole

# Forward reference for get_current_active_user to avoid circular imports
get_current_active_user = None

# Configure logging
logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Permission enum for role-based access control."""

    # User management permissions
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"

    # Documentation permissions
    MANAGE_DOCUMENTATION = "manage_documentation"
    VIEW_DOCUMENTATION = "view_documentation"

    # Troubleshooting permissions
    MANAGE_TROUBLESHOOTING = "manage_troubleshooting"
    VIEW_TROUBLESHOOTING = "view_troubleshooting"

    # Maintenance permissions
    MANAGE_MAINTENANCE = "manage_maintenance"
    VIEW_MAINTENANCE = "view_maintenance"

    # System permissions
    MANAGE_SYSTEM = "manage_system"
    VIEW_SYSTEM = "view_system"


# Role-based permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.MANAGE_DOCUMENTATION,
        Permission.VIEW_DOCUMENTATION,
        Permission.MANAGE_TROUBLESHOOTING,
        Permission.VIEW_TROUBLESHOOTING,
        Permission.MANAGE_MAINTENANCE,
        Permission.VIEW_MAINTENANCE,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_SYSTEM,
    },
    UserRole.MANAGER: {
        Permission.VIEW_USERS,
        Permission.MANAGE_DOCUMENTATION,
        Permission.VIEW_DOCUMENTATION,
        Permission.MANAGE_TROUBLESHOOTING,
        Permission.VIEW_TROUBLESHOOTING,
        Permission.MANAGE_MAINTENANCE,
        Permission.VIEW_MAINTENANCE,
        Permission.VIEW_SYSTEM,
    },
    UserRole.ENGINEER: {
        Permission.VIEW_DOCUMENTATION,
        Permission.MANAGE_TROUBLESHOOTING,
        Permission.VIEW_TROUBLESHOOTING,
        Permission.MANAGE_MAINTENANCE,
        Permission.VIEW_MAINTENANCE,
    },
    UserRole.TECHNICIAN: {
        Permission.VIEW_DOCUMENTATION,
        Permission.VIEW_TROUBLESHOOTING,
        Permission.VIEW_MAINTENANCE,
    },
    UserRole.GUEST: {
        Permission.VIEW_DOCUMENTATION,
    },
}


def get_permissions_for_role(role: UserRole) -> Set[Permission]:
    """
    Get permissions for a role.

    Args:
        role: User role

    Returns:
        Set[Permission]: Set of permissions
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(user: User, permission: Permission) -> bool:
    """
    Check if a user has a permission.

    Args:
        user: User to check
        permission: Permission to check

    Returns:
        bool: True if the user has the permission, False otherwise
    """
    # Superusers have all permissions
    if user.is_superuser:
        return True

    # Get permissions for the user's role
    user_permissions = get_permissions_for_role(user.role)

    # Check if the permission is in the user's permissions
    return permission in user_permissions


def require_permissions(
    required_permissions: Union[Permission, List[Permission]],
    require_all: bool = True,
):
    """
    Dependency for requiring permissions.

    Args:
        required_permissions: Required permissions
        require_all: Whether to require all permissions or just one

    Returns:
        Callable: Dependency function
    """
    if isinstance(required_permissions, Permission):
        required_permissions = [required_permissions]

    async def _require_permissions(
        current_user: User = Depends(get_current_active_user) if get_current_active_user else Depends(),
    ):
        """
        Check if the current user has the required permissions.

        Args:
            current_user: Current user

        Raises:
            HTTPException: If the user doesn't have the required permissions
        """
        if current_user.is_superuser:
            return current_user

        user_permissions = get_permissions_for_role(current_user.role)

        if require_all:
            # Check if the user has all required permissions
            has_all_permissions = all(
                permission in user_permissions for permission in required_permissions
            )
            if not has_all_permissions:
                logger.warning(
                    f"User {current_user.id} ({current_user.username}) "
                    f"doesn't have all required permissions: {required_permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )
        else:
            # Check if the user has at least one of the required permissions
            has_any_permission = any(
                permission in user_permissions for permission in required_permissions
            )
            if not has_any_permission:
                logger.warning(
                    f"User {current_user.id} ({current_user.username}) "
                    f"doesn't have any of the required permissions: {required_permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )

        return current_user

    return _require_permissions
