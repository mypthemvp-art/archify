---
name: run-open-source-maintenance
description: Run the Open-Source Maintenance Plugin instruction routine for the current change, PR, or incident.
---

# Run Open-Source Maintenance Plugin

1. Load skill `open-source-maintenance`.
2. Identify matching automation IDs (A013, A061, A062, A063, A064, A065, A066, A067, A088).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
