"""Load certified connector manifests from disk (registry control plane source)."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ConnectorManifest

ROOT = Path(__file__).resolve().parents[2]
CONNECTORS_DIR = ROOT / "connectors"

TRUST_TIER_RANK = {
    "unverified": 1,
    "sandboxed": 2,
    "reviewed": 3,
    "certified": 4,
    "production_critical": 5,
}


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


class Registry:
    def __init__(self, connectors_dir: Path | None = None):
        self.connectors_dir = connectors_dir or CONNECTORS_DIR
        self.connectors: dict[str, ConnectorManifest] = {}
        self.reload()

    def reload(self) -> None:
        self.connectors.clear()
        if not self.connectors_dir.exists():
            return
        for path in sorted(self.connectors_dir.glob("*.manifest.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            manifest = ConnectorManifest.model_validate(data)
            self.connectors[manifest.slug] = manifest

    def list(
        self,
        *,
        category: str | None = None,
        trust_tier: str | None = None,
        capability: str | None = None,
        operation: str | None = None,
        environment: str | None = None,
        certification_state: str | None = None,
        transport: str | None = None,
        data_classification: str | None = None,
        health: str | None = None,
        owner: str | None = None,
        q: str | None = None,
        sort: str | None = None,
        trust_tier_min: int | None = None,
    ) -> list[ConnectorManifest]:
        items = list(self.connectors.values())

        categories = _split_csv(category)
        if categories:
            items = [c for c in items if c.category in categories]

        tiers = _split_csv(trust_tier)
        if tiers:
            # allow numeric trustTier=3,4 as well as names
            resolved: set[str] = set()
            for t in tiers:
                if t.isdigit():
                    for name, rank in TRUST_TIER_RANK.items():
                        if rank == int(t):
                            resolved.add(name)
                else:
                    resolved.add(t)
            items = [c for c in items if c.trust_tier.value in resolved]

        if trust_tier_min is not None:
            items = [c for c in items if TRUST_TIER_RANK.get(c.trust_tier.value, 0) >= trust_tier_min]

        ops = _split_csv(capability or operation)
        if ops:
            items = [c for c in items if any(t.capability.value in ops for t in c.tools)]

        environments = _split_csv(environment)
        if environments:
            items = [c for c in items if any(e in c.allowed_environments for e in environments)]

        cert_states = _split_csv(certification_state)
        if cert_states:
            items = [c for c in items if c.certification_state in cert_states]

        transports = _split_csv(transport)
        if transports:
            items = [c for c in items if c.transport in transports]

        classifications = _split_csv(data_classification)
        if classifications:
            items = [c for c in items if c.data_classification in classifications]

        health_filters = _split_csv(health)
        if health_filters:
            filtered = []
            for c in items:
                healthy_flag = bool((c.health or {}).get("healthy", True))
                status = "healthy" if healthy_flag else "degraded"
                err = float((c.health or {}).get("error_rate_24h") or 0)
                if err >= 0.2:
                    status = "unhealthy"
                if status in health_filters or ("unknown" in health_filters and not c.health):
                    filtered.append(c)
            items = filtered

        if owner:
            ol = owner.lower()
            items = [c for c in items if ol in c.owner_team.lower()]

        if q:
            ql = q.lower()
            items = [
                c
                for c in items
                if ql in c.slug.lower()
                or ql in c.display_name.lower()
                or ql in c.description.lower()
                or ql in c.owner_team.lower()
                or any(ql in t.name.lower() for t in c.tools)
            ]

        return self._sort(items, sort)

    def _sort(self, items: list[ConnectorManifest], sort: str | None) -> list[ConnectorManifest]:
        raw = sort or "rank"
        reverse = raw.startswith("-")
        key = raw.lstrip("-")

        def activity(c: ConnectorManifest) -> float:
            h = c.health or {}
            return float(h.get("success_rate_24h") or 0) * 100 - float(h.get("error_rate_24h") or 0) * 100

        sorters = {
            "rank": lambda c: c.rank,
            "name": lambda c: c.display_name.lower(),
            "trust_tier": lambda c: TRUST_TIER_RANK.get(c.trust_tier.value, 0),
            "activity_24h": activity,
            "p95_latency_ms": lambda c: int((c.health or {}).get("p95_latency_ms") or 0),
            "success_rate_24h": lambda c: float((c.health or {}).get("success_rate_24h") or 0),
        }
        fn = sorters.get(key, sorters["rank"])
        # Default rank ascending; activity/latency often requested descending via -prefix
        if key == "rank" and not sort:
            reverse = False
        return sorted(items, key=fn, reverse=reverse)

    def get(self, slug: str) -> ConnectorManifest | None:
        return self.connectors.get(slug)

    def get_tool(self, slug: str, tool_name: str):
        conn = self.get(slug)
        if not conn:
            return None, None
        for tool in conn.tools:
            if tool.name == tool_name:
                return conn, tool
        return conn, None
