"""Concurrency check for the append-only audit hash chain."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.audit import AuditStore  # noqa: E402
from app.security import sha256_hex  # noqa: E402


def test_concurrent_audit_chain_holds():
    store = AuditStore()

    def worker(n: int) -> None:
        store.append({"correlation_id": f"c-{n}", "actor_id": "user:stress", "outcome": "ok"})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(40)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    events = list(reversed(store.list(limit=100)))
    assert len(events) == 40
    prev = None
    for event in events:
        body = {k: v for k, v in event.items() if k != "event_hash"}
        digest = sha256_hex(json.dumps(body, sort_keys=True, separators=(",", ":")))
        assert digest == event["event_hash"]
        assert event["prev_event_hash"] == prev
        prev = event["event_hash"]
