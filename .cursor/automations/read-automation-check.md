---
id: read-automation-check
title: Read automation full check
plugin: mcp-security-gateway
mutation: none
status: operational
contract: [trigger, inputs, plan, guardrails, approval, evidence, verification]
---

# Read automation full check

Outside the 100-automation catalog. Copy this prompt into a Cursor Automation on a daily schedule, or run it before relying on any read-only automation.

## Prompt

Load `.cursor/skills/levelupworld/agent-window-lanes/SKILL.md`.

Run `node levelupworld/scripts/check-read-automations.mjs`. That command opens every catalog automation whose mutation class is `none`. Do not sample. Do not skip an ID because the set is large.

- `ok: true`: report `correlation_id`, how many were checked, and how many plan/apply rows were skipped.
- `ok: false`: list every finding. Do not edit the blueprints in this run. A person reviews the finding list.

Plan and apply automations are not read automations. Leave them in `skipped`.

This check does not resume cloud agents. Finished runs with a pull request are the Read lane in the triage script; reviewing those diffs is a separate pass and still read-only.
