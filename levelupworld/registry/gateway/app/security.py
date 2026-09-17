"""Canonical argument hashing, redaction, budgets, and audit hash-chain helpers."""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from typing import Any


SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|password|private[_-]?key|secret|token|authorization|connection[_-]?string)\s*[:=]\s*['\"]?([^\s'\"]{6,})"
)
PII_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: canonicalize(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value


def args_hash(arguments: dict[str, Any]) -> str:
    payload = json.dumps(canonicalize(arguments), separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def redact_text(text: str) -> tuple[str, int]:
    count = 0

    def secret_sub(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}=***REDACTED***"

    text = SECRET_RE.sub(secret_sub, text)

    def email_sub(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return "***EMAIL***"

    text = PII_EMAIL_RE.sub(email_sub, text)
    return text, count


def redact_payload(payload: Any) -> tuple[Any, int]:
    count = 0

    def walk(value: Any) -> Any:
        nonlocal count
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, item in value.items():
                key_l = str(key).lower()
                if any(
                    s in key_l
                    for s in (
                        "password",
                        "secret",
                        "token",
                        "api_key",
                        "apikey",
                        "private_key",
                        "authorization",
                        "connection_string",
                    )
                ) and isinstance(item, str):
                    count += 1
                    out[key] = "***REDACTED***"
                else:
                    out[key] = walk(item)
            return out
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, str):
            text, n = redact_text(value)
            count += n
            return text
        return value

    return walk(payload), count


def new_correlation_id() -> str:
    return str(uuid.uuid4())


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class BudgetTracker:
    """In-memory per-run budget enforcement."""

    def __init__(self, max_tools: int = 20, max_duration_ms: int = 900_000, max_cost_micros: int = 5_000_000):
        self.max_tools = max_tools
        self.max_duration_ms = max_duration_ms
        self.max_cost_micros = max_cost_micros
        self.runs: dict[str, dict[str, Any]] = {}

    def begin(self, run_id: str | None) -> str:
        rid = run_id or str(uuid.uuid4())
        self.runs.setdefault(
            rid,
            {
                "tool_calls": 0,
                "cost_micros": 0,
                "started_ms": int(time.time() * 1000),
                "breached": False,
            },
        )
        return rid

    def charge(self, run_id: str, cost_micros: int = 0) -> tuple[bool, str]:
        state = self.runs[self.begin(run_id)]
        state["tool_calls"] += 1
        state["cost_micros"] += cost_micros
        elapsed = int(time.time() * 1000) - state["started_ms"]
        if state["tool_calls"] > self.max_tools:
            state["breached"] = True
            return False, f"tool-call budget exceeded ({self.max_tools})"
        if elapsed > self.max_duration_ms:
            state["breached"] = True
            return False, f"duration budget exceeded ({self.max_duration_ms}ms)"
        if state["cost_micros"] > self.max_cost_micros:
            state["breached"] = True
            return False, f"cost budget exceeded ({self.max_cost_micros} micros)"
        return True, "ok"
