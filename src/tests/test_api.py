"""
Tests for API endpoints
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from memos_api.models.memo import Memo
from memos_api.models.user import User


class TestMemoEndpoints:
    """Test memo API endpoints."""

    def test_list_memos_empty(self, test_client: TestClient):
        """Test listing memos when none exist."""
        response = test_client.get("/api/v1/memos")
        assert response.status_code == 200
        data = response.json()
        assert data["memos"] == []

    def test_create_memo(self, test_client: TestClient):
        """Test memo creation."""
        memo_data = {
            "memo": {
                "content": "Test memo content",
                "visibility": "PRIVATE",
                "state": "NORMAL",
            }
        }

        response = test_client.post("/api/v1/memos", json=memo_data)
        assert response.status_code == 200

        data = response.json()
        assert data["content"] == "Test memo content"
        assert data["name"] == "memos/1"

    def test_get_memo(self, test_client: TestClient):
        """Test memo retrieval."""
        # Create memo first
        memo_data = {
            "memo": {"content": "Test memo", "visibility": "PRIVATE", "state": "NORMAL"}
        }
        test_client.post("/api/v1/memos", json=memo_data)

        # Get memo
        response = test_client.get("/api/v1/memos/1")
        assert response.status_code == 200

        data = response.json()
        assert data["content"] == "Test memo"

    def test_get_nonexistent_memo(self, test_client: TestClient):
        """Test getting non-existent memo."""
        response = test_client.get("/api/v1/memos/999")
        assert response.status_code == 404

    def test_update_memo(self, test_client: TestClient):
        """Test memo update."""
        # Create memo
        memo_data = {
            "memo": {
                "content": "Original content",
                "visibility": "PRIVATE",
                "state": "NORMAL",
            }
        }
        test_client.post("/api/v1/memos", json=memo_data)

        # Update memo
        update_data = {
            "memo": {
                "content": "Updated content",
                "visibility": "PRIVATE",
                "state": "NORMAL",
            }
        }

        response = test_client.patch("/api/v1/memos/1", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["content"] == "Updated content"

    def test_delete_memo(self, test_client: TestClient):
        """Test memo deletion."""
        # Create memo
        memo_data = {
            "memo": {
                "content": "To be deleted",
                "visibility": "PRIVATE",
                "state": "NORMAL",
            }
        }
        test_client.post("/api/v1/memos", json=memo_data)

        # Delete memo
        response = test_client.delete("/api/v1/memos/1")
        assert response.status_code == 200

        # Verify deletion
        get_response = test_client.get("/api/v1/memos/1")
        assert get_response.status_code == 404

    def test_list_memos_with_filter(self, test_client: TestClient):
        """Test memo listing with filter."""
        # Create memos
        memo1_data = {
            "memo": {
                "content": "Python tutorial",
                "visibility": "PRIVATE",
                "state": "NORMAL",
            }
        }
        memo2_data = {
            "memo": {
                "content": "JavaScript guide",
                "visibility": "PRIVATE",
                "state": "NORMAL",
            }
        }

        test_client.post("/api/v1/memos", json=memo1_data)
        test_client.post("/api/v1/memos", json=memo2_data)

        # Filter memos
        response = test_client.get("/api/v1/memos?filter=python")
        assert response.status_code == 200

        data = response.json()
        assert len(data["memos"]) == 1
        assert "Python" in data["memos"][0]["content"]


class TestUserEndpoints:
    """Test user API endpoints."""

    def test_list_users(self, test_client: TestClient):
        """Test listing users."""
        response = test_client.get("/api/v1/users")
        assert response.status_code == 200

        data = response.json()
        assert len(data["users"]) == 1  # Mock user exists
        assert data["users"][0]["username"] == "admin"

    def test_create_user(self, test_client: TestClient):
        """Test user creation."""
        user_data = {
            "user": {
                "username": "newuser",
                "email": "new@example.com",
                "displayName": "New User",
            }
        }

        response = test_client.post("/api/v1/users", json=user_data)
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == "newuser"
        assert data["name"].startswith("users/")  # More flexible ID checking

    def test_get_user(self, test_client: TestClient):
        """Test user retrieval."""
        response = test_client.get("/api/v1/users/1")  # Mock user
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == "admin"

    def test_search_users(self, test_client: TestClient):
        """Test user search."""
        response = test_client.get("/api/v1/users:search?query=admin")
        assert response.status_code == 200

        data = response.json()
        assert len(data["users"]) == 1
        assert data["users"][0]["username"] == "admin"


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_signin_valid(self, test_client: TestClient):
        """Test valid signin."""
        auth_data = {
            "password_credentials": {"username": "admin", "password": "password"}
        }

        response = test_client.post("/api/v1/auth/signin", json=auth_data)
        assert response.status_code == 200

        data = response.json()
        assert data["user"]["username"] == "admin"
        assert "last_accessed_at" in data

    def test_signin_invalid(self, test_client: TestClient):
        """Test invalid signin."""
        auth_data = {
            "password_credentials": {"username": "admin", "password": "wrongpass"}
        }

        response = test_client.post("/api/v1/auth/signin", json=auth_data)
        assert response.status_code == 401

    def test_signout(self, test_client: TestClient):
        """Test signout."""
        response = test_client.post("/api/v1/auth/signout")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Signed out successfully"


class TestAttachmentEndpoints:
    """Test attachment API endpoints."""

    def test_list_attachments(self, test_client: TestClient):
        """Test listing attachments."""
        response = test_client.get("/api/v1/attachments")
        assert response.status_code == 200

        data = response.json()
        assert data["attachments"] == []

    def test_create_attachment(self, test_client: TestClient):
        """Test attachment creation."""
        attachment_data = {
            "attachment": {"filename": "test.txt", "type": "text/plain", "size": 12}
        }

        response = test_client.post("/api/v1/attachments", json=attachment_data)
        assert response.status_code == 200

        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["name"] == "attachments/1"


class TestActivityEndpoints:
    """Test activity API endpoints."""

    def test_list_activities(self, test_client: TestClient):
        """Test listing activities."""
        response = test_client.get("/api/v1/activities")
        assert response.status_code == 200

        data = response.json()
        assert data["activities"] == []
