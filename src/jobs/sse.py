"""Server-Sent Events (SSE) broadcaster for streaming job updates to frontend."""

from __future__ import annotations
import asyncio
import json
from typing import Dict, Set, Any, AsyncGenerator


class SSEBroadcaster:
    """Manages active SSE client connections and event dispatching."""

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._global_subscribers: Set[asyncio.Queue] = set()
        self._history: Dict[str, List[str]] = {}

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        q: asyncio.Queue = asyncio.Queue()
        if channel not in self._subscribers:
            self._subscribers[channel] = set()
        self._subscribers[channel].add(q)

        # Replay past events on this channel to avoid race conditions
        if channel in self._history:
            for past_msg in list(self._history[channel]):
                yield f"data: {past_msg}\n\n"

        try:
            while True:
                msg = await q.get()
                yield f"data: {msg}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if channel in self._subscribers:
                self._subscribers[channel].discard(q)

    async def subscribe_global(self) -> AsyncGenerator[str, None]:
        q: asyncio.Queue = asyncio.Queue()
        self._global_subscribers.add(q)
        try:
            while True:
                msg = await q.get()
                yield f"data: {msg}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self._global_subscribers.discard(q)

    async def publish(self, channel: str, data: Dict[str, Any]) -> None:
        payload = json.dumps(data)
        if channel not in self._history:
            self._history[channel] = []
        self._history[channel].append(payload)

        # Cap channel history to prevent unbounded memory growth
        if len(self._history[channel]) > 250:
            self._history[channel] = self._history[channel][-250:]

        # Notify channel subscribers
        if channel in self._subscribers:
            for q in list(self._subscribers[channel]):
                await q.put(payload)
        # Notify global stream
        for q in list(self._global_subscribers):
            await q.put(payload)


broadcaster = SSEBroadcaster()
