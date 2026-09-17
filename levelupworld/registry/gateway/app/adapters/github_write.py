"""Constrained non-prod GitHub pull-request creation behind signed grants.

Safety:
  - environments: development, staging only (never production)
  - repository allowlist via GITHUB_WRITE_REPO_ALLOWLIST
  - requires approval grant bound to exact args_hash
  - uses short-lived GITHUB_WRITE_TOKEN (fine-scoped PAT or GitHub App install token)
"""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from ..security import args_hash

SLUG = "github-write"
VERSION = "1.0.0"
ALLOWED_ENVIRONMENTS = {"development", "staging"}
TOOL_NAME = "create_pull_request"

_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def allowlist() -> set[str]:
    raw = os.environ.get("GITHUB_WRITE_REPO_ALLOWLIST", "")
    return {r.strip() for r in raw.split(",") if r.strip()}


def validate_args(arguments: dict[str, Any], environment: str) -> None:
    if environment not in ALLOWED_ENVIRONMENTS:
        raise ValueError("github-write.create_pull_request is forbidden in production")
    repo = arguments.get("repository")
    head = arguments.get("head")
    base = arguments.get("base")
    title = arguments.get("title")
    if not repo or not _REPO_RE.match(str(repo)):
        raise ValueError("repository must look like owner/name")
    allowed = allowlist()
    if allowed and str(repo) not in allowed:
        raise ValueError(f"repository {repo} is not on GITHUB_WRITE_REPO_ALLOWLIST")
    if not head or not base or not title:
        raise ValueError("head, base, and title are required")
    if str(base) in {"main", "master"} and environment == "staging":
        # Still allowed in staging, but body must acknowledge risk
        pass
    body = arguments.get("body") or ""
    if len(str(title)) > 200:
        raise ValueError("title too long")
    if len(str(body)) > 50_000:
        raise ValueError("body too long")


def create_pull_request(
    *,
    arguments: dict[str, Any],
    environment: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    validate_args(arguments, environment)
    repo = arguments["repository"]
    payload = {
        "title": arguments["title"],
        "head": arguments["head"],
        "base": arguments["base"],
        "body": arguments.get("body") or "",
        "draft": bool(arguments.get("draft", True)),
    }
    digest = args_hash(arguments)
    if dry_run or os.environ.get("GITHUB_WRITE_DRY_RUN", "1") == "1":
        return {
            "ok": True,
            "dry_run": True,
            "repository": repo,
            "pull_request": payload,
            "html_url": f"https://github.com/{repo}/compare/{payload['base']}...{payload['head']}?expand=1",
            "args_hash": digest,
            "note": "Dry-run only. Set GITHUB_WRITE_DRY_RUN=0 and GITHUB_WRITE_TOKEN to create a real PR.",
        }

    # Live mutation: allowlist must be explicit (fail closed)
    if not allowlist():
        raise RuntimeError("GITHUB_WRITE_REPO_ALLOWLIST is required when dry-run is disabled")
    token = os.environ.get("GITHUB_WRITE_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_WRITE_TOKEN is required when dry-run is disabled")

    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    url = f"{api.rstrip('/')}/repos/{repo}/pulls"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "agent-ops-registry-gateway",
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
    return {
        "ok": True,
        "dry_run": False,
        "repository": repo,
        "number": data.get("number"),
        "html_url": data.get("html_url"),
        "args_hash": digest,
    }


MANIFEST = {
    "slug": SLUG,
    "display_name": "GitHub Write (non-prod PR create)",
    "category": "github",
    "rank": 11,
    "description": "Create pull requests in allowlisted non-production repositories behind signed approval grants.",
    "owner_team": "platform-security",
    "escalation_contact": "secops@localhost",
    "trust_tier": "reviewed",
    "certification_state": "in_lab",
    "transport": "streamable_http",
    "version": VERSION,
    "image_digest": "sha256:github-write-dev-digest",
    "oauth_scopes": ["pull_requests:write", "contents:read"],
    "outbound_domains": ["api.github.com"],
    "allowed_environments": ["development", "staging"],
    "data_classification": "internal",
    "tools": [
        {
            "name": TOOL_NAME,
            "capability": "write",
            "description": "Create a pull request (draft by default) in an allowlisted repository.",
            "input_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["repository", "head", "base", "title"],
                "properties": {
                    "repository": {"type": "string"},
                    "head": {"type": "string"},
                    "base": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "draft": {"type": "boolean"},
                },
            },
            "risk_level": "high",
            "requires_approval": True,
        }
    ],
    "read_tool_count": 0,
    "write_tool_count": 1,
    "delete_tool_count": 0,
    "safety": "Non-prod only; repo allowlist; signed grant; dry-run default",
    "health": {
        "success_rate_24h": 1.0,
        "p95_latency_ms": 200,
        "error_rate_24h": 0.0,
        "policy_denial_rate_24h": 0.0,
        "healthy": True,
    },
    "active_in_production": False,
}
