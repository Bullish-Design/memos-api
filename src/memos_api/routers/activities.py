"""
Activities router implementation
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..models.base import PaginatedResponse, TimestampMixin
from ..storage import ActivityStorage


class ActivityMemoCommentPayload(BaseModel):
    """Activity memo comment payload."""

    memo: str
    related_memo: str


class ActivityPayload(BaseModel):
    """Activity payload union."""

    memo_comment: Optional[ActivityMemoCommentPayload] = None


class Activity(TimestampMixin):
    """Activity model."""

    name: Optional[str] = None
    creator: str
    type: str
    level: str
    payload: Optional[ActivityPayload] = None


class ListActivitiesResponse(PaginatedResponse):
    """List activities response."""

    activities: list[Activity] = []


class ActivityRouter:
    """Activity API router handler."""

    def __init__(self, storage: ActivityStorage) -> None:
        self.router = APIRouter()
        self.storage = storage
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure activity routes."""

        @self.router.get("/activities", response_model=ListActivitiesResponse)
        async def list_activities(
            page_size: Optional[int] = Query(None, ge=1, le=1000),
            page_token: Optional[str] = Query(None),
        ) -> ListActivitiesResponse:
            """List activities."""
            activities_data = self.storage.list_activities()
            activities = [Activity(**data) for data in activities_data]
            return ListActivitiesResponse(activities=activities)
