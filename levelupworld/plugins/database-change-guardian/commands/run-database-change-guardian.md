---
name: run-database-change-guardian
description: Run the Database Change Guardian instruction routine against the current PR, incident, or change under discussion.
---

# Run Database Change Guardian

1. Load skill `database-change-guardian`.
2. Identify the matching automation IDs (A031–A040) for the user request.
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence links, and next gated actions.
