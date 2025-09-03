"""
User router implementation
"""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from ..models.user import (
    CreateUserAccessTokenRequest,
    CreateUserRequest,
    ListAllUserStatsResponse,
    ListUserAccessTokensResponse,
    ListUsersResponse,
    SearchUsersResponse,
    UpdateUserRequest,
    User,
    UserAccessToken,
)
from ..storage import UserStorage


class UserRouter:
    """User API router handler."""

    def __init__(self, storage: UserStorage) -> None:
        self.router = APIRouter()
        self.storage = storage
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure user routes."""

        @self.router.get("/users", response_model=ListUsersResponse)
        async def list_users(
            page_size: Optional[int] = Query(None, ge=1, le=1000),
            page_token: Optional[str] = Query(None),
        ) -> ListUsersResponse:
            """List users."""
            users = self.storage.list()
            return ListUsersResponse(users=users)

        @self.router.post("/users", response_model=User)
        async def create_user(request: CreateUserRequest) -> User:
            """Create a new user."""
            return self.storage.create(request.user, request.user_id)

        @self.router.get("/users/{user_id}", response_model=User)
        async def get_user(user_id: str) -> User:
            """Get user by ID."""
            user = self.storage.get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user

        @self.router.patch("/users/{user_id}", response_model=User)
        async def update_user(user_id: str, request: UpdateUserRequest) -> User:
            """Update existing user."""
            user = self.storage.update(user_id, request.user)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user

        @self.router.delete("/users/{user_id}")
        async def delete_user(user_id: str) -> Dict[str, str]:
            """Delete user by ID."""
            success = self.storage.delete(user_id)
            if not success:
                raise HTTPException(status_code=404, detail="User not found")
            return {"message": "User deleted successfully"}

        @self.router.get("/users:search", response_model=SearchUsersResponse)
        async def search_users(
            query: str = Query(..., description="Search query"),
            page_size: Optional[int] = Query(None, ge=1, le=1000),
            page_token: Optional[str] = Query(None),
        ) -> SearchUsersResponse:
            """Search users."""
            users = self.storage.search(query)
            return SearchUsersResponse(users=users)

        @self.router.get("/users:stats", response_model=ListAllUserStatsResponse)
        async def list_all_user_stats(
            page_size: Optional[int] = Query(None, ge=1, le=1000),
            page_token: Optional[str] = Query(None),
        ) -> ListAllUserStatsResponse:
            """List all user statistics."""
            stats = self.storage.get_user_stats()
            return ListAllUserStatsResponse(stats=stats)

        @self.router.get("/users/{user_id}/accessTokens", response_model=ListUserAccessTokensResponse)
        async def list_user_access_tokens(
            user_id: str,
            page_size: Optional[int] = Query(None, ge=1, le=1000),
            page_token: Optional[str] = Query(None),
        ) -> ListUserAccessTokensResponse:
            """List user access tokens."""
            tokens = self.storage.list_access_tokens(user_id)
            return ListUserAccessTokensResponse(access_tokens=tokens)

        @self.router.post("/users/{user_id}/accessTokens", response_model=UserAccessToken)
        async def create_user_access_token(
            user_id: str, request: CreateUserAccessTokenRequest
        ) -> UserAccessToken:
            """Create user access token."""
            if not self.storage.get(user_id):
                raise HTTPException(status_code=404, detail="User not found")

            return self.storage.create_access_token(user_id, request.access_token, request.access_token_id)

        @self.router.delete("/users/{user_id}/accessTokens/{token_id}")
        async def delete_user_access_token(user_id: str, token_id: str) -> Dict[str, str]:
            """Delete user access token."""
            success = self.storage.delete_access_token(token_id)
            if not success:
                raise HTTPException(status_code=404, detail="Access token not found")
            return {"message": "Access token deleted successfully"}
