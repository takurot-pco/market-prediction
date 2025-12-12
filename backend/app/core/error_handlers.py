"""
FastAPI exception handlers for the Market Prediction API.
Converts AppError instances to standardized JSON error responses.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


def create_error_response(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response dictionary.

    Args:
        error_code: The error code string
        message: Human-readable error message
        details: Additional error details (optional)

    Returns:
        Error response dictionary with error_code, message, and details fields
    """
    return {
        "error_code": error_code,
        "message": message,
        "details": details,
    }


async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    """Handle AppError and return JSON response.

    Args:
        request: The FastAPI request object
        exc: The AppError instance

    Returns:
        JSONResponse with error details and appropriate status code
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=exc.error_code.value,
            message=exc.message,
            details=exc.details,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application.

    Args:
        app: The FastAPI application instance
    """
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
