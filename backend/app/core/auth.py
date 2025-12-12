"""
Authentication utilities for JWT token handling.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.exceptions import TokenExpiredError, UnauthorizedError

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The subject of the token (typically user ID)
        expires_delta: Optional custom expiry time
        additional_claims: Optional additional claims to include in the token

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_expire_minutes)

    expire = datetime.now(UTC) + expires_delta

    to_encode: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded: str = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Args:
        token: The JWT token string to decode

    Returns:
        The decoded token payload

    Raises:
        TokenExpiredError: If the token has expired
        UnauthorizedError: If the token is invalid
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except ExpiredSignatureError as e:
        raise TokenExpiredError() from e
    except JWTError as e:
        raise UnauthorizedError(message="Invalid token") from e


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """FastAPI dependency to get the current user ID from JWT token.

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        The user ID from the token

    Raises:
        UnauthorizedError: If no token provided or token is invalid
    """
    if credentials is None:
        raise UnauthorizedError(message="Authentication required")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")

    if user_id is None:
        raise UnauthorizedError(message="Invalid token payload")

    return cast(str, user_id)


# Alias for backwards compatibility and cleaner API
get_current_user = get_current_user_id
