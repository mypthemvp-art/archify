---
name: run-repository-intelligence
description: Run the Repository Intelligence Plugin instruction routine for the current change, PR, or incident.
---

# Run Repository Intelligence Plugin

1. Load skill `repository-intelligence`.
2. Identify matching automation IDs (A001, A002, A022, A029, A030, A058, A060).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
