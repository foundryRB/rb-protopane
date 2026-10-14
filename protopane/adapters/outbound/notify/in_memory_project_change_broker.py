from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

_Subscriber = tuple[asyncio.AbstractEventLoop, asyncio.Queue[str]]


class InMemoryProjectChangeBroker:
    """In-process fan-out of project-change events to live SSE subscribers.

    Implements the ProjectChangeNotifier port (publish) and hands out per-subscriber
    async queues the HTTP layer consumes. publish() runs in the request threadpool
    (save routes are sync); delivery hops to each subscriber's event loop via
    call_soon_threadsafe, so it is safe across the thread boundary.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: set[_Subscriber] = set()

    def publish(self, slug: str) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for entry in subscribers:
            loop, queue = entry
            try:
                loop.call_soon_threadsafe(queue.put_nowait, slug)
            except RuntimeError:
                # The subscriber's loop is shutting down; drop it.
                with self._lock:
                    self._subscribers.discard(entry)

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[str]]:
        """Yield a queue that receives every published slug for the caller's lifetime."""
        entry: _Subscriber = (asyncio.get_running_loop(), asyncio.Queue())
        with self._lock:
            self._subscribers.add(entry)
        try:
            yield entry[1]
        finally:
            with self._lock:
                self._subscribers.discard(entry)
