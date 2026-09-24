"""Append-only audit log with hash chaining; dual-writes to Postgres when DATABASE_URL is set."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any

from .persist import persistence
from .security import sha256_hex


class AuditStore:
    def __init__(self, store=None):
        self._persist = store if store is not None else persistence
        self.events: list[dict[str, Any]] = []
        self._prev_hash: str | None = None
        self._lock = threading.Lock()

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            record = {
                **event,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "prev_event_hash": self._prev_hash,
            }
            payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
            event_hash = sha256_hex(payload)
            record["event_hash"] = event_hash
            self.events.append(record)
            self._prev_hash = event_hash
        # Dual-write outside the lock so DB latency does not stall concurrent appends.
        try:
            self._persist.insert_audit_event(record)
        except Exception as exc:  # noqa: BLE001
            record = {**record, "persist_error": str(exc)}
        return record

    def list(self, *, limit: int = 100, correlation_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self.events)
        if correlation_id:
            items = [e for e in items if e.get("correlation_id") == correlation_id]
        return list(reversed(items[-limit:]))
