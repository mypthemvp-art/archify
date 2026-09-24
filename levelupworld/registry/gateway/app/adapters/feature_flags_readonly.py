"""Sandboxed read-only feature flag discovery.

Safety:
  - environments: development, staging only while trust_tier=sandboxed
  - project allowlist via FEATURE_FLAGS_PROJECT_ALLOWLIST (empty = demo fixture only)
  - no mutate/toggle/rollout tools
  - returns fixture data unless FEATURE_FLAGS_LIVE=1 (still allowlisted)
"""

from __future__ import annotations

import os
import re
from typing import Any

SLUG = "feature-flags-readonly"
VERSION = "1.0.0"
ALLOWED_ENVIRONMENTS = {"development", "staging"}
READ_TOOLS = {"list_flags", "get_flag", "get_evaluation_rules"}

_FLAG_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

_FIXTURE_FLAGS = [
    {
        "key": "secure-pr-guardian",
        "name": "Secure PR Guardian",
        "kind": "boolean",
        "archived": False,
        "tags": ["security", "pilot"],
    },
    {
        "key": "triage-copilot-beta",
        "name": "Triage Copilot Beta",
        "kind": "boolean",
        "archived": False,
        "tags": ["ops", "pilot"],
    },
    {
        "key": "registry-catalog-v2",
        "name": "Registry Catalog V2",
        "kind": "boolean",
        "archived": False,
        "tags": ["platform"],
    },
]


def project_allowlist() -> set[str]:
    raw = os.environ.get("FEATURE_FLAGS_PROJECT_ALLOWLIST", "agent-platform,demo")
    return {p.strip() for p in raw.split(",") if p.strip()}


def validate_args(tool_name: str, arguments: dict[str, Any], environment: str) -> str:
    if environment not in ALLOWED_ENVIRONMENTS:
        raise ValueError(f"{SLUG} is forbidden in production while sandboxed")
    if tool_name not in READ_TOOLS:
        raise ValueError(f"unknown or non-read tool for {SLUG}: {tool_name}")

    project = str(arguments.get("project") or "agent-platform")
    if not _PROJECT_RE.match(project):
        raise ValueError("invalid project id")
    allowed = project_allowlist()
    if allowed and project not in allowed:
        raise ValueError(f"project '{project}' not on FEATURE_FLAGS_PROJECT_ALLOWLIST")

    if tool_name in {"get_flag", "get_evaluation_rules"}:
        flag_key = arguments.get("flag_key")
        if not flag_key or not _FLAG_KEY_RE.match(str(flag_key)):
            raise ValueError("flag_key is required and must be a safe identifier")
    return project


def invoke(tool_name: str, arguments: dict[str, Any], environment: str) -> dict[str, Any]:
    project = validate_args(tool_name, arguments, environment)
    env_name = str(arguments.get("environment") or environment)
    q = str(arguments.get("q") or "").lower()

    if tool_name == "list_flags":
        flags = [f for f in _FIXTURE_FLAGS if not q or q in f["key"] or q in f["name"].lower()]
        return {
            "ok": True,
            "connector": SLUG,
            "tool": tool_name,
            "project": project,
            "environment": env_name,
            "flags": flags,
            "count": len(flags),
            "note": "sandboxed fixture — live provider disabled by default",
        }

    flag_key = str(arguments["flag_key"])
    flag = next((f for f in _FIXTURE_FLAGS if f["key"] == flag_key), None)
    if tool_name == "get_flag":
        if not flag:
            return {
                "ok": False,
                "connector": SLUG,
                "tool": tool_name,
                "project": project,
                "flag_key": flag_key,
                "error": "flag_not_found",
            }
        return {
            "ok": True,
            "connector": SLUG,
            "tool": tool_name,
            "project": project,
            "environment": env_name,
            "flag": {**flag, "description": f"Fixture definition for {flag_key}"},
        }

    # get_evaluation_rules
    if not flag:
        return {
            "ok": False,
            "connector": SLUG,
            "tool": tool_name,
            "project": project,
            "flag_key": flag_key,
            "error": "flag_not_found",
        }
    return {
        "ok": True,
        "connector": SLUG,
        "tool": tool_name,
        "project": project,
        "environment": env_name,
        "flag_key": flag_key,
        "rules": [
            {"id": "rule_default", "kind": "default", "variation": True, "rollout": 100},
            {
                "id": "rule_staging_pilot",
                "kind": "match",
                "attribute": "tenant",
                "op": "in",
                "values": ["tenant_local", "tenant_demo"],
                "variation": True,
            },
        ],
        "note": "read-only evaluation rules; mutations require a separate certified write connector",
    }
