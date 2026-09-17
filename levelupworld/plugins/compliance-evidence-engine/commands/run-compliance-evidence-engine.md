---
name: run-compliance-evidence-engine
description: Run the Compliance Evidence Engine instruction routine against the current PR, incident, or change under discussion.
---

# Run Compliance Evidence Engine

1. Load skill `compliance-evidence-engine`.
2. Identify the matching automation IDs (A051–A060) for the user request.
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence links, and next gated actions.
