---
name: run-mcp-security-gateway
description: Run the MCP Security Gateway instruction routine for the current change, PR, or incident.
---

# Run MCP Security Gateway

1. Load skill `mcp-security-gateway`.
2. Identify matching automation IDs (A091, A092, A093, A094, A095, A096, A097, A098, A099).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
