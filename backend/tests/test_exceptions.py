"""
Tests for custom exceptions and error handlers - SPEC Section 8 compliance.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error_handlers import register_exception_handlers
from app.core.exceptions import (
    AppError,
    ErrorCode,
    ForbiddenError,
    InsufficientBalanceError,
    InsufficientPositionError,
    InternalError,
    InvalidQuantityError,
    MarketNotOpenError,
    NotFoundError,
    PriceBoundaryExceededError,
    TokenExpiredError,
    UnauthorizedError,
    ValidationError,
)


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI app with error handlers registered."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise-insufficient-balance")
    async def raise_insufficient_balance():
        raise InsufficientBalanceError()

    @app.get("/raise-insufficient-position")
    async def raise_insufficient_position():
        raise InsufficientPositionError()

    @app.get("/raise-market-not-open")
    async def raise_market_not_open():
        raise MarketNotOpenError()

    @app.get("/raise-invalid-quantity")
    async def raise_invalid_quantity():
        raise InvalidQuantityError()

    @app.get("/raise-price-boundary")
    async def raise_price_boundary():
        raise PriceBoundaryExceededError()

    @app.get("/raise-unauthorized")
    async def raise_unauthorized():
        raise UnauthorizedError()

    @app.get("/raise-forbidden")
    async def raise_forbidden():
        raise ForbiddenError()

    @app.get("/raise-token-expired")
    async def raise_token_expired():
        raise TokenExpiredError()

    @app.get("/raise-not-found")
    async def raise_not_found():
        raise NotFoundError()

    @app.get("/raise-validation-error")
    async def raise_validation_error():
        raise ValidationError(details={"field": "email", "message": "invalid format"})

    @app.get("/raise-internal-error")
    async def raise_internal_error():
        raise InternalError()

    @app.get("/raise-custom-message")
    async def raise_custom_message():
        raise InsufficientBalanceError(
            message="You need 100 more points",
            details={"required": 150, "available": 50},
        )

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(test_app)


class TestErrorCode:
    """Test ErrorCode enum values match SPEC Section 8."""

    def test_trading_error_codes_exist(self) -> None:
        """Trading error codes should exist (SPEC Section 8.1)."""
        assert ErrorCode.INSUFFICIENT_BALANCE.value == "INSUFFICIENT_BALANCE"
        assert ErrorCode.INSUFFICIENT_POSITION.value == "INSUFFICIENT_POSITION"
        assert ErrorCode.MARKET_NOT_OPEN.value == "MARKET_NOT_OPEN"
        assert ErrorCode.INVALID_QUANTITY.value == "INVALID_QUANTITY"
        assert ErrorCode.PRICE_BOUNDARY_EXCEEDED.value == "PRICE_BOUNDARY_EXCEEDED"

    def test_auth_error_codes_exist(self) -> None:
        """Auth error codes should exist (SPEC Section 8.2)."""
        assert ErrorCode.UNAUTHORIZED.value == "UNAUTHORIZED"
        assert ErrorCode.FORBIDDEN.value == "FORBIDDEN"
        assert ErrorCode.TOKEN_EXPIRED.value == "TOKEN_EXPIRED"

    def test_general_error_codes_exist(self) -> None:
        """General error codes should exist (SPEC Section 8.3)."""
        assert ErrorCode.NOT_FOUND.value == "NOT_FOUND"
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"


class TestAppError:
    """Test base AppError class."""

    def test_app_error_has_required_attributes(self) -> None:
        """AppError should have error_code, message, status_code, details."""
        exc = AppError(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Test error",
            status_code=500,
            details={"key": "value"},
        )
        assert exc.error_code == ErrorCode.INTERNAL_ERROR
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.details == {"key": "value"}

    def test_app_error_details_default_to_none(self) -> None:
        """AppError details should default to None."""
        exc = AppError(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Test error",
            status_code=500,
        )
        assert exc.details is None


class TestTradingExceptions:
    """Test trading exception classes (SPEC Section 8.1)."""

    def test_insufficient_balance_error(self) -> None:
        """InsufficientBalanceError should have correct defaults."""
        exc = InsufficientBalanceError()
        assert exc.error_code == ErrorCode.INSUFFICIENT_BALANCE
        assert exc.status_code == 400
        assert "balance" in exc.message.lower() or "残高" in exc.message

    def test_insufficient_position_error(self) -> None:
        """InsufficientPositionError should have correct defaults."""
        exc = InsufficientPositionError()
        assert exc.error_code == ErrorCode.INSUFFICIENT_POSITION
        assert exc.status_code == 400

    def test_market_not_open_error(self) -> None:
        """MarketNotOpenError should have correct defaults."""
        exc = MarketNotOpenError()
        assert exc.error_code == ErrorCode.MARKET_NOT_OPEN
        assert exc.status_code == 400

    def test_invalid_quantity_error(self) -> None:
        """InvalidQuantityError should have correct defaults."""
        exc = InvalidQuantityError()
        assert exc.error_code == ErrorCode.INVALID_QUANTITY
        assert exc.status_code == 400

    def test_price_boundary_exceeded_error(self) -> None:
        """PriceBoundaryExceededError should have correct defaults."""
        exc = PriceBoundaryExceededError()
        assert exc.error_code == ErrorCode.PRICE_BOUNDARY_EXCEEDED
        assert exc.status_code == 400


class TestAuthExceptions:
    """Test authentication/authorization exception classes (SPEC Section 8.2)."""

    def test_unauthorized_error(self) -> None:
        """UnauthorizedError should return 401."""
        exc = UnauthorizedError()
        assert exc.error_code == ErrorCode.UNAUTHORIZED
        assert exc.status_code == 401

    def test_forbidden_error(self) -> None:
        """ForbiddenError should return 403."""
        exc = ForbiddenError()
        assert exc.error_code == ErrorCode.FORBIDDEN
        assert exc.status_code == 403

    def test_token_expired_error(self) -> None:
        """TokenExpiredError should return 401."""
        exc = TokenExpiredError()
        assert exc.error_code == ErrorCode.TOKEN_EXPIRED
        assert exc.status_code == 401


class TestGeneralExceptions:
    """Test general exception classes (SPEC Section 8.3)."""

    def test_not_found_error(self) -> None:
        """NotFoundError should return 404."""
        exc = NotFoundError()
        assert exc.error_code == ErrorCode.NOT_FOUND
        assert exc.status_code == 404

    def test_validation_error(self) -> None:
        """ValidationError should return 422."""
        exc = ValidationError()
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 422

    def test_internal_error(self) -> None:
        """InternalError should return 500."""
        exc = InternalError()
        assert exc.error_code == ErrorCode.INTERNAL_ERROR
        assert exc.status_code == 500


class TestErrorHandlers:
    """Test FastAPI error handlers return correct response format."""

    def test_response_format_has_required_fields(self, client: TestClient) -> None:
        """Error response should have error_code, message, details fields."""
        response = client.get("/raise-insufficient-balance")
        assert response.status_code == 400
        data = response.json()
        assert "error_code" in data
        assert "message" in data
        assert "details" in data

    def test_insufficient_balance_response(self, client: TestClient) -> None:
        """InsufficientBalanceError should return 400 with correct error_code."""
        response = client.get("/raise-insufficient-balance")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INSUFFICIENT_BALANCE"

    def test_insufficient_position_response(self, client: TestClient) -> None:
        """InsufficientPositionError should return 400 with correct error_code."""
        response = client.get("/raise-insufficient-position")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INSUFFICIENT_POSITION"

    def test_market_not_open_response(self, client: TestClient) -> None:
        """MarketNotOpenError should return 400 with correct error_code."""
        response = client.get("/raise-market-not-open")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "MARKET_NOT_OPEN"

    def test_invalid_quantity_response(self, client: TestClient) -> None:
        """InvalidQuantityError should return 400 with correct error_code."""
        response = client.get("/raise-invalid-quantity")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_QUANTITY"

    def test_price_boundary_response(self, client: TestClient) -> None:
        """PriceBoundaryExceededError should return 400 with correct error_code."""
        response = client.get("/raise-price-boundary")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "PRICE_BOUNDARY_EXCEEDED"

    def test_unauthorized_response(self, client: TestClient) -> None:
        """UnauthorizedError should return 401 with correct error_code."""
        response = client.get("/raise-unauthorized")
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"

    def test_forbidden_response(self, client: TestClient) -> None:
        """ForbiddenError should return 403 with correct error_code."""
        response = client.get("/raise-forbidden")
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "FORBIDDEN"

    def test_token_expired_response(self, client: TestClient) -> None:
        """TokenExpiredError should return 401 with correct error_code."""
        response = client.get("/raise-token-expired")
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "TOKEN_EXPIRED"

    def test_not_found_response(self, client: TestClient) -> None:
        """NotFoundError should return 404 with correct error_code."""
        response = client.get("/raise-not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "NOT_FOUND"

    def test_validation_error_response(self, client: TestClient) -> None:
        """ValidationError should return 422 with correct error_code."""
        response = client.get("/raise-validation-error")
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert data["details"] == {"field": "email", "message": "invalid format"}

    def test_internal_error_response(self, client: TestClient) -> None:
        """InternalError should return 500 with correct error_code."""
        response = client.get("/raise-internal-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"

    def test_custom_message_and_details(self, client: TestClient) -> None:
        """Custom message and details should be included in response."""
        response = client.get("/raise-custom-message")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INSUFFICIENT_BALANCE"
        assert data["message"] == "You need 100 more points"
        assert data["details"] == {"required": 150, "available": 50}
