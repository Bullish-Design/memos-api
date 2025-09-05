# src/tests/test_client_fixes.py
"""
Fixed test cases for client functionality
"""

from __future__ import annotations

import re
import pytest
import httpx
import respx
from unittest.mock import patch

from memos_api.client import MemosClient
from memos_api.config import MemosClientConfig
from memos_api.exceptions import (
    MemosConnectionError,
    MemosNotFoundError,
    MemosAuthenticationError,
)


class TestClientFixes:
    """Fixed test cases."""

    def test_default_config_clean_env(self):
        """Test default config without environment variables."""
        with patch.dict("os.environ", {}, clear=True):
            config = MemosClientConfig()
            assert config.base_url == "http://localhost:5232"

    @pytest.mark.asyncio
    async def test_connection_failure_direct(self):
        """Test connection failure handling."""
        config = MemosClientConfig(base_url="http://test.example.com")

        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            client = MemosClient(config)
            with pytest.raises(MemosConnectionError):
                await client.connect()

    @pytest.mark.asyncio
    async def test_memo_not_found_proper(self):
        """Test 404 error for memo returns MemosNotFoundError."""
        config = MemosClientConfig(base_url="http://test.example.com", retries=1)

        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos/999").mock(
                return_value=httpx.Response(404, json={"detail": "Not found"})
            )

            async with MemosClient(config) as client:
                with pytest.raises(MemosNotFoundError) as exc_info:
                    await client.get_memo("999")
                assert "memo" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_auth_error_proper(self):
        """Test 401 error returns MemosAuthenticationError."""
        config = MemosClientConfig(base_url="http://test.example.com", retries=1)

        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos/1").mock(
                return_value=httpx.Response(401, json={"detail": "Unauthorized"})
            )

            async with MemosClient(config) as client:
                with pytest.raises(MemosAuthenticationError):
                    await client.get_memo("1")


def test_cli_version_no_ansi():
    """Test CLI version command without ANSI codes."""
    from memos_api.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(app, ["version"])

    # Strip ANSI color codes for comparison
    clean_output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert result.exit_code == 0
    assert "Memotic CLI v0.1.0" in clean_output
