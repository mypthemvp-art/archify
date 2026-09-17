---
name: levelupworld-catalog-router
description: >-
  Routes requests across the LevelUpWorld / agent-ops catalog of 100 Cursor
  automations and the 12 priority plugins. Use when the user mentions the
  automation catalog, agent-ops, MCP gateway governance, or asks which
  automation/skill to run.
---

# LevelUpWorld catalog router

## Routine

1. Read `levelupworld/docs/CATALOG.md` or `catalog.json` to resolve automation IDs.
2. Pick the matching skill under `.cursor/skills/levelupworld/<plugin>/`.
3. Open the blueprint in `.cursor/automations/` for trigger, output/guardrail, and mutation class.
4. Enforce the automation contract: trigger → inputs → plan → guardrails → approval → evidence → verification.
5. Apply always-on Rules in `.cursor/rules/`.
6. For architecture maps (A001) or diagram deltas, prefer the `archify` skill for validated HTML artifacts.

## 12-plugin priority map

| Priority | Skill | IDs |
|---:|---|---|
| 1 | `secure-pr-guardian` | A003, A004, A007, A011, A021, A026, A031, A068 |
| 2 | `mcp-security-gateway` | A091, A092, A093, A094, A095, A096, A097, A098, A099 |
| 3 | `production-triage-copilot` | A024, A040, A041, A042, A043, A044, A045, A046, A074 |
| 4 | `database-change-guardian` | A010, A046, A047, A048, A049 |
| 5 | `gitops-release-controller` | A036, A037, A038, A039, A070, A075, A076, A077, A078, A079, A100 |
| 6 | `compliance-evidence-engine` | A080, A081, A082, A083, A084, A085, A086, A087, A088, A089, A090 |
| 7 | `featureops` | A053, A054 |
| 8 | `accessibility-qa` | A055, A056, A057 |
| 9 | `repository-intelligence` | A001, A002, A022, A029, A030, A058, A060 |
| 10 | `cloud-cost-governor` | A045, A069, A071, A072, A073 |
| 11 | `privacy-engineering` | A005, A049, A051, A082, A084, A095 |
| 12 | `open-source-maintenance` | A013, A061, A062, A063, A064, A065, A066, A067, A088 |
