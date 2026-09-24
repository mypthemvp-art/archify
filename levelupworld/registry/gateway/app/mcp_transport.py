"""Streamable HTTP MCP termination at the policy gateway.

Clients connect to POST /mcp (JSON-RPC). The gateway:
  - advertises only non-quarantined, activated-eligible connector tools
  - never accepts raw connector URLs from the client
  - routes tools/call through policy evaluate + invoke

Tool names use the mcp__{connector_slug}__{tool_name} convention so Cursor
hooks and the gateway share the same identity.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from .auth import Principal, get_principal
from .models import Environment, InvokeRequest, PolicyDecision

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "agent-ops-mcp-gateway", "version": "0.5.0"}

router = APIRouter(tags=["mcp"])


def _tool_name(slug: str, tool: str) -> str:
    return f"mcp__{slug}__{tool}"


def _parse_tool_name(name: str) -> tuple[str, str] | None:
    if not name.startswith("mcp__"):
        return None
    rest = name[len("mcp__") :]
    if "__" not in rest:
        return None
    slug, tool = rest.split("__", 1)
    if not slug or not tool:
        return None
    return slug, tool


def build_mcp_router(
    *,
    registry,
    control_plane,
    evaluate_fn: Callable,
    invoke_fn: Callable,
) -> APIRouter:
    """Factory so main.py can inject live registry/evaluate/invoke callables."""

    def list_gateway_tools() -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for conn in registry.list():
            if control_plane.is_quarantined(conn.slug, conn.version):
                continue
            if conn.certification_state == "quarantined":
                continue
            for tool in conn.tools:
                tools.append(
                    {
                        "name": _tool_name(conn.slug, tool.name),
                        "description": tool.description or f"{conn.slug}.{tool.name}",
                        "inputSchema": tool.input_schema
                        or {"type": "object", "additionalProperties": True},
                        "_meta": {
                            "connector_slug": conn.slug,
                            "connector_version": conn.version,
                            "capability": tool.capability.value,
                            "requires_approval": tool.requires_approval,
                            "risk_level": tool.risk_level,
                        },
                    }
                )
        # Control-plane helpers always available
        tools.extend(
            [
                {
                    "name": "registry_list_connectors",
                    "description": "List connectors from the registry control plane.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"q": {"type": "string"}, "category": {"type": "string"}},
                    },
                },
                {
                    "name": "gateway_evaluate_policy",
                    "description": "Preflight policy evaluate without invoking a connector.",
                    "inputSchema": {
                        "type": "object",
                        "required": ["connector_slug", "tool_name"],
                        "properties": {
                            "connector_slug": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "arguments": {"type": "object"},
                            "environment": {"type": "string"},
                        },
                    },
                },
            ]
        )
        return tools

    async def handle_rpc(msg: dict[str, Any], principal: Principal, request: Request) -> dict[str, Any]:
        method = msg.get("method")
        rpc_id = msg.get("id")
        params = msg.get("params") or {}

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": SERVER_INFO,
                },
            }

        if method in {"notifications/initialized", "notifications/cancelled"}:
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {}}

        if method == "tools/list":
            # Strip _meta for wire protocol (clients ignore unknown fields, but keep clean)
            tools = []
            for t in list_gateway_tools():
                tools.append(
                    {
                        "name": t["name"],
                        "description": t["description"],
                        "inputSchema": t["inputSchema"],
                    }
                )
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": tools}}

        if method == "ping":
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {}}

        if method == "tools/call":
            name = params.get("name") or ""
            args = params.get("arguments") or {}
            # Reject client-supplied connector endpoint overrides
            if any(k in args for k in ("connector_url", "endpoint", "base_url", "raw_url")):
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "Rejected: client must not supply connector URLs; gateway resolves pinned versions.",
                            }
                        ],
                        "isError": True,
                    },
                }

            if name == "registry_list_connectors":
                items = registry.list(q=args.get("q"), category=args.get("category"))
                payload = {
                    "count": len(items),
                    "connectors": [
                        {"slug": c.slug, "version": c.version, "trust_tier": c.trust_tier.value} for c in items
                    ],
                }
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(payload)}]},
                }

            if name == "gateway_evaluate_policy":
                req = InvokeRequest(
                    actor=principal.subject,
                    org_id=principal.org_id,
                    tenant_id=principal.tenant_id,
                    project_id=request.headers.get("X-Project-ID", "project_local"),
                    environment=Environment(args.get("environment") or request.headers.get("X-Requested-Environment") or "development"),
                    connector_slug=args["connector_slug"],
                    tool_name=args["tool_name"],
                    arguments=args.get("arguments") or {},
                )
                result = evaluate_fn(req)
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
                }

            parsed = _parse_tool_name(name)
            if not parsed:
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [{"type": "text", "text": f"unknown tool: {name}"}],
                        "isError": True,
                    },
                }
            slug, tool = parsed
            env_raw = (
                args.pop("_environment", None)
                or request.headers.get("X-Requested-Environment")
                or "development"
            )
            grant = args.pop("approval_grant", None) or request.headers.get("X-Approval-Grant")
            idem = args.pop("idempotency_key", None) or request.headers.get("X-Idempotency-Key")
            invoke_req = InvokeRequest(
                actor=principal.subject,
                org_id=principal.org_id,
                tenant_id=principal.tenant_id,
                project_id=request.headers.get("X-Project-ID", "project_local"),
                environment=Environment(env_raw),
                connector_slug=slug,
                tool_name=tool,
                arguments=args,
                approval_grant=grant,
                idempotency_key=idem,
            )
            # Pre-evaluate for clearer MCP error shaping
            decision = evaluate_fn(invoke_req)
            if decision.get("decision") == PolicyDecision.require_approval.value:
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "error": "approval_required",
                                        "policy": decision,
                                        "hint": "Retry tools/call with approval_grant bound to args_hash",
                                    }
                                ),
                            }
                        ],
                        "isError": True,
                    },
                }
            if decision.get("decision") == PolicyDecision.deny.value:
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(decision)}],
                        "isError": True,
                    },
                }
            try:
                outcome = invoke_fn(invoke_req, principal)
            except HTTPException as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps({"error": exc.detail})}],
                        "isError": True,
                    },
                }
            # invoke_fn may return JSONResponse for approval_required
            if isinstance(outcome, JSONResponse):
                body = json.loads(outcome.body.decode())
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(body)}],
                        "isError": True,
                    },
                }
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {"content": [{"type": "text", "text": json.dumps(outcome)}]},
            }

        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    @router.post("/mcp")
    async def mcp_post(request: Request, principal: Principal = Depends(get_principal)):
        try:
            msg = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, f"invalid JSON-RPC body: {exc}") from exc
        if isinstance(msg, list):
            # Batch: process sequentially
            out = []
            for item in msg:
                out.append(await handle_rpc(item, principal, request))
            return out
        return await handle_rpc(msg, principal, request)

    @router.get("/mcp")
    def mcp_get():
        """Discovery / health for Streamable HTTP MCP entry."""
        return {
            "ok": True,
            "transport": "streamable_http",
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": SERVER_INFO,
            "endpoint": "/mcp",
            "note": "POST JSON-RPC methods: initialize, tools/list, tools/call",
        }

    return router
