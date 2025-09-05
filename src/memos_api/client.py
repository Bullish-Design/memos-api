# src/memos_api/client.py
# src/memos_api/client_fixed.py
"""
Fixed client implementation without tenacity issues
"""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx

from .config import MemosClientConfig, MemosConnectionInfo
from .exceptions import (
    MemosConnectionError,
    MemosAuthenticationError,
    MemosNotFoundError,
    MemosValidationError,
    MemosAPIError,
)
from .models.memo import Memo, CreateMemoRequest, UpdateMemoRequest
from .models.user import User, CreateUserRequest, UpdateUserRequest


class MemosClient:
    """High-level async Memos API client."""

    def __init__(self, config: Optional[MemosClientConfig] = None) -> None:
        self.config = config or MemosClientConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self.connection_info = MemosConnectionInfo(base_url=self.config.base_url)

    async def __aenter__(self) -> MemosClient:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection to Memos API."""
        headers = {"Content-Type": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        self._client = httpx.AsyncClient(
            base_url=self.config.base_url, headers=headers, timeout=self.config.timeout
        )

        try:
            is_healthy = await self.health_check()
            if not is_healthy:
                raise MemosConnectionError(
                    f"Health check failed for {self.config.base_url}"
                )
            self.connection_info.connected = True
        except MemosConnectionError:
            raise
        except Exception as e:
            self.connection_info.last_error = str(e)
            await self.disconnect()
            raise MemosConnectionError(
                f"Failed to connect to {self.config.base_url}: {e}"
            )

    async def disconnect(self) -> None:
        """Close connection to Memos API."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self.connection_info.connected = False

    async def health_check(self) -> bool:
        """Check if API server is healthy."""
        if not self._client:
            return False

        try:
            response = await self._client.get("/docs")
            return response.status_code == 200
        except Exception:
            return False

    def _extract_resource_info(self, endpoint: str) -> tuple[str, str]:
        """Extract resource type and ID from endpoint."""
        parts = endpoint.strip("/").split("/")
        resource = ""
        resource_id = ""

        if len(parts) >= 3 and parts[1] == "v1":
            resource = parts[2].rstrip("s")  # users -> user, memos -> memo
            if len(parts) >= 4:
                resource_id = parts[3]

        return resource, resource_id

    def _handle_response_error(self, response: httpx.Response, endpoint: str) -> None:
        """Handle HTTP response errors with proper exception types."""
        resource, resource_id = self._extract_resource_info(endpoint)

        if response.status_code == 401:
            raise MemosAuthenticationError()
        elif response.status_code == 404 and resource:
            raise MemosNotFoundError(resource, resource_id)
        elif response.status_code == 400:
            try:
                detail = response.json().get("detail", "Validation failed")
            except Exception:
                detail = "Validation failed"
            raise MemosValidationError(detail)
        elif 500 <= response.status_code < 600:
            raise MemosAPIError(f"Server error: {response.text}", response.status_code)
        else:
            raise MemosAPIError(
                f"HTTP {response.status_code}: {response.text}", response.status_code
            )

    async def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make HTTP request with manual retry logic."""
        if not self._client:
            raise MemosConnectionError("Client not connected")

        last_exception = None

        for attempt in range(max(1, self.config.retries)):
            try:
                response = await self._client.request(method, endpoint, **kwargs)

                if not response.is_success:
                    self._handle_response_error(response, endpoint)

                return response

            except (MemosAuthenticationError, MemosNotFoundError, MemosValidationError):
                # Don't retry these errors - raise immediately
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.config.retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = min(4 * (2**attempt), 10)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed
                    raise

        if last_exception:
            raise last_exception

    # Memo Operations
    async def create_memo(
        self, content: str, visibility: str = "PRIVATE", **kwargs
    ) -> Memo:
        """Create a new memo."""
        memo_data = {"content": content, "visibility": visibility, "state": "NORMAL"}
        memo_data.update(kwargs)

        request = CreateMemoRequest(memo=Memo(**memo_data))
        response = await self._request(
            "POST", "/api/v1/memos", json=request.model_dump(by_alias=True)
        )
        return Memo(**response.json())

    async def get_memo(self, memo_id: str) -> Memo:
        """Get memo by ID."""
        response = await self._request("GET", f"/api/v1/memos/{memo_id}")
        return Memo(**response.json())

    async def list_memos(
        self, filter_text: Optional[str] = None, page_size: Optional[int] = None
    ) -> list[Memo]:
        """List all memos with optional filtering."""
        params = {}
        if filter_text:
            params["filter"] = filter_text
        if page_size:
            params["page_size"] = page_size

        response = await self._request("GET", "/api/v1/memos", params=params)
        data = response.json()
        return [Memo(**memo) for memo in data.get("memos", [])]

    async def update_memo(self, memo_id: str, memo: Memo) -> Memo:
        """Update existing memo."""
        request = UpdateMemoRequest(memo=memo)
        response = await self._request(
            "PATCH", f"/api/v1/memos/{memo_id}", json=request.model_dump(by_alias=True)
        )
        return Memo(**response.json())

    async def delete_memo(self, memo_id: str) -> bool:
        """Delete memo by ID."""
        await self._request("DELETE", f"/api/v1/memos/{memo_id}")
        return True

    # User Operations
    async def create_user(
        self, username: str, email: Optional[str] = None, **kwargs
    ) -> User:
        """Create a new user."""
        user_data = {"username": username, "role": "USER"}
        user_data.update(kwargs)

        if email:
            user_data["email"] = email
            user_data["displayName"] = user_data.get("displayName", username.title())

        request = CreateUserRequest(user=User(**user_data))
        response = await self._request(
            "POST",
            "/api/v1/users",
            json={"user": request.user.model_dump(by_alias=True)},
        )
        return User(**response.json())

    async def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        response = await self._request("GET", f"/api/v1/users/{user_id}")
        return User(**response.json())

    async def list_users(self) -> list[User]:
        """List all users."""
        response = await self._request("GET", "/api/v1/users")
        data = response.json()
        return [User(**user) for user in data.get("users", [])]

    async def update_user(self, user_id: str, user: User) -> User:
        """Update existing user."""
        request = UpdateUserRequest(user=user)
        response = await self._request(
            "PATCH", f"/api/v1/users/{user_id}", json=request.model_dump(by_alias=True)
        )
        return User(**response.json())

    async def delete_user(self, user_id: str) -> bool:
        """Delete user by ID."""
        await self._request("DELETE", f"/api/v1/users/{user_id}")
        return True


class SyncMemosClient:
    """Synchronous wrapper for MemosClient."""

    def __init__(self, config: Optional[MemosClientConfig] = None) -> None:
        self.config = config or MemosClientConfig()
        self._async_client = MemosClient(config)

    def __enter__(self) -> SyncMemosClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def _run_async(self, coro):
        """Run async operation in sync context."""

        async def _wrapped():
            async with self._async_client as client:
                return await coro(client)

        return asyncio.run(_wrapped())

    def create_memo(self, content: str, **kwargs) -> Memo:
        return self._run_async(lambda client: client.create_memo(content, **kwargs))

    def get_memo(self, memo_id: str) -> Memo:
        return self._run_async(lambda client: client.get_memo(memo_id))

    def list_memos(self, filter_text: Optional[str] = None) -> list[Memo]:
        return self._run_async(lambda client: client.list_memos(filter_text))

    def update_memo(self, memo_id: str, memo: Memo) -> Memo:
        return self._run_async(lambda client: client.update_memo(memo_id, memo))

    def delete_memo(self, memo_id: str) -> bool:
        return self._run_async(lambda client: client.delete_memo(memo_id))

    def create_user(self, username: str, **kwargs) -> User:
        return self._run_async(lambda client: client.create_user(username, **kwargs))

    def get_user(self, user_id: str) -> User:
        return self._run_async(lambda client: client.get_user(user_id))

    def list_users(self) -> list[User]:
        return self._run_async(lambda client: client.list_users())


# Convenience functions
async def quick_memo(
    content: str, base_url: str = "http://localhost:5232", token: Optional[str] = None
) -> Memo:
    """Quick memo creation."""
    config = MemosClientConfig(base_url=base_url, token=token)
    async with MemosClient(config) as client:
        return await client.create_memo(content)


def quick_memo_sync(
    content: str, base_url: str = "http://localhost:5232", token: Optional[str] = None
) -> Memo:
    """Quick memo creation (sync)."""
    return asyncio.run(quick_memo(content, base_url, token))

