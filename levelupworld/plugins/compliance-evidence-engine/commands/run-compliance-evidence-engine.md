---
name: run-compliance-evidence-engine
description: Run the Compliance Evidence Engine instruction routine for the current change, PR, or incident.
---

# Run Compliance Evidence Engine

1. Load skill `compliance-evidence-engine`.
2. Identify matching automation IDs (A080, A081, A082, A083, A084, A085, A086, A087, A088, A089, A090).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
