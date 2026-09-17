---
name: run-featureops
description: Run the FeatureOps Plugin instruction routine for the current change, PR, or incident.
---

# Run FeatureOps Plugin

1. Load skill `featureops`.
2. Identify matching automation IDs (A053, A054).
3. Execute the skill routine with read-only tools first.
4. Return a structured report with correlation ID, findings, evidence, and gated next actions.
