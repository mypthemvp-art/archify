---
name: run-production-triage-copilot
description: Run the Production Triage Copilot instruction routine for the current change, PR, or incident.
---

# Run Production Triage Copilot

1. Load skill `production-triage-copilot`.
2. Identify matching automation IDs (A024, A040, A041, A042, A043, A044, A045, A046, A074).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
