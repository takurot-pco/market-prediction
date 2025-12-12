"""
Authentication API endpoints - SPEC Section 5 compliant.
"""
from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.core.auth import create_access_token, get_current_user_id
from app.core.config import settings

router = APIRouter(tags=["auth"])


class TokenResponse(BaseModel):
    """Response model for token endpoints."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Response model for user info endpoint."""

    id: str
    email: str
    name: str | None = None
    role: str = "user"
    department: str | None = None
    balance: float = 1000.00


# Mock user database for development
_mock_users: dict[str, dict] = {}


def _get_or_create_mock_user(user_id: str) -> dict:
    """Get or create a mock user for development."""
    if user_id not in _mock_users:
        _mock_users[user_id] = {
            "id": user_id,
            "email": f"user-{user_id[:8]}@example.com",
            "name": f"Mock User {user_id[:8]}",
            "role": "user",
            "department": "Engineering",
            "balance": 1000.00,
        }
    return _mock_users[user_id]


@router.get("/login", response_model=None)
async def login() -> RedirectResponse:
    """Start SSO authentication flow.

    In mock mode, redirects directly to callback with a mock code.
    In production, would redirect to Azure AD login page.
    """
    if settings.auth_provider == "mock":
        # Mock mode: redirect to callback with mock code
        return RedirectResponse(
            url="/api/v1/auth/callback?code=mock_code",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    # TODO: Implement Azure AD redirect
    # For now, mock mode is always used
    return RedirectResponse(
        url="/api/v1/auth/callback?code=mock_code",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


@router.get("/callback", response_model=TokenResponse)
async def callback(code: Annotated[str, Query(description="Authorization code")]) -> TokenResponse:
    """Handle authentication callback.

    In mock mode, accepts any code and returns a token for a mock user.
    In production, would exchange the code for Azure AD tokens.

    Args:
        code: Authorization code from the identity provider

    Returns:
        Access token response
    """
    # Mock mode: create a mock user and return token
    # TODO: Implement Azure AD token exchange when auth_provider != "mock"
    user_id = str(uuid4())
    _get_or_create_mock_user(user_id)

    token = create_access_token(subject=user_id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> dict:
    """Logout the current user.

    In a stateless JWT setup, this mainly serves as a client-side indicator.
    For stateful sessions, this would invalidate the session.

    Args:
        current_user_id: The current authenticated user's ID

    Returns:
        Logout success message
    """
    # In mock mode, we could remove the user from mock storage
    # In production with refresh tokens, we would invalidate them
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> UserResponse:
    """Get current user information.

    Args:
        current_user_id: The current authenticated user's ID

    Returns:
        Current user's information

    Raises:
        NotFoundError: If user not found in database
    """
    # Mock mode: return mock user data
    # TODO: Implement database lookup when auth_provider != "mock"
    user = _mock_users.get(current_user_id)
    if user is None:
        # Create a mock user if not exists (for testing)
        user = _get_or_create_mock_user(current_user_id)
    return UserResponse(**user)
