import asyncio
import json
from typing import Any

class EventBroadcaster:
    """Manages SSE and WebSocket client event subscriptions for real-time run updates."""

    def __init__(self):
        # Map of run_id -> set of asyncio.Queue
        self._listeners: dict[str, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, run_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        async with self._lock:
            if run_id not in self._listeners:
                self._listeners[run_id] = set()
            self._listeners[run_id].add(queue)
        return queue

    async def unsubscribe(self, run_id: str, queue: asyncio.Queue):
        async with self._lock:
            if run_id in self._listeners:
                self._listeners[run_id].discard(queue)
                if not self._listeners[run_id]:
                    del self._listeners[run_id]

    async def broadcast(self, run_id: str, event_type: str, data: dict[str, Any]):
        payload = {
            "run_id": run_id,
            "event": event_type,
            "data": data
        }
        async with self._lock:
            queues = list(self._listeners.get(run_id, []))

        for q in queues:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass

broadcaster = EventBroadcaster()
