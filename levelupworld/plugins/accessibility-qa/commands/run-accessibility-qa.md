---
name: run-accessibility-qa
description: Run the Accessibility QA Plugin instruction routine for the current change, PR, or incident.
---

# Run Accessibility QA Plugin

1. Load skill `accessibility-qa`.
2. Identify matching automation IDs (A055, A056, A057).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
