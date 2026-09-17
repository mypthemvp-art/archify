"""Append-only in-memory audit log with hash chaining (swap for Postgres later)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .security import sha256_hex


class AuditStore:
    def __init__(self):
        self.events: list[dict[str, Any]] = []
        self._prev_hash: str | None = None

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
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
        return record

    def list(self, *, limit: int = 100, correlation_id: str | None = None) -> list[dict[str, Any]]:
        items = self.events
        if correlation_id:
            items = [e for e in items if e.get("correlation_id") == correlation_id]
        return list(reversed(items[-limit:]))
