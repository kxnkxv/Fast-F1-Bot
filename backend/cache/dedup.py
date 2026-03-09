from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


_pending: dict[str, asyncio.Task[Any]] = {}


async def deduplicated_call(key: str, coro_factory: Callable[[], Awaitable[Any]]) -> Any:
    """Deduplicate concurrent calls with the same key.

    If multiple callers request the same key simultaneously,
    only one actual call is made. All callers receive the same result.
    """
    if key in _pending:
        return await _pending[key]

    task = asyncio.create_task(coro_factory())
    _pending[key] = task
    try:
        return await task
    finally:
        _pending.pop(key, None)
