---
name: run-secure-pr-guardian
description: Run the Secure PR Guardian instruction routine against the current PR, incident, or change under discussion.
---

# Run Secure PR Guardian

1. Load skill `secure-pr-guardian`.
2. Identify the matching automation IDs (A001–A010) for the user request.
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence links, and next gated actions.
