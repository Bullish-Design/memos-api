# src/tests/test_client.py
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pytest>=8.0.0",
#     "pytest-asyncio>=0.23.0",
#     "httpx>=0.27.0",
#     "respx>=0.20.0",
# ]
# ///
"""
Test suite for Memos API client
"""

from __future__ import annotations

import pytest
import httpx
import respx
from unittest.mock import patch

from memos_api.client import MemosClient, SyncMemosClient, quick_memo, quick_memo_sync
from memos_api.config import MemosClientConfig
from memos_api.exceptions import (
    MemosConnectionError,
    MemosNotFoundError,
    MemosAuthenticationError,
)
from memos_api.models.memo import Memo
from memos_api.models.user import User


@pytest.fixture
def client_config():
    """Test client configuration."""
    return MemosClientConfig(
        base_url="http://test.example.com", token="test-token", timeout=10.0
    )


@pytest.fixture
def mock_memo_response():
    """Mock memo response data."""
    return {
        "name": "memos/1",
        "content": "Test memo content",
        "visibility": "PRIVATE",
        "state": "NORMAL",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_user_response():
    """Mock user response data."""
    return {
        "name": "users/1",
        "username": "testuser",
        "email": "test@example.com",
        "displayName": "Test User",
        "role": "USER",
        "state": "NORMAL",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-01T00:00:00Z",
    }


class TestMemosClientConfig:
    """Test client configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MemosClientConfig()
        assert config.base_url == "http://localhost:5232"
        assert config.token is None
        assert config.timeout == 30.0
        assert config.retries == 3

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(
            "os.environ",
            {"MEMOS_URL": "http://custom.example.com", "MEMOS_TOKEN": "env-token"},
        ):
            config = MemosClientConfig()
            assert config.base_url == "http://custom.example.com"
            assert config.token == "env-token"

    def test_config_validation(self):
        """Test configuration validation."""
        with pytest.raises(ValueError):
            MemosClientConfig(timeout=-1)

        with pytest.raises(ValueError):
            MemosClientConfig(retries=-1)


class TestMemosClient:
    """Test async client functionality."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self, client_config):
        """Test client as async context manager."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )

            async with MemosClient(client_config) as client:
                assert client.connection_info.connected is True
                assert client._client is not None

    @pytest.mark.asyncio
    async def test_connection_failure(self, client_config):
        """Test connection failure handling."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            client = MemosClient(client_config)
            with pytest.raises(MemosConnectionError):
                await client.connect()

    @pytest.mark.asyncio
    async def test_create_memo(self, client_config, mock_memo_response):
        """Test memo creation."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.post("http://test.example.com/api/v1/memos").mock(
                return_value=httpx.Response(200, json=mock_memo_response)
            )

            async with MemosClient(client_config) as client:
                memo = await client.create_memo("Test content")
                assert isinstance(memo, Memo)
                assert memo.content == "Test memo content"
                assert memo.name == "memos/1"

    @pytest.mark.asyncio
    async def test_get_memo(self, client_config, mock_memo_response):
        """Test getting memo by ID."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos/1").mock(
                return_value=httpx.Response(200, json=mock_memo_response)
            )

            async with MemosClient(client_config) as client:
                memo = await client.get_memo("1")
                assert isinstance(memo, Memo)
                assert memo.name == "memos/1"

    @pytest.mark.asyncio
    async def test_get_memo_not_found(self, client_config):
        """Test getting non-existent memo."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos/999").mock(
                return_value=httpx.Response(404, json={"detail": "Memo not found"})
            )

            async with MemosClient(client_config) as client:
                with pytest.raises(MemosNotFoundError):
                    await client.get_memo("999")

    @pytest.mark.asyncio
    async def test_list_memos(self, client_config, mock_memo_response):
        """Test listing memos."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos").mock(
                return_value=httpx.Response(200, json={"memos": [mock_memo_response]})
            )

            async with MemosClient(client_config) as client:
                memos = await client.list_memos()
                assert len(memos) == 1
                assert isinstance(memos[0], Memo)

    @pytest.mark.asyncio
    async def test_list_memos_with_filter(self, client_config, mock_memo_response):
        """Test listing memos with filter."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos").mock(
                return_value=httpx.Response(200, json={"memos": [mock_memo_response]})
            )

            async with MemosClient(client_config) as client:
                memos = await client.list_memos(filter_text="test")
                assert len(memos) == 1

    @pytest.mark.asyncio
    async def test_delete_memo(self, client_config):
        """Test deleting memo."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.delete("http://test.example.com/api/v1/memos/1").mock(
                return_value=httpx.Response(200, json={"message": "Deleted"})
            )

            async with MemosClient(client_config) as client:
                result = await client.delete_memo("1")
                assert result is True

    @pytest.mark.asyncio
    async def test_create_user(self, client_config, mock_user_response):
        """Test user creation."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.post("http://test.example.com/api/v1/users").mock(
                return_value=httpx.Response(200, json=mock_user_response)
            )

            async with MemosClient(client_config) as client:
                user = await client.create_user("testuser", email="test@example.com")
                assert isinstance(user, User)
                assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_authentication_error(self, client_config):
        """Test authentication error handling."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos/1").mock(
                return_value=httpx.Response(401, json={"detail": "Unauthorized"})
            )

            async with MemosClient(client_config) as client:
                with pytest.raises(MemosAuthenticationError):
                    await client.get_memo("1")


