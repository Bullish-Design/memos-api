# examples/basic_usage.py
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "memos-api @ https://github.com/Bullish-Design/memos-api.git"
# ]
# ///
"""
Basic usage examples for Memos API client
"""

from __future__ import annotations

import asyncio
from memos_api import (
    MemosClient,
    SyncMemosClient,
    MemosClientConfig,
    quick_memo_sync,
    quick_memo,
)


async def async_examples():
    """Demonstrate async client usage."""
    print("=== Async Client Examples ===")

    # Basic usage with context manager
    async with MemosClient() as client:
        # Create a memo
        memo = await client.create_memo(
            "My first memo!", visibility="PRIVATE", tags=["example", "test"]
        )
        print(f"Created memo: {memo.name}")

        # List all memos
        memos = await client.list_memos()
        print(f"Total memos: {len(memos)}")

        # Search memos
        filtered = await client.list_memos(filter_text="first")
        print(f"Filtered memos: {len(filtered)}")

        # Get specific memo
        memo_id = memo.name.split("/")[-1]
        retrieved = await client.get_memo(memo_id)
        print(f"Retrieved: {retrieved.content}")


def sync_examples():
    """Demonstrate sync client usage."""
    print("\n=== Sync Client Examples ===")

    # Custom configuration
    config = MemosClientConfig(base_url="http://localhost:5232", timeout=60.0)

    with SyncMemosClient(config) as client:
        # Create memo
        memo = client.create_memo("Sync memo example")
        print(f"Created sync memo: {memo.name}")

        # List memos
        memos = client.list_memos()
        print(f"Total memos (sync): {len(memos)}")

        # Create user
        user = client.create_user(username="newuser", email="newuser@example.com")
        print(f"Created user: {user.username}")


def convenience_examples():
    """Demonstrate convenience functions."""
    print("\n=== Convenience Functions ===")

    # Super simple memo creation
    memo = quick_memo_sync("Quick note from convenience function")
    print(f"Quick memo: {memo.content}")

    # Async version
    async def async_quick():
        memo = await quick_memo("Async quick note")
        print(f"Async quick memo: {memo.content}")

    asyncio.run(async_quick())


def error_handling_example():
    """Demonstrate error handling."""
    print("\n=== Error Handling ===")

    from memos_api import MemosNotFoundError, MemosConnectionError

    try:
        with SyncMemosClient() as client:
            # This will raise MemosNotFoundError
            client.get_memo("nonexistent")
    except MemosNotFoundError as e:
        print(f"Handled not found error: {e}")
    except MemosConnectionError as e:
        print(f"Connection error (expected if server not running): {e}")


if __name__ == "__main__":
    print("Memos API Client Examples")
    print("=" * 40)

    # Run examples (these will fail if server isn't running)
    try:
        asyncio.run(async_examples())
        sync_examples()
        convenience_examples()
    except Exception as e:
        print(f"Examples require running Memos server: {e}")

    error_handling_example()

