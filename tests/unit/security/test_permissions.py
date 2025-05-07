"""
Unit tests for permission checking utilities.
"""
import pytest
from unittest.mock import MagicMock

from app.core.security.permissions import (
    Permission,
    get_permissions_for_role,
    has_permission,
)
from app.models.user import User, UserRole


def test_get_permissions_for_role():
    """Test getting permissions for a role."""
    # Test admin role
    admin_permissions = get_permissions_for_role(UserRole.ADMIN)
    assert Permission.MANAGE_USERS in admin_permissions
    assert Permission.VIEW_USERS in admin_permissions
    assert Permission.MANAGE_DOCUMENTATION in admin_permissions
    assert Permission.VIEW_DOCUMENTATION in admin_permissions
    assert Permission.MANAGE_TROUBLESHOOTING in admin_permissions
    assert Permission.VIEW_TROUBLESHOOTING in admin_permissions
    assert Permission.MANAGE_MAINTENANCE in admin_permissions
    assert Permission.VIEW_MAINTENANCE in admin_permissions
    assert Permission.MANAGE_SYSTEM in admin_permissions
    assert Permission.VIEW_SYSTEM in admin_permissions
    
    # Test manager role
    manager_permissions = get_permissions_for_role(UserRole.MANAGER)
    assert Permission.MANAGE_USERS not in manager_permissions
    assert Permission.VIEW_USERS in manager_permissions
    assert Permission.MANAGE_DOCUMENTATION in manager_permissions
    assert Permission.VIEW_DOCUMENTATION in manager_permissions
    assert Permission.MANAGE_TROUBLESHOOTING in manager_permissions
    assert Permission.VIEW_TROUBLESHOOTING in manager_permissions
    assert Permission.MANAGE_MAINTENANCE in manager_permissions
    assert Permission.VIEW_MAINTENANCE in manager_permissions
    assert Permission.MANAGE_SYSTEM not in manager_permissions
    assert Permission.VIEW_SYSTEM in manager_permissions
    
    # Test engineer role
    engineer_permissions = get_permissions_for_role(UserRole.ENGINEER)
    assert Permission.MANAGE_USERS not in engineer_permissions
    assert Permission.VIEW_USERS not in engineer_permissions
    assert Permission.MANAGE_DOCUMENTATION not in engineer_permissions
    assert Permission.VIEW_DOCUMENTATION in engineer_permissions
    assert Permission.MANAGE_TROUBLESHOOTING in engineer_permissions
    assert Permission.VIEW_TROUBLESHOOTING in engineer_permissions
    assert Permission.MANAGE_MAINTENANCE in engineer_permissions
    assert Permission.VIEW_MAINTENANCE in engineer_permissions
    assert Permission.MANAGE_SYSTEM not in engineer_permissions
    assert Permission.VIEW_SYSTEM not in engineer_permissions
    
    # Test technician role
    technician_permissions = get_permissions_for_role(UserRole.TECHNICIAN)
    assert Permission.MANAGE_USERS not in technician_permissions
    assert Permission.VIEW_USERS not in technician_permissions
    assert Permission.MANAGE_DOCUMENTATION not in technician_permissions
    assert Permission.VIEW_DOCUMENTATION in technician_permissions
    assert Permission.MANAGE_TROUBLESHOOTING not in technician_permissions
    assert Permission.VIEW_TROUBLESHOOTING in technician_permissions
    assert Permission.MANAGE_MAINTENANCE not in technician_permissions
    assert Permission.VIEW_MAINTENANCE in technician_permissions
    assert Permission.MANAGE_SYSTEM not in technician_permissions
    assert Permission.VIEW_SYSTEM not in technician_permissions
    
    # Test guest role
    guest_permissions = get_permissions_for_role(UserRole.GUEST)
    assert Permission.MANAGE_USERS not in guest_permissions
    assert Permission.VIEW_USERS not in guest_permissions
    assert Permission.MANAGE_DOCUMENTATION not in guest_permissions
    assert Permission.VIEW_DOCUMENTATION in guest_permissions
    assert Permission.MANAGE_TROUBLESHOOTING not in guest_permissions
    assert Permission.VIEW_TROUBLESHOOTING not in guest_permissions
    assert Permission.MANAGE_MAINTENANCE not in guest_permissions
    assert Permission.VIEW_MAINTENANCE not in guest_permissions
    assert Permission.MANAGE_SYSTEM not in guest_permissions
    assert Permission.VIEW_SYSTEM not in guest_permissions


