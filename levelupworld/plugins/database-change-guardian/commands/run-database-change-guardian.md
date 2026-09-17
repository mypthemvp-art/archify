---
name: run-database-change-guardian
description: Run the Database Change Guardian instruction routine for the current change, PR, or incident.
---

# Run Database Change Guardian

1. Load skill `database-change-guardian`.
2. Identify matching automation IDs (A010, A046, A047, A048, A049).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
