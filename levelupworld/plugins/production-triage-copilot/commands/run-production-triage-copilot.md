---
name: run-production-triage-copilot
description: Run the Production Triage Copilot instruction routine against the current PR, incident, or change under discussion.
---

# Run Production Triage Copilot

1. Load skill `production-triage-copilot`.
2. Identify the matching automation IDs (A021–A030) for the user request.
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence links, and next gated actions.
