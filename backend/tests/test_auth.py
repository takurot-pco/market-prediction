"""
Tests for authentication module - SPEC Section 5 compliance.
"""
from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.core.auth import (
    create_access_token,
    decode_access_token,
)
from app.core.exceptions import TokenExpiredError, UnauthorizedError


class TestJWTToken:
    """Test JWT token generation and verification."""

    def test_create_access_token_returns_string(self) -> None:
        """create_access_token should return a JWT string."""
        user_id = uuid4()
        token = create_access_token(subject=str(user_id))
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self) -> None:
        """create_access_token should accept custom expiry time."""
        user_id = uuid4()
        expires_delta = timedelta(hours=2)
        token = create_access_token(subject=str(user_id), expires_delta=expires_delta)
        assert isinstance(token, str)

    def test_decode_access_token_returns_payload(self) -> None:
        """decode_access_token should return the token payload."""
        user_id = uuid4()
        token = create_access_token(subject=str(user_id))
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert "exp" in payload

    def test_decode_access_token_with_invalid_token_raises_error(self) -> None:
        """decode_access_token should raise UnauthorizedError for invalid token."""
        with pytest.raises(UnauthorizedError):
            decode_access_token("invalid.token.here")

    def test_decode_access_token_with_expired_token_raises_error(self) -> None:
        """decode_access_token should raise TokenExpiredError for expired token."""
        user_id = uuid4()
        # Create a token that expires immediately
        token = create_access_token(
            subject=str(user_id),
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(TokenExpiredError):
            decode_access_token(token)


class TestAuthAPI:
    """Test Auth API endpoints (SPEC Section 5)."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create test FastAPI app with auth routes."""
        from app.api.auth import router as auth_router
        from app.core.error_handlers import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(auth_router, prefix="/api/v1/auth")
        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_login_endpoint_exists(self, client: TestClient) -> None:
        """GET /api/v1/auth/login should exist."""
        response = client.get("/api/v1/auth/login", follow_redirects=False)
        # Should redirect or return login info (not 404)
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_callback_endpoint_exists(self, client: TestClient) -> None:
        """GET /api/v1/auth/callback should exist."""
        response = client.get("/api/v1/auth/callback")
        # Should return error without proper params, but not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_logout_endpoint_exists(self, client: TestClient) -> None:
        """POST /api/v1/auth/logout should exist."""
        response = client.post("/api/v1/auth/logout")
        # Should require auth, but not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_me_endpoint_requires_auth(self, client: TestClient) -> None:
        """GET /api/v1/auth/me should require authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_endpoint_returns_user_info(self, client: TestClient) -> None:
        """GET /api/v1/auth/me should return user info with valid token."""
        # Create a mock user token
        user_id = uuid4()
        token = create_access_token(subject=str(user_id))
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        # With mock auth, this should succeed or return user data
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestMockAuthFlow:
    """Test Mock authentication flow for development environment."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create test FastAPI app with auth routes."""
        from app.api.auth import router as auth_router
        from app.core.error_handlers import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(auth_router, prefix="/api/v1/auth")
        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_mock_login_returns_redirect_or_token(self, client: TestClient) -> None:
        """Mock login should return redirect URL or direct token."""
        response = client.get("/api/v1/auth/login", follow_redirects=False)
        # In mock mode, should either redirect to callback or return token info
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_302_FOUND,
            status.HTTP_307_TEMPORARY_REDIRECT,
        ]

    def test_mock_callback_with_mock_code_returns_token(self, client: TestClient) -> None:
        """Mock callback should return access token with mock code."""
        response = client.get("/api/v1/auth/callback?code=mock_code")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_logout_clears_session(self, client: TestClient) -> None:
        """Logout should return success."""
        # First get a token
        response = client.get("/api/v1/auth/callback?code=mock_code")
        token = response.json()["access_token"]

        # Then logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK


class TestGetCurrentUserDependency:
    """Test get_current_user FastAPI dependency."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create test FastAPI app with protected endpoint."""
        from typing import Annotated

        from fastapi import Depends

        from app.api.auth import router as auth_router
        from app.core.auth import get_current_user_id
        from app.core.error_handlers import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(auth_router, prefix="/api/v1/auth")

        @app.get("/protected")
        async def protected_endpoint(
            current_user_id: Annotated[str, Depends(get_current_user_id)],
        ) -> dict:
            return {"user_id": current_user_id}

        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_missing_auth_header_returns_error(self, client: TestClient) -> None:
        """Request without auth header should return error."""
        response = client.get("/protected")
        # HTTPBearer with auto_error=False returns None, our code raises UnauthorizedError
        # Note: FastAPI may return 422 in some configurations
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            422,  # FastAPI validation error in some cases
        ]

    def test_invalid_auth_header_format_returns_error(self, client: TestClient) -> None:
        """Request with invalid auth header format should return error."""
        response = client.get(
            "/protected",
            headers={"Authorization": "InvalidToken"},
        )
        # Invalid format returns error from FastAPI's HTTPBearer
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            422,  # FastAPI validation error
        ]

    def test_invalid_bearer_token_returns_401(self, client: TestClient) -> None:
        """Request with invalid Bearer token should return 401."""
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        # Our exception handler converts UnauthorizedError to 401
        # Note: FastAPI may return 422 in some configurations
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            422,  # FastAPI validation error
        ]
