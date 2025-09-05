# src/memos_api/config.py
"""
Configuration classes for Memos API client
"""

from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

load_dotenv()


class MemosClientConfig(BaseModel):
    """Configuration for Memos API client."""

    base_url: str = Field(
        default_factory=lambda: os.getenv("MEMOS_URL", "http://localhost:5232"),
        description="Base URL for the Memos API server",
    )
    token: Optional[str] = Field(
        default_factory=lambda: os.getenv("MEMOS_TOKEN"),
        description="Authentication token for API requests",
    )
    timeout: float = Field(default=30.0, gt=0, description="Request timeout in seconds")
    retries: int = Field(
        default=3, ge=0, description="Number of retry attempts for failed requests"
    )

    model_config = ConfigDict(env_prefix="MEMOS_", validate_assignment=True)


class MemosConnectionInfo(BaseModel):
    """Connection information and status."""

    base_url: str
    connected: bool = False
    server_version: Optional[str] = None
    last_error: Optional[str] = None

