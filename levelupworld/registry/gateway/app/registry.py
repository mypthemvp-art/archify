"""Load certified connector manifests from disk (registry control plane source)."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ConnectorManifest

ROOT = Path(__file__).resolve().parents[2]
CONNECTORS_DIR = ROOT / "connectors"


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
        environment: str | None = None,
        q: str | None = None,
    ) -> list[ConnectorManifest]:
        items = list(self.connectors.values())
        if category:
            items = [c for c in items if c.category == category]
        if trust_tier:
            items = [c for c in items if c.trust_tier.value == trust_tier]
        if capability:
            items = [c for c in items if any(t.capability.value == capability for t in c.tools)]
        if environment:
            items = [c for c in items if environment in c.allowed_environments]
        if q:
            ql = q.lower()
            items = [
                c
                for c in items
                if ql in c.slug.lower()
                or ql in c.display_name.lower()
                or ql in c.description.lower()
                or ql in c.owner_team.lower()
            ]
        return sorted(items, key=lambda c: c.rank)

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
