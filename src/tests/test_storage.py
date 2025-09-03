"""
Tests for storage classes
"""

from __future__ import annotations

import pytest

from memos_api.models.memo import Attachment, Memo
from memos_api.models.user import User, UserAccessToken
from memos_api.storage import AppStorage


class TestMemoStorage:
    """Test memo storage functionality."""

    def test_create_memo(self, storage: AppStorage, sample_memo: Memo):
        """Test memo creation."""
        created = storage.memos.create(sample_memo)
        assert created.name == "memos/1"
        assert created.content == sample_memo.content

    def test_get_memo(self, storage: AppStorage, sample_memo: Memo):
        """Test memo retrieval."""
        created = storage.memos.create(sample_memo)
        retrieved = storage.memos.get("1")
        assert retrieved is not None
        assert retrieved.content == sample_memo.content

    def test_list_memos(self, storage: AppStorage, sample_memo: Memo):
        """Test memo listing."""
        storage.memos.create(sample_memo)
        memos = storage.memos.list()
        assert len(memos) == 1
        assert memos[0].content == sample_memo.content

    def test_list_memos_with_filter(self, storage: AppStorage):
        """Test memo listing with filter."""
        memo1 = Memo(content="Python programming", visibility="PRIVATE", state="NORMAL")
        memo2 = Memo(
            content="JavaScript tutorial", visibility="PRIVATE", state="NORMAL"
        )

        storage.memos.create(memo1)
        storage.memos.create(memo2)

        filtered = storage.memos.list("python")
        assert len(filtered) == 1
        assert "Python" in filtered[0].content

    def test_update_memo(self, storage: AppStorage, sample_memo: Memo):
        """Test memo update."""
        created = storage.memos.create(sample_memo)
        created.content = "Updated content"

        updated = storage.memos.update("1", created)
        assert updated is not None
        assert updated.content == "Updated content"

    def test_delete_memo(self, storage: AppStorage, sample_memo: Memo):
        """Test memo deletion."""
        storage.memos.create(sample_memo)
        success = storage.memos.delete("1")
        assert success is True
        assert storage.memos.get("1") is None


class TestUserStorage:
    """Test user storage functionality."""

    def test_create_user(self, storage: AppStorage, sample_user: User):
        """Test user creation."""
        created = storage.users.create(sample_user)
        assert created.name.startswith("users/")
        assert created.username == sample_user.username

        # Verify it's stored correctly
        user_id = created.name.split("/")[-1]
        retrieved = storage.users.get(user_id)
        assert retrieved is not None
        assert retrieved.username == sample_user.username

    def test_get_user(self, storage: AppStorage, sample_user: User):
        """Test user retrieval."""
        created = storage.users.create(sample_user)
        retrieved = storage.users.get("2")
        assert retrieved is not None
        assert retrieved.username == sample_user.username

    def test_list_users(self, storage: AppStorage):
        """Test user listing."""
        users = storage.users.list()
        assert len(users) == 1  # Mock user exists
        assert users[0].username == "admin"

    def test_search_users(self, storage: AppStorage, sample_user: User):
        """Test user search."""
        storage.users.create(sample_user)
        results = storage.users.search("test")
        assert len(results) == 1
        assert results[0].username == "testuser"

    def test_authenticate_valid(self, storage: AppStorage):
        """Test valid authentication."""
        session = storage.users.authenticate("admin", "password")
        assert session is not None
        assert session["user"].username == "admin"

    def test_authenticate_invalid(self, storage: AppStorage):
        """Test invalid authentication."""
        session = storage.users.authenticate("admin", "wrongpass")
        assert session is None

    def test_access_tokens(self, storage: AppStorage):
        """Test access token operations."""
        token = UserAccessToken(access_token="test-token-123")
        created = storage.users.create_access_token("1", token)

        assert created.name == "users/1/accessTokens/1"

        tokens = storage.users.list_access_tokens("1")
        assert len(tokens) == 1

        deleted = storage.users.delete_access_token("1")
        assert deleted is True


class TestAttachmentStorage:
    """Test attachment storage functionality."""

    def test_create_attachment(self, storage: AppStorage):
        """Test attachment creation."""
        attachment = Attachment(
            filename="test.txt", type="text/plain", content=b"test content", size=12
        )

        created = storage.attachments.create(attachment)
        assert created.name == "attachments/1"
        assert created.filename == "test.txt"

    def test_list_attachments_with_filter(self, storage: AppStorage):
        """Test attachment listing with filter."""
        att1 = Attachment(filename="document.pdf", type="application/pdf", size=1024)
        att2 = Attachment(filename="image.jpg", type="image/jpeg", size=2048)

        storage.attachments.create(att1)
        storage.attachments.create(att2)

        filtered = storage.attachments.list("pdf")
        assert len(filtered) == 1
        assert filtered[0].filename == "document.pdf"


class TestAppStorage:
    """Test unified app storage."""

    def test_storage_components(self, storage: AppStorage):
        """Test all storage components are available."""
        assert storage.memos is not None
        assert storage.users is not None
        assert storage.attachments is not None
        assert storage.activities is not None

    def test_reset(self, storage: AppStorage, sample_memo: Memo):
        """Test storage reset."""
        storage.memos.create(sample_memo)
        assert len(storage.memos.list()) == 1

        storage.reset()
        assert len(storage.memos.list()) == 0
        assert len(storage.users.list()) == 1  # Mock user recreated
