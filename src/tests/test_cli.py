"""
Tests for CLI functionality
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from memos_api.cli import app, get_auth_settings, APIClient


class TestCLISettings:
    """Test CLI configuration and settings."""

    def test_get_auth_settings_defaults(self):
        """Test default auth settings."""
        with patch.dict(os.environ, {}, clear=True):
            url, token = get_auth_settings()
            assert url == "http://localhost:5232"
            assert token is None

    def test_get_auth_settings_env_vars(self):
        """Test auth settings from environment variables."""
        env_vars = {
            "MEMOS_URL": "https://example.com:8080",
            "MEMOS_TOKEN": "test-token-123",
        }
        with patch.dict(os.environ, env_vars):
            url, token = get_auth_settings()
            assert url == "https://example.com:8080"
            assert token == "test-token-123"


class TestAPIClient:
    """Test API client functionality."""

    @pytest.mark.asyncio
    async def test_api_client_context_manager(self):
        """Test API client as context manager."""
        async with APIClient("http://test.com", "token") as client:
            assert client.base_url == "http://test.com"
            assert client.client.headers.get("Authorization") == "Bearer token"


class TestCLICommands:
    """Test CLI commands."""

    def setup_method(self):
        """Setup test runner."""
        self.runner = CliRunner()

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Memotic CLI v0.1.0" in result.stdout

    @patch("memos_api.cli.uvicorn.run")
    @patch("memos_api.cli.MemosAPI")
    def test_serve_command(self, mock_api, mock_uvicorn):
        """Test serve command."""
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        result = self.runner.invoke(
            app, ["serve", "--host", "localhost", "--port", "8000"]
        )
        assert result.exit_code == 0

        mock_api.assert_called_once()
        mock_uvicorn.assert_called_once()

        # Check uvicorn was called with correct parameters
        call_args = mock_uvicorn.call_args
        assert call_args[1]["host"] == "localhost"
        assert call_args[1]["port"] == 8000

    @patch("memos_api.cli.APIClient")
    def test_memo_create_command(self, mock_client_class):
        """Test memo create command."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "memos/1", "content": "test memo"}
        mock_client.client.post.return_value = mock_response

        mock_client_class.return_value.__aenter__.return_value = mock_client

        with patch("memos_api.cli.asyncio.run") as mock_run:
            result = self.runner.invoke(app, ["memo", "create", "test memo content"])
            assert result.exit_code == 0
            mock_run.assert_called_once()

    @patch("memos_api.cli.asyncio.run")
    @patch("memos_api.cli.APIClient")
    def test_memo_list_command(self, mock_client_class, mock_asyncio_run):
        """Test memo list command."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "memos": [
                {
                    "name": "memos/1",
                    "content": "Test memo",
                    "visibility": "PRIVATE",
                    "pinned": False,
                }
            ]
        }
        mock_client.client.get.return_value = mock_response

        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_asyncio_run.return_value = None

        result = self.runner.invoke(app, ["memo", "list"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("memos_api.cli.asyncio.run")
    @patch("memos_api.cli.APIClient")
    def test_memo_get_command(self, mock_client_class, mock_asyncio_run):
        """Test memo get command."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "memos/1",
            "content": "Test memo content",
            "visibility": "PRIVATE",
            "pinned": False,
        }
        mock_client.client.get.return_value = mock_response

        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_asyncio_run.return_value = None

        result = self.runner.invoke(app, ["memo", "get", "1"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("memos_api.cli.asyncio.run")
    @patch("memos_api.cli.APIClient")
    def test_user_create_command(self, mock_client_class, mock_asyncio_run):
        """Test user create command."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "users/2", "username": "newuser"}
        mock_client.client.post.return_value = mock_response

        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_asyncio_run.return_value = None

        result = self.runner.invoke(
            app, ["user", "create", "newuser", "--email", "new@example.com"]
        )
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("memos_api.cli.asyncio.run")
    @patch("memos_api.cli.APIClient")
    def test_user_list_command(self, mock_client_class, mock_asyncio_run):
        """Test user list command."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "users": [
                {
                    "name": "users/1",
                    "username": "admin",
                    "email": "admin@example.com",
                    "role": "ADMIN",
                }
            ]
        }
        mock_client.client.get.return_value = mock_response

        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_asyncio_run.return_value = None

        result = self.runner.invoke(app, ["user", "list"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("memos_api.cli.asyncio.run")
    @patch("memos_api.cli.APIClient")
    def test_status_command_success(self, mock_client_class, mock_asyncio_run):
        """Test status command with successful connection."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.client.get.return_value = mock_response

        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_asyncio_run.return_value = None

        result = self.runner.invoke(app, ["status"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    def test_memo_command_group(self):
        """Test memo command group help."""
        result = self.runner.invoke(app, ["memo", "--help"])
        assert result.exit_code == 0
        assert "Memo management commands" in result.stdout

    def test_user_command_group(self):
        """Test user command group help."""
        result = self.runner.invoke(app, ["user", "--help"])
        assert result.exit_code == 0
        assert "User management commands" in result.stdout

    def test_main_help(self):
        """Test main CLI help."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Memotic - FastAPI Memos CLI" in result.stdout

    @patch("memos_api.cli.asyncio.run")
    def test_command_exception_handling(self, mock_asyncio_run):
        """Test CLI command exception handling."""
        mock_asyncio_run.side_effect = Exception("Connection failed")

        result = self.runner.invoke(app, ["status"])
        assert result.exit_code == 0  # Commands handle exceptions gracefully
