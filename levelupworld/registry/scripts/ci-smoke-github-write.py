#!/usr/bin/env python3
"""CI smoke: certification suite + approval-bound github-write PR create (dry-run)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8787"
ARGS = {
    "repository": "acme/agent-platform",
    "head": "ci/demo",
    "base": "main",
    "title": "ci demo",
    "draft": True,
}


def post(url: str, body: dict | None = None) -> dict:
    payload = json.dumps(body if body is not None else {}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise SystemExit(f"HTTP {exc.code} {url}: {detail}") from exc


def main() -> None:
    health = json.loads(urllib.request.urlopen(f"{BASE}/healthz", timeout=10).read().decode())
    assert health.get("ok") is True, health
    print(f"healthz ok auth_mode={health.get('auth_mode')} connectors={health.get('connectors')}")

    run = post(f"{BASE}/api/v1/connectors/github-readonly/versions/1.0.0/test-runs?suite=full")
    assert run.get("status") == "passed", run
    print("sandbox certification suite passed")

    apr = post(
        f"{BASE}/api/v1/approvals",
        {
            "actor": "user:ci",
            "environment": "staging",
            "connector_slug": "github-write",
            "connector_version": "1.0.0",
            "tool_name": "create_pull_request",
            "plan_markdown": "CI dry-run PR",
            "arguments": ARGS,
            "idempotency_key": "ci-pr-1",
            "correlation_id": "00000000-0000-0000-0000-0000000000c1",
        },
    )
    decided = post(
        f"{BASE}/api/v1/approvals/{apr['id']}/decide",
        {"approver": "user:ci-approver", "approve": True},
    )
    token = decided["grant_token"]
    invoked = post(
        f"{BASE}/api/v1/gateway/invoke",
        {
            "actor": "user:ci",
            "tenant_id": "tenant_local",
            "project_id": "project_local",
            "environment": "staging",
            "connector_slug": "github-write",
            "tool_name": "create_pull_request",
            "arguments": ARGS,
            "idempotency_key": "ci-pr-1",
            "approval_grant": token,
        },
    )
    assert invoked["result"]["ok"] is True, invoked
    assert invoked["result"]["dry_run"] is True, invoked
    print("github-write dry-run mutation path passed")


if __name__ == "__main__":
    main()
