---
name: levelupworld-catalog-router
description: >-
  Routes requests to the LevelUpWorld 100-automation catalog and the six
  priority plugin skills. Use when the user mentions LevelUpWorld, Cursor
  automations catalog, MCP gateway governance, or asks which automation/skill
  to run for PR security, incidents, DB migrations, releases, or compliance.
---

# LevelUpWorld catalog router

## Routine

1. Read `levelupworld/docs/CATALOG.md` (or `catalog.json`) to resolve automation IDs.
2. Pick the matching priority skill under `.cursor/skills/levelupworld/<plugin>/`.
3. Open the blueprint in `.cursor/automations/` for trigger, output, and guardrail details.
4. Enforce mutation class: `none` → report only; `plan` → reviewable PR/plan; `apply` → require approval gateway.
5. Apply always-on Rules in `.cursor/rules/levelupworld-*.mdc`.
6. For architecture/workflow diagrams of the automation itself or the system under change, use the `archify` skill (`A092`).

## Priority map

| Priority | Plugin skill | IDs |
|---:|---|---|
| 1 | `secure-pr-guardian` | A001–A010 |
| 2 | `mcp-security-gateway` | A011–A020 |
| 3 | `production-triage-copilot` | A021–A030 |
| 4 | `database-change-guardian` | A031–A040 |
| 5 | `gitops-release-controller` | A041–A050 |
| 6 | `compliance-evidence-engine` | A051–A060 |

Additional catalog domains A061–A100 remain blueprint-only until their plugins are promoted behind the gateway.
