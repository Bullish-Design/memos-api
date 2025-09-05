# src/memos_api/exceptions.py
"""
Custom exceptions for Memos API client
"""
from __future__ import annotations

from typing import Optional

import httpx


class MemosAPIError(Exception):
    """Base exception for Memos API client errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class MemosConnectionError(MemosAPIError):
    """Raised when unable to connect to Memos API server."""
    pass


class MemosAuthenticationError(MemosAPIError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, 401)


class MemosNotFoundError(MemosAPIError):
    """Raised when requested resource is not found."""
    
    def __init__(self, resource: str, resource_id: str) -> None:
        message = f"{resource} '{resource_id}' not found"
        super().__init__(message, 404)


class MemosValidationError(MemosAPIError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message, 400)


class MemosServerError(MemosAPIError):
    """Raised when server returns 5xx error."""
    
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message, status_code)


def handle_http_error(response: httpx.Response, resource: str = "", resource_id: str = "") -> None:
    """Convert HTTP errors to appropriate Memos exceptions."""
    if response.status_code == 401:
        raise MemosAuthenticationError()
    elif response.status_code == 404 and resource:
        raise MemosNotFoundError(resource, resource_id)
    elif response.status_code == 400:
        try:
            detail = response.json().get("detail", "Validation failed")
        except Exception:
            detail = "Validation failed"
        raise MemosValidationError(detail)
    elif 500 <= response.status_code < 600:
        raise MemosServerError(f"Server error: {response.text}", response.status_code)
    else:
        raise MemosAPIError(f"HTTP {response.status_code}: {response.text}", response.status_code)