def test_has_permission():
    """Test checking if a user has a permission."""
    # Create a mock user with admin role
    admin_user = MagicMock(spec=User)
    admin_user.role = UserRole.ADMIN
    admin_user.is_superuser = False
    
    # Test admin permissions
    assert has_permission(admin_user, Permission.MANAGE_USERS)
    assert has_permission(admin_user, Permission.VIEW_USERS)
    assert has_permission(admin_user, Permission.MANAGE_DOCUMENTATION)
    assert has_permission(admin_user, Permission.VIEW_DOCUMENTATION)
    assert has_permission(admin_user, Permission.MANAGE_TROUBLESHOOTING)
    assert has_permission(admin_user, Permission.VIEW_TROUBLESHOOTING)
    assert has_permission(admin_user, Permission.MANAGE_MAINTENANCE)
    assert has_permission(admin_user, Permission.VIEW_MAINTENANCE)
    assert has_permission(admin_user, Permission.MANAGE_SYSTEM)
    assert has_permission(admin_user, Permission.VIEW_SYSTEM)
    
    # Create a mock user with manager role
    manager_user = MagicMock(spec=User)
    manager_user.role = UserRole.MANAGER
    manager_user.is_superuser = False
    
    # Test manager permissions
    assert not has_permission(manager_user, Permission.MANAGE_USERS)
    assert has_permission(manager_user, Permission.VIEW_USERS)
    assert has_permission(manager_user, Permission.MANAGE_DOCUMENTATION)
    assert has_permission(manager_user, Permission.VIEW_DOCUMENTATION)
    assert has_permission(manager_user, Permission.MANAGE_TROUBLESHOOTING)
    assert has_permission(manager_user, Permission.VIEW_TROUBLESHOOTING)
    assert has_permission(manager_user, Permission.MANAGE_MAINTENANCE)
    assert has_permission(manager_user, Permission.VIEW_MAINTENANCE)
    assert not has_permission(manager_user, Permission.MANAGE_SYSTEM)
    assert has_permission(manager_user, Permission.VIEW_SYSTEM)
    
    # Create a mock user with engineer role
    engineer_user = MagicMock(spec=User)
    engineer_user.role = UserRole.ENGINEER
    engineer_user.is_superuser = False
    
    # Test engineer permissions
    assert not has_permission(engineer_user, Permission.MANAGE_USERS)
    assert not has_permission(engineer_user, Permission.VIEW_USERS)
    assert not has_permission(engineer_user, Permission.MANAGE_DOCUMENTATION)
    assert has_permission(engineer_user, Permission.VIEW_DOCUMENTATION)
    assert has_permission(engineer_user, Permission.MANAGE_TROUBLESHOOTING)
    assert has_permission(engineer_user, Permission.VIEW_TROUBLESHOOTING)
    assert has_permission(engineer_user, Permission.MANAGE_MAINTENANCE)
    assert has_permission(engineer_user, Permission.VIEW_MAINTENANCE)
    assert not has_permission(engineer_user, Permission.MANAGE_SYSTEM)
    assert not has_permission(engineer_user, Permission.VIEW_SYSTEM)
    
    # Create a mock user with technician role
    technician_user = MagicMock(spec=User)
    technician_user.role = UserRole.TECHNICIAN
    technician_user.is_superuser = False
    
    # Test technician permissions
    assert not has_permission(technician_user, Permission.MANAGE_USERS)
    assert not has_permission(technician_user, Permission.VIEW_USERS)
    assert not has_permission(technician_user, Permission.MANAGE_DOCUMENTATION)
    assert has_permission(technician_user, Permission.VIEW_DOCUMENTATION)
    assert not has_permission(technician_user, Permission.MANAGE_TROUBLESHOOTING)
    assert has_permission(technician_user, Permission.VIEW_TROUBLESHOOTING)
    assert not has_permission(technician_user, Permission.MANAGE_MAINTENANCE)
    assert has_permission(technician_user, Permission.VIEW_MAINTENANCE)
    assert not has_permission(technician_user, Permission.MANAGE_SYSTEM)
    assert not has_permission(technician_user, Permission.VIEW_SYSTEM)
    
    # Create a mock user with guest role
    guest_user = MagicMock(spec=User)
    guest_user.role = UserRole.GUEST
    guest_user.is_superuser = False
    
    # Test guest permissions
    assert not has_permission(guest_user, Permission.MANAGE_USERS)
    assert not has_permission(guest_user, Permission.VIEW_USERS)
    assert not has_permission(guest_user, Permission.MANAGE_DOCUMENTATION)
    assert has_permission(guest_user, Permission.VIEW_DOCUMENTATION)
    assert not has_permission(guest_user, Permission.MANAGE_TROUBLESHOOTING)
    assert not has_permission(guest_user, Permission.VIEW_TROUBLESHOOTING)
    assert not has_permission(guest_user, Permission.MANAGE_MAINTENANCE)
    assert not has_permission(guest_user, Permission.VIEW_MAINTENANCE)
    assert not has_permission(guest_user, Permission.MANAGE_SYSTEM)
    assert not has_permission(guest_user, Permission.VIEW_SYSTEM)


def test_superuser_has_all_permissions():
    """Test that a superuser has all permissions."""
    # Create a mock user with guest role but is a superuser
    superuser = MagicMock(spec=User)
    superuser.role = UserRole.GUEST
    superuser.is_superuser = True
    
    # Test that the superuser has all permissions
    assert has_permission(superuser, Permission.MANAGE_USERS)
    assert has_permission(superuser, Permission.VIEW_USERS)
    assert has_permission(superuser, Permission.MANAGE_DOCUMENTATION)
    assert has_permission(superuser, Permission.VIEW_DOCUMENTATION)
    assert has_permission(superuser, Permission.MANAGE_TROUBLESHOOTING)
    assert has_permission(superuser, Permission.VIEW_TROUBLESHOOTING)
    assert has_permission(superuser, Permission.MANAGE_MAINTENANCE)
    assert has_permission(superuser, Permission.VIEW_MAINTENANCE)
    assert has_permission(superuser, Permission.MANAGE_SYSTEM)
    assert has_permission(superuser, Permission.VIEW_SYSTEM)
