"""
Attachments router implementation
"""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile
from pydantic import BaseModel

from ..models.base import PaginatedResponse
from ..models.memo import Attachment
from ..storage import AttachmentStorage


class ListAttachmentsResponse(PaginatedResponse):
    """List attachments response."""

    attachments: list[Attachment] = []


class CreateAttachmentRequest(BaseModel):
    """Create attachment request."""

    attachment: Attachment


class AttachmentRouter:
    """Attachment API router handler."""

    def __init__(self, storage: AttachmentStorage) -> None:
        self.router = APIRouter()
        self.storage = storage
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure attachment routes."""

        @self.router.get("/attachments", response_model=ListAttachmentsResponse)
        async def list_attachments(
            page_size: Optional[int] = Query(None, ge=1, le=1000),
            page_token: Optional[str] = Query(None),
            filter: Optional[str] = Query(None),
        ) -> ListAttachmentsResponse:
            """List attachments."""
            attachments = self.storage.list(filter)
            return ListAttachmentsResponse(attachments=attachments)

        @self.router.post("/attachments", response_model=Attachment)
        async def create_attachment(request: CreateAttachmentRequest) -> Attachment:
            """Create a new attachment."""
            return self.storage.create(request.attachment)

        @self.router.post("/attachments/upload", response_model=Attachment)
        async def upload_attachment(file: UploadFile) -> Attachment:
            """Upload attachment file."""
            content = await file.read()
            attachment = Attachment(
                filename=file.filename or "unknown",
                type=file.content_type or "application/octet-stream",
                content=content,
                size=len(content),
            )
            return self.storage.create(attachment)

        @self.router.get("/attachments/{attachment_id}", response_model=Attachment)
        async def get_attachment(attachment_id: str) -> Attachment:
            """Get attachment by ID."""
            attachment = self.storage.get(attachment_id)
            if not attachment:
                raise HTTPException(status_code=404, detail="Attachment not found")
            return attachment

        @self.router.delete("/attachments/{attachment_id}")
        async def delete_attachment(attachment_id: str) -> Dict[str, str]:
            """Delete attachment by ID."""
            success = self.storage.delete(attachment_id)
            if not success:
                raise HTTPException(status_code=404, detail="Attachment not found")
            return {"message": "Attachment deleted successfully"}
