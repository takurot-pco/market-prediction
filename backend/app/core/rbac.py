"""
Role-Based Access Control (RBAC) for the Market Prediction API.
SPEC Section 5 compliant - implements role permissions.

Role hierarchy:
- Admin: Full access (can do everything)
- Moderator: Can create/edit/publish markets, plus User permissions
- User: Can view markets, trade, view own data
"""
from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import decode_access_token
from app.core.exceptions import ForbiddenError, UnauthorizedError

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """User roles as defined in SPEC Section 4."""

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


# Role hierarchy: higher roles include permissions of lower roles
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.USER: 1,
    UserRole.MODERATOR: 2,
    UserRole.ADMIN: 3,
}


def has_required_role(user_role: UserRole, required_role: UserRole) -> bool:
    """Check if user has the required role permission.

    Uses role hierarchy: admin > moderator > user.
    Higher roles automatically have permissions of lower roles.

    Args:
        user_role: The user's actual role
        required_role: The minimum role required for the action

    Returns:
        True if user has sufficient permissions, False otherwise
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


async def get_current_user_data(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    """FastAPI dependency to get current user data from JWT token.

    This is a simplified version that extracts user data from the JWT claims.
    In production, this would fetch the full user from the database.

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        Dictionary containing user data

    Raises:
        UnauthorizedError: If no token provided or token is invalid
    """
    if credentials is None:
        raise UnauthorizedError(message="Authentication required")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")

    if user_id is None:
        raise UnauthorizedError(message="Invalid token payload")

    # Extract user data from JWT claims
    # In production, you might want to fetch fresh data from DB
    return {
        "id": user_id,
        "email": payload.get("email", ""),
        "name": payload.get("name"),
        "role": payload.get("role", "user"),
        "department": payload.get("department"),
        "balance": payload.get("balance", 1000.00),
    }


class RoleChecker:
    """FastAPI dependency class for role-based access control.

    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(
            user: dict = Depends(RoleChecker(UserRole.ADMIN))
        ):
            return {"message": "Admin access granted"}

    Or with multiple allowed roles:
        @app.get("/moderator-or-admin")
        async def mod_admin_endpoint(
            user: dict = Depends(RoleChecker(UserRole.MODERATOR, UserRole.ADMIN))
        ):
            return {"message": "Access granted"}
    """

    def __init__(self, *roles: UserRole) -> None:
        """Initialize RoleChecker with required role(s).

        Args:
            *roles: One or more roles that are allowed access.
                   If multiple roles specified, uses the lowest (most permissive).
        """
        if not roles:
            raise ValueError("At least one role must be specified")

        self.allowed_roles = set(roles)
        # Use the lowest hierarchy level as the required role
        # This means if both MODERATOR and ADMIN are specified,
        # MODERATOR level is the minimum requirement
        self.required_role = min(roles, key=lambda r: ROLE_HIERARCHY.get(r, 0))

    async def __call__(
        self,
        user_data: dict[str, Any] = Depends(get_current_user_data),
    ) -> dict[str, Any]:
        """Check if current user has required role.

        Args:
            user_data: User data from get_current_user_data dependency

        Returns:
            The user data if role check passes

        Raises:
            ForbiddenError: If user doesn't have required role
        """
        user_role_str = user_data.get("role", "user")

        try:
            user_role = UserRole(user_role_str)
        except ValueError:
            # Unknown role, treat as user
            user_role = UserRole.USER

        if not has_required_role(user_role, self.required_role):
            raise ForbiddenError(
                message=f"Permission denied. Required role: {self.required_role.value}",
                details={
                    "required_role": self.required_role.value,
                    "user_role": user_role.value,
                },
            )

        return user_data


def get_current_user_with_role(
    required_role: UserRole,
) -> Callable[..., Any]:
    """Factory function to create a role-checking dependency.

    This is a convenience function for creating role-based dependencies
    in a more functional style.

    Args:
        required_role: The minimum role required for access

    Returns:
        A dependency function that checks role and returns user data

    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(
            user: dict = Depends(get_current_user_with_role(UserRole.ADMIN))
        ):
            return {"message": "Admin access granted"}
    """
    checker = RoleChecker(required_role)
    return checker


# Convenience dependencies for common role requirements
require_user = RoleChecker(UserRole.USER)
require_moderator = RoleChecker(UserRole.MODERATOR)
require_admin = RoleChecker(UserRole.ADMIN)
