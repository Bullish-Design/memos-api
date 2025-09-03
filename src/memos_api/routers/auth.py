"""
Authentication router implementation
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.user import User
from ..storage import UserStorage


class PasswordCredentials(BaseModel):
    """Password authentication credentials."""

    username: str
    password: str


class SSOCredentials(BaseModel):
    """SSO authentication credentials."""

    idp_id: str
    code: str
    redirect_uri: str


class CreateSessionRequest(BaseModel):
    """Create session request."""

    password_credentials: Optional[PasswordCredentials] = None
    sso_credentials: Optional[SSOCredentials] = None


class CreateSessionResponse(BaseModel):
    """Create session response."""

    user: User
    last_accessed_at: datetime


class GetCurrentSessionResponse(BaseModel):
    """Get current session response."""

    user: User
    last_accessed_at: datetime


class AuthRouter:
    """Authentication API router handler."""

    def __init__(self, storage: UserStorage) -> None:
        self.router = APIRouter()
        self.storage = storage
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure auth routes."""

        @self.router.post("/auth/signin", response_model=CreateSessionResponse)
        async def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
            """Create authentication session."""
            if request.password_credentials:
                session = self.storage.authenticate(
                    request.password_credentials.username,
                    request.password_credentials.password
                )
                if session:
                    return CreateSessionResponse(
                        user=session["user"],
                        last_accessed_at=session["last_accessed_at"]
                    )
                raise HTTPException(status_code=401, detail="Invalid credentials")

            if request.sso_credentials:
                raise HTTPException(status_code=501, detail="SSO not implemented in MVP")

            raise HTTPException(status_code=400, detail="No credentials provided")

        @self.router.get("/auth/status", response_model=GetCurrentSessionResponse)
        async def get_auth_status() -> GetCurrentSessionResponse:
            """Get current authentication status."""
            session = self.storage.get_current_session()
            if not session:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return GetCurrentSessionResponse(
                user=session["user"],
                last_accessed_at=session["last_accessed_at"]
            )

        @self.router.post("/auth/signout")
        async def sign_out() -> Dict[str, str]:
            """Sign out current session."""
            self.storage.clear_sessions()
            return {"message": "Signed out successfully"}
