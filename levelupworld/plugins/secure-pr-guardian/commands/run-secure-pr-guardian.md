---
name: run-secure-pr-guardian
description: Run the Secure PR Guardian instruction routine for the current change, PR, or incident.
---

# Run Secure PR Guardian

1. Load skill `secure-pr-guardian`.
2. Identify matching automation IDs (A003, A004, A007, A011, A021, A026, A031, A068).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
