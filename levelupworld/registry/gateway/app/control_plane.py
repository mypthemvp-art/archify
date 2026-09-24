"""In-memory control-plane state: activations, quarantine, test runs, policy logs."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class ControlPlaneStore:
    def __init__(self):
        self.activations: dict[str, dict[str, Any]] = {}
        self.quarantines: dict[str, dict[str, Any]] = {}  # key: slug@version
        self.test_runs: dict[str, dict[str, Any]] = {}
        self.policy_decisions: list[dict[str, Any]] = []
        self.certification_decisions: list[dict[str, Any]] = []

    def quarantine(self, slug: str, version: str, reason: str, actor: str) -> dict[str, Any]:
        key = f"{slug}@{version}"
        record = {
            "id": f"qrn_{uuid.uuid4().hex}",
            "slug": slug,
            "version": version,
            "reason": reason,
            "actor": actor,
            "quarantined_at": _now(),
            "lifted_at": None,
            "lifted_by": None,
            "lift_reason": None,
            "active": True,
        }
        self.quarantines[key] = record
        # Disable all activations for this version
        for act in self.activations.values():
            if act["slug"] == slug and act["version"] == version:
                act["enabled"] = False
                act["disabled_reason"] = f"quarantine: {reason}"
                act["status"] = "disabled"
        return record

    def unquarantine(self, slug: str, version: str, reason: str, actor: str) -> dict[str, Any]:
        key = f"{slug}@{version}"
        existing = self.quarantines.get(key)
        if not existing or not existing.get("active"):
            raise KeyError("active quarantine not found")
        existing["active"] = False
        existing["lifted_at"] = _now()
        existing["lifted_by"] = actor
        existing["lift_reason"] = reason
        return existing

    def is_quarantined(self, slug: str, version: str) -> bool:
        q = self.quarantines.get(f"{slug}@{version}")
        return bool(q and q.get("active"))

    def list_quarantines(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        items = list(self.quarantines.values())
        if active_only:
            items = [q for q in items if q.get("active")]
        return items

    def request_activation(self, body: dict[str, Any]) -> dict[str, Any]:
        act_id = f"act_{uuid.uuid4().hex}"
        record = {
            "id": act_id,
            "org_id": body.get("org_id", "org_local"),
            "slug": body["slug"],
            "version": body["version"],
            "project_id": body["project_id"],
            "environment": body["environment"],
            "enabled": False,
            "status": "pending",
            "requested_by": body.get("actor", "user:unknown"),
            "created_at": _now(),
            "approved_by": None,
            "approved_at": None,
            "expires_at": body.get("expires_at"),
            "disabled_reason": None,
            "renewed_at": None,
        }
        self.activations[act_id] = record
        return record

    def approve_activation(self, activation_id: str, approver: str, approve: bool = True) -> dict[str, Any]:
        act = self.activations.get(activation_id)
        if not act:
            raise KeyError("activation not found")
        if self.is_quarantined(act["slug"], act["version"]):
            raise ValueError("connector version is quarantined")
        act["approved_by"] = approver
        act["approved_at"] = _now()
        if approve:
            act["enabled"] = True
            act["status"] = "approved"
            act["disabled_reason"] = None
            if not act.get("expires_at"):
                act["expires_at"] = (datetime.now(tz=timezone.utc) + timedelta(days=90)).isoformat()
        else:
            act["enabled"] = False
            act["status"] = "denied"
        return act

    def disable_activation(self, activation_id: str, actor: str, reason: str) -> dict[str, Any]:
        act = self.activations.get(activation_id)
        if not act:
            raise KeyError("activation not found")
        act["enabled"] = False
        act["status"] = "disabled"
        act["disabled_reason"] = reason
        act["disabled_by"] = actor
        act["disabled_at"] = _now()
        return act

    def renew_activation(self, activation_id: str, actor: str, days: int = 90) -> dict[str, Any]:
        act = self.activations.get(activation_id)
        if not act:
            raise KeyError("activation not found")
        if self.is_quarantined(act["slug"], act["version"]):
            raise ValueError("connector version is quarantined")
        if act.get("status") == "denied":
            raise ValueError("denied activations cannot be renewed")
        base = _parse_iso(act.get("expires_at")) or datetime.now(tz=timezone.utc)
        if base < datetime.now(tz=timezone.utc):
            base = datetime.now(tz=timezone.utc)
        act["expires_at"] = (base + timedelta(days=max(1, days))).isoformat()
        act["renewed_at"] = _now()
        act["renewed_by"] = actor
        if act.get("status") in {"approved", "disabled"} and not self.is_quarantined(act["slug"], act["version"]):
            act["enabled"] = True
            act["status"] = "approved"
            act["disabled_reason"] = None
        return act

    def list_activations(self, project_id: str | None = None) -> list[dict[str, Any]]:
        items = list(self.activations.values())
        if project_id:
            items = [a for a in items if a["project_id"] == project_id]
        return items

    def record_certification_decision(
        self,
        *,
        slug: str,
        version: str,
        decision: str,
        actor: str,
        reason: str,
        test_run_id: str | None = None,
        org_id: str = "org_local",
    ) -> dict[str, Any]:
        allowed = {"review", "certify", "fail", "waive"}
        if decision not in allowed:
            raise ValueError(f"decision must be one of {sorted(allowed)}")
        record = {
            "id": f"cert_{uuid.uuid4().hex}",
            "org_id": org_id,
            "slug": slug,
            "version": version,
            "decision": decision,
            "actor": actor,
            "reason": reason,
            "test_run_id": test_run_id,
            "created_at": _now(),
        }
        self.certification_decisions.append(record)
        return record

    def list_certification_queue(self, registry_connectors: dict[str, Any]) -> list[dict[str, Any]]:
        """Versions needing reviewer attention: not certified, or actively quarantined."""
        terminal: dict[str, str] = {}
        for d in self.certification_decisions:
            if d["decision"] in {"certify", "fail", "waive"}:
                terminal[f"{d['slug']}@{d['version']}"] = d["decision"]

        queue: list[dict[str, Any]] = []
        for slug, conn in registry_connectors.items():
            key = f"{slug}@{conn.version}"
            quarantined = self.is_quarantined(slug, conn.version)
            state = conn.certification_state
            needs_review = state in {"in_lab", "reviewed", "failed", "quarantined"} or quarantined
            if state == "certified" and terminal.get(key) == "certify" and not quarantined:
                continue
            if needs_review or state != "certified":
                queue.append(
                    {
                        "slug": slug,
                        "version": conn.version,
                        "certification_state": state,
                        "owner_team": conn.owner_team,
                        "trust_tier": conn.trust_tier.value,
                        "quarantined": quarantined,
                        "last_decision": terminal.get(key),
                    }
                )
        return queue

    def list_certification_decisions(self, slug: str | None = None) -> list[dict[str, Any]]:
        items = self.certification_decisions
        if slug:
            items = [d for d in items if d["slug"] == slug]
        return list(reversed(items[-200:]))

    def create_test_run(self, slug: str, version: str, suite: str, org_id: str = "org_local") -> dict[str, Any]:
        run_id = f"run_{uuid.uuid4().hex}"
        # Spec families from MULTI-TENANT-DASHBOARD-SPEC / SECURITY-TEST-LAB.md
        suite_families = {
            "protocol": ["mcp_init", "tool_discovery", "schema_validation", "malformed_inputs"],
            "authn": ["missing_token", "expired_token", "wrong_audience", "insufficient_scope"],
            "authz": ["tenant_escape", "project_env_mismatch", "allowlist_bypass"],
            "input_safety": ["sql_injection", "path_traversal", "shell_metachar", "bad_url", "oversized"],
            "ssrf_egress": ["metadata_ip", "private_range", "redirect_chain", "dns_rebinding", "unapproved_host"],
            "data_protection": ["secret_redaction", "pii_redaction", "output_size_cap", "retention"],
            "prompt_injection": ["hostile_issue", "hostile_log", "hostile_doc", "hostile_connector_response"],
            "reliability": ["timeout", "retry", "circuit_breaker", "partial_failure", "duplicate_request"],
            "approval_binding": ["arg_mutation", "replay", "expiry", "wrong_identity"],
            "supply_chain": ["pinned_digest", "signature", "sbom", "vuln_policy"],
            "auditability": ["correlation_id", "policy_evidence", "tamper_evident", "trace_linkage"],
            # legacy aliases
            "schema_conformance": ["schema_validation"],
            "auth_negative": ["missing_token", "expired_token"],
            "timeout_retry": ["timeout", "retry"],
            "secret_pii_redaction": ["secret_redaction", "pii_redaction"],
            "injection_traversal_ssrf": ["sql_injection", "path_traversal", "metadata_ip"],
            "idempotency": ["duplicate_request"],
        }
        hard_gates = [
            "pinned_digest",
            "owner_present",
            "no_embedded_creds",
            "egress_restricted",
            "tenant_authz",
            "write_tools_require_approval",
            "immutable_audit",
        ]
        if suite == "full":
            selected_tests: list[str] = []
            for tests in suite_families.values():
                selected_tests.extend(tests)
            # de-dupe preserve order
            seen: set[str] = set()
            ordered: list[str] = []
            for t in selected_tests:
                if t not in seen:
                    seen.add(t)
                    ordered.append(t)
            selected_tests = ordered
        else:
            selected_tests = list(suite_families.get(suite, [suite]))

        force_fail = "fail" in slug
        results = []
        overall = "passed"
        for name in selected_tests:
            passed = not force_fail
            if not passed:
                overall = "failed"
            results.append({"name": name, "family": suite if suite != "full" else "full", "status": "passed" if passed else "failed"})

        gate_results = []
        for gate in hard_gates:
            passed = not force_fail
            if not passed:
                overall = "failed"
            gate_results.append({"gate": gate, "passed": passed})

        record = {
            "id": run_id,
            "org_id": org_id,
            "slug": slug,
            "version": version,
            "suite": suite,
            "status": overall,
            "report": {
                "results": results,
                "hard_gates": gate_results,
                "certification_gate": overall == "passed",
                "note": "Ephemeral lab stub — expand to real probes per SECURITY-TEST-LAB.md",
            },
            "started_at": _now(),
            "finished_at": _now(),
        }
        self.test_runs[run_id] = record
        return record

    def get_test_run(self, run_id: str) -> dict[str, Any] | None:
        return self.test_runs.get(run_id)

    def log_policy_decision(self, policy_key: str, decision: str, correlation_id: str, reason: str, input_data: dict):
        self.policy_decisions.append(
            {
                "id": f"pold_{uuid.uuid4().hex}",
                "policy_key": policy_key,
                "decision": decision,
                "correlation_id": correlation_id,
                "reason": reason,
                "input": input_data,
                "created_at": _now(),
            }
        )

    def list_policy_decisions(self, policy_key: str | None = None) -> list[dict[str, Any]]:
        items = self.policy_decisions
        if policy_key:
            items = [d for d in items if d["policy_key"] == policy_key]
        return list(reversed(items[-200:]))
