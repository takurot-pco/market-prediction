"""
Custom exception classes for the Market Prediction API.
SPEC Section 8 compliant error codes and exceptions.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Error codes as defined in SPEC Section 8."""

    # Trading errors (Section 8.1)
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    INSUFFICIENT_POSITION = "INSUFFICIENT_POSITION"
    MARKET_NOT_OPEN = "MARKET_NOT_OPEN"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    PRICE_BOUNDARY_EXCEEDED = "PRICE_BOUNDARY_EXCEEDED"

    # Auth errors (Section 8.2)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # General errors (Section 8.3)
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """Base exception class for all application exceptions.

    Attributes:
        error_code: The error code from ErrorCode enum
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details (optional)
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


# Trading Exceptions (SPEC Section 8.1)


class InsufficientBalanceError(AppError):
    """Raised when user doesn't have enough balance for a transaction."""

    def __init__(
        self,
        message: str = "Insufficient balance for this transaction",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.INSUFFICIENT_BALANCE,
            message=message,
            status_code=400,
            details=details,
        )


class InsufficientPositionError(AppError):
    """Raised when user doesn't have enough position to sell."""

    def __init__(
        self,
        message: str = "Insufficient position for this sale",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.INSUFFICIENT_POSITION,
            message=message,
            status_code=400,
            details=details,
        )


class MarketNotOpenError(AppError):
    """Raised when trying to trade on a market that is not open."""

    def __init__(
        self,
        message: str = "Market is not open for trading",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.MARKET_NOT_OPEN,
            message=message,
            status_code=400,
            details=details,
        )


class InvalidQuantityError(AppError):
    """Raised when an invalid quantity is specified."""

    def __init__(
        self,
        message: str = "Invalid quantity specified",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_QUANTITY,
            message=message,
            status_code=400,
            details=details,
        )


class PriceBoundaryExceededError(AppError):
    """Raised when price would exceed allowed boundaries (0.1% - 99.9%)."""

    def __init__(
        self,
        message: str = "Price boundary exceeded (allowed: 0.1% - 99.9%)",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.PRICE_BOUNDARY_EXCEEDED,
            message=message,
            status_code=400,
            details=details,
        )


# Auth Exceptions (SPEC Section 8.2)


class UnauthorizedError(AppError):
    """Raised when authentication is required but not provided."""

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=401,
            details=details,
        )


class ForbiddenError(AppError):
    """Raised when user doesn't have permission for the action."""

    def __init__(
        self,
        message: str = "Permission denied",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=403,
            details=details,
        )


class TokenExpiredError(AppError):
    """Raised when the authentication token has expired."""

    def __init__(
        self,
        message: str = "Token has expired",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.TOKEN_EXPIRED,
            message=message,
            status_code=401,
            details=details,
        )


# General Exceptions (SPEC Section 8.3)


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=message,
            status_code=404,
            details=details,
        )


class ValidationError(AppError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=422,
            details=details,
        )


class InternalError(AppError):
    """Raised for internal server errors."""

    def __init__(
        self,
        message: str = "Internal server error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=message,
            status_code=500,
            details=details,
        )
