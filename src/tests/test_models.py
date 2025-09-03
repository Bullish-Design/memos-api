"""
Tests for model validation
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from memos_api.models.memo import Memo, Attachment, MemoRelation, Reaction
from memos_api.models.user import User, UserAccessToken
from memos_api.models.base import State, Visibility, UserRole


class TestMemoModel:
    """Test memo model validation."""

    def test_memo_creation_valid(self):
        """Test valid memo creation."""
        memo = Memo(
            content="Test memo content",
            visibility=Visibility.PRIVATE,
            state=State.NORMAL
        )
        assert memo.content == "Test memo content"
        assert memo.visibility == Visibility.PRIVATE
        assert memo.state == State.NORMAL

    def test_memo_required_content(self):
        """Test memo requires content."""
        with pytest.raises(ValidationError):
            Memo()

    def test_memo_defaults(self):
        """Test memo default values."""
        memo = Memo(content="Test")
        assert memo.visibility == Visibility.PRIVATE
        assert memo.state == State.NORMAL
        assert memo.pinned is False
        assert memo.tags is None

    def test_memo_with_tags(self):
        """Test memo with tags."""
        memo = Memo(
            content="Tagged memo",
            tags=["work", "urgent"]
        )
        assert memo.tags == ["work", "urgent"]


class TestUserModel:
    """Test user model validation."""

    def test_user_creation_valid(self):
        """Test valid user creation."""
        user = User(
            username="testuser",
            email="test@example.com",
            display_name="Test User"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"

    def test_user_required_username(self):
        """Test user requires username."""
        with pytest.raises(ValidationError):
            User()

    def test_user_defaults(self):
        """Test user default values."""
        user = User(username="test")
        assert user.role == UserRole.USER
        assert user.state == State.NORMAL
        assert user.email is None


class TestAttachmentModel:
    """Test attachment model validation."""

    def test_attachment_creation_valid(self):
        """Test valid attachment creation."""
        attachment = Attachment(
            filename="test.txt",
            type="text/plain",
            size=100
        )
        assert attachment.filename == "test.txt"
        assert attachment.type == "text/plain"
        assert attachment.size == 100

    def test_attachment_required_fields(self):
        """Test attachment required fields."""
        with pytest.raises(ValidationError):
            Attachment()

    def test_attachment_with_content(self):
        """Test attachment with binary content."""
        attachment = Attachment(
            filename="test.bin",
            type="application/octet-stream",
            content=b"binary data",
            size=11
        )
        assert attachment.content == b"binary data"


class TestReactionModel:
    """Test reaction model validation."""

    def test_reaction_creation_valid(self):
        """Test valid reaction creation."""
        reaction = Reaction(
            creator="users/1",
            content_type="EMOJI",
            content="👍"
        )
        assert reaction.creator == "users/1"
        assert reaction.content_type == "EMOJI"
        assert reaction.content == "👍"

    def test_reaction_required_fields(self):
        """Test reaction required fields."""
        with pytest.raises(ValidationError):
            Reaction()


class TestUserAccessTokenModel:
    """Test user access token validation."""

    def test_token_creation_valid(self):
        """Test valid token creation."""
        token = UserAccessToken(
            access_token="abc123",
            description="Test token"
        )
        assert token.access_token == "abc123"
        assert token.description == "Test token"

    def test_token_required_access_token(self):
        """Test token requires access_token."""
        with pytest.raises(ValidationError):
            UserAccessToken()


class TestEnums:
    """Test enum values."""

    def test_state_enum(self):
        """Test State enum values."""
        assert State.NORMAL == "NORMAL"
        assert State.ARCHIVED == "ARCHIVED"

    def test_visibility_enum(self):
        """Test Visibility enum values."""
        assert Visibility.PRIVATE == "PRIVATE"
        assert Visibility.PUBLIC == "PUBLIC"
        assert Visibility.PROTECTED == "PROTECTED"

    def test_user_role_enum(self):
        """Test UserRole enum values."""
        assert UserRole.USER == "USER"
        assert UserRole.ADMIN == "ADMIN"
        assert UserRole.HOST == "HOST"


class TestModelSerialization:
    """Test model serialization/deserialization."""

    def test_memo_dict_conversion(self):
        """Test memo to/from dict conversion."""
        memo_data = {
            "content": "Test memo",
            "visibility": "PRIVATE",
            "state": "NORMAL",
            "pinned": True
        }
        
        memo = Memo(**memo_data)
        serialized = memo.model_dump()
        
        assert serialized["content"] == "Test memo"
        assert serialized["pinned"] is True

    def test_user_dict_conversion(self):
        """Test user to/from dict conversion."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "role": "USER"
        }
        
        user = User(**user_data)
        serialized = user.model_dump()
        
        assert serialized["username"] == "testuser"
        assert serialized["role"] == "USER"