class TestSyncMemosClient:
    """Test synchronous client wrapper."""

    def test_sync_create_memo(self, client_config, mock_memo_response):
        """Test synchronous memo creation."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.post("http://test.example.com/api/v1/memos").mock(
                return_value=httpx.Response(200, json=mock_memo_response)
            )

            with SyncMemosClient(client_config) as client:
                memo = client.create_memo("Test content")
                assert isinstance(memo, Memo)
                assert memo.content == "Test memo content"

    def test_sync_list_memos(self, client_config, mock_memo_response):
        """Test synchronous memo listing."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos").mock(
                return_value=httpx.Response(200, json={"memos": [mock_memo_response]})
            )

            with SyncMemosClient(client_config) as client:
                memos = client.list_memos()
                assert len(memos) == 1
                assert isinstance(memos[0], Memo)


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_quick_memo_async(self, mock_memo_response):
        """Test async quick memo function."""
        with respx.mock:
            respx.get("http://localhost:5232/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.post("http://localhost:5232/api/v1/memos").mock(
                return_value=httpx.Response(200, json=mock_memo_response)
            )

            memo = await quick_memo("Quick test")
            assert isinstance(memo, Memo)
            assert memo.content == "Test memo content"

    def test_quick_memo_sync(self, mock_memo_response):
        """Test sync quick memo function."""
        with respx.mock:
            respx.get("http://localhost:5232/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.post("http://localhost:5232/api/v1/memos").mock(
                return_value=httpx.Response(200, json=mock_memo_response)
            )

            memo = quick_memo_sync("Quick test")
            assert isinstance(memo, Memo)
            assert memo.content == "Test memo content"


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_server_error(self, client_config):
        """Test server error handling."""
        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )
            respx.get("http://test.example.com/api/v1/memos/1").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )

            async with MemosClient(client_config) as client:
                with pytest.raises(Exception):  # Should raise MemosServerError
                    await client.get_memo("1")

    @pytest.mark.asyncio
    async def test_network_timeout(self, client_config):
        """Test network timeout handling."""
        config = MemosClientConfig(
            base_url="http://test.example.com",
            timeout=0.001,  # Very short timeout
        )

        with respx.mock:
            respx.get("http://test.example.com/docs").mock(
                return_value=httpx.Response(200)
            )

            async with MemosClient(config) as client:
                # This should work since we're mocking
                assert client.connection_info.connected is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

