#!/usr/bin/env python3
"""Concurrent gateway stress plus tamper-evident audit verification.

Starts an isolated gateway, mixes catalog/policy/MCP/invoke traffic, then
rebuilds the hash chain. Exits non-zero on 5xx, broken evidence, or slow p95.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "gateway"
PORT = os.environ.get("STRESS_PORT", "8791")
BASE = f"http://127.0.0.1:{PORT}"
WORKERS = int(os.environ.get("STRESS_WORKERS", "12"))
PER_WORKER = int(os.environ.get("STRESS_PER_WORKER", "20"))
P95_BUDGET_MS = float(os.environ.get("STRESS_P95_MS", "1500"))


def request(method: str, path: str, body: dict | None = None, timeout: float = 10) -> tuple[int, dict | list | str, float]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"content-type": "application/json"} if data else {},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            elapsed = (time.perf_counter() - started) * 1000
            parsed: dict | list | str
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = raw
            return resp.status, parsed, elapsed
    except urllib.error.HTTPError as exc:
        elapsed = (time.perf_counter() - started) * 1000
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed, elapsed


def sha256_hex(data: str) -> str:
    import hashlib

    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def one_call(i: int) -> tuple[str, int, float]:
    kind = i % 6
    if kind == 0:
        status, _, ms = request("GET", "/healthz")
        return "healthz", status, ms
    if kind == 1:
        status, body, ms = request("GET", "/api/v1/connectors?operation=read&trustTier=3,4&sort=rank")
        if status == 200 and not isinstance(body, dict):
            return "catalog", 500, ms
        return "catalog", status, ms
    if kind == 2:
        status, body, ms = request(
            "POST",
            "/api/v1/policy/evaluate",
            {
                "actor": "user:stress",
                "connector_slug": "github-readonly",
                "tool_name": "get_pull_request",
                "arguments": {"number": i},
                "environment": "development",
            },
        )
        if status == 200 and isinstance(body, dict) and not body.get("correlation_id"):
            return "evaluate", 500, ms
        return "evaluate", status, ms
    if kind == 3:
        status, body, ms = request(
            "POST",
            "/mcp",
            {"jsonrpc": "2.0", "id": i, "method": "tools/list", "params": {}},
        )
        if status == 200 and isinstance(body, dict):
            tools = (body.get("result") or {}).get("tools") or []
            if len(tools) < 5:
                return "mcp-list", 500, ms
        return "mcp-list", status, ms
    if kind == 4:
        status, body, ms = request(
            "POST",
            "/mcp",
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "mcp__github-readonly__get_pull_request",
                    "arguments": {"number": i, "connector_url": "http://169.254.169.254/"},
                },
            },
        )
        if status != 200 or not isinstance(body, dict) or not body.get("result", {}).get("isError"):
            return "mcp-reject-url", 500, ms
        return "mcp-reject-url", status, ms
    status, body, ms = request(
        "POST",
        "/api/v1/gateway/invoke",
        {
            "actor": "user:stress",
            "connector_slug": "github-readonly",
            "tool_name": "get_pull_request",
            "arguments": {"number": i},
            "environment": "development",
        },
    )
    if status == 200 and isinstance(body, dict) and not body.get("correlation_id"):
        return "invoke", 500, ms
    return "invoke", status, ms


def verify_chain(events_newest_first: list[dict]) -> None:
    chronological = list(reversed(events_newest_first))
    prev = None
    for event in chronological:
        assert event.get("correlation_id"), event
        assert event.get("event_hash"), event
        without = {k: v for k, v in event.items() if k != "event_hash"}
        payload = json.dumps(without, sort_keys=True, separators=(",", ":"))
        digest = sha256_hex(payload)
        if digest != event["event_hash"]:
            raise SystemExit("audit hash mismatch — chain is not tamper-evident")
        if event.get("prev_event_hash") != prev:
            raise SystemExit("audit prev_event_hash broken under concurrency")
        prev = event["event_hash"]


def wait_healthy(proc: subprocess.Popen) -> None:
    for _ in range(40):
        if proc.poll() is not None:
            raise SystemExit(f"gateway exited early: {proc.returncode}")
        try:
            status, body, _ = request("GET", "/healthz", timeout=2)
            if status == 200 and isinstance(body, dict) and body.get("ok"):
                return
        except Exception:
            time.sleep(0.25)
            continue
        time.sleep(0.25)
    raise SystemExit("gateway did not become healthy")


def main() -> None:
    env = os.environ.copy()
    env["AUTH_MODE"] = "disabled"
    env["GITHUB_WRITE_DRY_RUN"] = "1"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--app-dir",
            str(GATEWAY),
            "--host",
            "127.0.0.1",
            "--port",
            PORT,
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    failures: list[str] = []
    latencies: list[float] = []
    try:
        wait_healthy(proc)
        total = WORKERS * PER_WORKER
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = [pool.submit(one_call, i) for i in range(total)]
            for fut in as_completed(futures):
                name, status, ms = fut.result()
                latencies.append(ms)
                if status >= 500:
                    failures.append(f"{name} -> {status}")
        # Write without a grant must stay an approval gate, not a 500.
        denied, _, _ = request(
            "POST",
            "/api/v1/gateway/invoke",
            {
                "actor": "user:stress",
                "connector_slug": "filesystem-sandbox",
                "tool_name": "write_artifact",
                "arguments": {"path": "out/x", "content": "no"},
                "environment": "development",
                "idempotency_key": "stress-deny",
            },
        )
        if denied != 401:
            failures.append(f"ungated write returned {denied}, expected 401")

        status, audit_body, _ = request("GET", "/api/v1/audit/events?limit=1000")
        if status != 200 or not isinstance(audit_body, dict):
            raise SystemExit(f"audit list failed: {status}")
        events = audit_body.get("events") or []
        if len(events) < 10:
            raise SystemExit(f"expected audit evidence, got {len(events)}")
        verify_chain(events)
        _, health, _ = request("GET", "/healthz")
        reported = int(health["audit_events"]) if isinstance(health, dict) else -1
        if reported != len(events) and reported > 1000:
            raise SystemExit("audit window truncated; lower stress volume")
        if reported != len(events):
            raise SystemExit(f"audit count mismatch healthz={reported} listed={len(events)}")

        latencies.sort()
        p95 = latencies[int(len(latencies) * 0.95)]
        if failures:
            raise SystemExit("stress failures: " + "; ".join(failures[:8]))
        if p95 > P95_BUDGET_MS:
            raise SystemExit(f"p95 {p95:.1f}ms exceeds {P95_BUDGET_MS}ms")
        print(
            json.dumps(
                {
                    "ok": True,
                    "requests": total,
                    "workers": WORKERS,
                    "p95_ms": round(p95, 1),
                    "max_ms": round(latencies[-1], 1),
                    "audit_events": len(events),
                    "chain": "verified",
                    "ungated_write": "approval_required",
                }
            )
        )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
