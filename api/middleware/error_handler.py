"""
Global Error Handler Middleware for API V1
==========================================
Provides consistent error responses across all endpoints.
All errors are converted to ErrorResponse schema with proper status codes.
Maps exceptions to HTTP status codes and error codes automatically.
"""

from fastapi import Request, status, FastAPI, HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime
import json
import uuid
from api.utils.timeutils import utcnow as _naive_utcnow
logger = logging.getLogger(__name__)


def _response_headers(request_id: str) -> dict:
    return {"X-Request-ID": request_id}


class ErrorHandler:
    """Global error handler for consistent error responses."""
    
    @staticmethod
    def to_error_response(
        error_code: str,
        message: str,
        status_code: int,
        detail: str = None,
        request_id: str = None
    ) -> dict:
        """
        Convert error to standard ErrorResponse format.
        
        Args:
            error_code: Machine-readable error code (e.g., "validation_error", "unauthorized")
            message: Human-readable error message
            status_code: HTTP status code
            detail: Optional additional error details
            request_id: Optional request ID for debugging
        
        Returns:
            Dictionary matching ErrorResponse schema
        """
        return {
            "error": error_code,
            "message": message,
            "status_code": status_code,
            "timestamp": _naive_utcnow().isoformat() + "Z",
            "detail": detail,
            "request_id": request_id or str(uuid.uuid4())
        }
    
    @staticmethod
    def map_exception_to_status_code(exception: Exception) -> tuple[str, int]:
        """Map Python exception types to error codes and HTTP status codes."""
        exception_type = type(exception).__name__
        
        mappings = {
            "ValueError": ("validation_error", status.HTTP_400_BAD_REQUEST),
            "KeyError": ("not_found", status.HTTP_404_NOT_FOUND),
            "PermissionError": ("forbidden", status.HTTP_403_FORBIDDEN),
            "TimeoutError": ("gateway_timeout", status.HTTP_504_GATEWAY_TIMEOUT),
            "ConnectionError": ("service_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE),
            "FileNotFoundError": ("not_found", status.HTTP_404_NOT_FOUND),
            "AttributeError": ("server_error", status.HTTP_500_INTERNAL_SERVER_ERROR),
            "TypeError": ("validation_error", status.HTTP_400_BAD_REQUEST),
            "RuntimeError": ("server_error", status.HTTP_500_INTERNAL_SERVER_ERROR),
        }
        
        return mappings.get(exception_type, ("server_error", status.HTTP_500_INTERNAL_SERVER_ERROR))


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTPException and convert to ErrorResponse format.
    Supports both simple string details and structured error details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Extract detail from HTTPException
    detail_obj = None
    if isinstance(exc.detail, dict):
        # Already a structured error (like {"error": "...", "message": "..."})
        if "error" in exc.detail and "message" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail["error"],
                    "message": exc.detail["message"],
                    "status_code": exc.status_code,
                    "timestamp": _naive_utcnow().isoformat() + "Z",
                    "detail": exc.detail.get("detail"),
                    "request_id": request_id
                },
                headers=_response_headers(request_id),
            )
        detail_obj = exc.detail

    # Map status code to error code
    error_code = _status_to_error_code(exc.status_code)
    message = str(exc.detail) if isinstance(exc.detail, str) else str(exc.detail)
    
    response = ErrorHandler.to_error_response(
        error_code=error_code,
        message=message,
        status_code=exc.status_code,
        detail=detail_obj if isinstance(detail_obj, str) else None,
        request_id=request_id
    )
    return JSONResponse(status_code=exc.status_code, content=response, headers=_response_headers(request_id))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI validation errors (422 Unprocessable Entity).
    Converts to standard error response with validation details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip "body"
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    response = ErrorHandler.to_error_response(
        error_code="validation_error",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=json.dumps({"validation_errors": errors}),
        request_id=request_id
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response,
        headers=_response_headers(request_id),
    )


def _capture_error(request: Request, exc: Exception, request_id: str) -> None:
    """Best-effort: record the error for ALFa AI triage. Never raises."""
    try:
        from api.services.error_monitor import record_error

        record_error(
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=str(getattr(request.url, "path", "")),
            method=getattr(request, "method", ""),
            request_id=request_id,
            traceback_text=traceback.format_exc(),
        )
    except Exception:
        pass


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handle ValueError and convert to 400 Bad Request.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(f"ValueError in {request.url.path}: {str(exc)}")
    _capture_error(request, exc, request_id)
    
    response = ErrorHandler.to_error_response(
        error_code="validation_error",
        message=str(exc),
        status_code=status.HTTP_400_BAD_REQUEST,
        request_id=request_id
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response,
        headers=_response_headers(request_id),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler for unexpected errors.
    Logs full traceback but returns safe error response (no internal details).
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path} [request_id: {request_id}]\n"
        f"Exception: {type(exc).__name__}: {str(exc)}\n"
        f"Traceback:\n{traceback.format_exc()}"
    )
    _capture_error(request, exc, request_id)
    
    # Map exception to error code
    error_code, http_status = ErrorHandler.map_exception_to_status_code(exc)
    
    response = ErrorHandler.to_error_response(
        error_code=error_code,
        message="An unexpected error occurred. Please try again later.",
        status_code=http_status,
        request_id=request_id
    )
    return JSONResponse(
        status_code=http_status,
        content=response,
        headers=_response_headers(request_id),
    )


def register_exception_handlers(app: FastAPI):
    """
    Register all global exception handlers on FastAPI app.
    
    Usage:
        from api.middleware.error_handler import register_exception_handlers
        register_exception_handlers(app)
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered successfully")


def _status_to_error_code(status_code: int) -> str:
    """Convert HTTP status code to machine-readable error code."""
    mappings = {
        status.HTTP_400_BAD_REQUEST: "validation_error",
        status.HTTP_401_UNAUTHORIZED: "unauthorized",
        status.HTTP_403_FORBIDDEN: "forbidden",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_422_UNPROCESSABLE_CONTENT: "validation_error",
        status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "server_error",
        status.HTTP_502_BAD_GATEWAY: "bad_gateway",
        status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
        status.HTTP_504_GATEWAY_TIMEOUT: "gateway_timeout",
    }
    return mappings.get(status_code, "server_error")
