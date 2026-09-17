---
name: run-privacy-engineering
description: Run the Privacy Engineering Plugin instruction routine for the current change, PR, or incident.
---

# Run Privacy Engineering Plugin

1. Load skill `privacy-engineering`.
2. Identify matching automation IDs (A005, A049, A051, A082, A084, A095).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
