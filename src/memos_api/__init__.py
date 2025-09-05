# src/memos_api/__init__.py
"""
Memotic - FastAPI Memos Library
"""
from __future__ import annotations

from .api import MemosAPI
from .client import MemosClient, SyncMemosClient, quick_memo, quick_memo_sync
from .config import MemosClientConfig
from .exceptions import (
    MemosAPIError,
    MemosAuthenticationError,
    MemosConnectionError,
    MemosNotFoundError,
    MemosServerError,
    MemosValidationError,
)
from .models import Memo, User
from .storage import AppStorage

__version__ = "0.3.1"
__all__ = [
    # Core API
    "MemosAPI",
    "AppStorage",
    # Client
    "MemosClient",
    "SyncMemosClient", 
    "MemosClientConfig",
    # Convenience functions
    "quick_memo",
    "quick_memo_sync",
    # Models
    "Memo",
    "User",
    # Exceptions
    "MemosAPIError",
    "MemosAuthenticationError", 
    "MemosConnectionError",
    "MemosNotFoundError",
    "MemosServerError",
    "MemosValidationError",
]