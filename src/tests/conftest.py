"""
Shared pytest fixtures for memos-api tests
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from memos_api.api import MemosAPI
from memos_api.models.memo import Memo
from memos_api.models.user import User
from memos_api.storage import AppStorage


@pytest.fixture
def storage() -> AppStorage:
    """Create fresh storage instance."""
    return AppStorage()


@pytest.fixture
def api_instance() -> MemosAPI:
    """Create fresh API instance."""
    return MemosAPI()


@pytest.fixture
def test_client(api_instance: MemosAPI) -> TestClient:
    """Create test client for API."""
    return TestClient(api_instance.app)


@pytest.fixture
def sample_memo() -> Memo:
    """Sample memo for testing."""
    return Memo(
        content="This is a test memo",
        visibility="PRIVATE",
        state="NORMAL"
    )


@pytest.fixture
def sample_user() -> User:
    """Sample user for testing."""
    return User(
        username="testuser",
        email="test@example.com",
        display_name="Test User"
    )
