---
name: run-mcp-security-gateway
description: Run the MCP Security Gateway instruction routine against the current PR, incident, or change under discussion.
---

# Run MCP Security Gateway

1. Load skill `mcp-security-gateway`.
2. Identify the matching automation IDs (A011–A020) for the user request.
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence links, and next gated actions.
