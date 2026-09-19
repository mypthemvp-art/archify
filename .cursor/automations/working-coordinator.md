---
id: working-coordinator
title: Working lane coordinator
plugin: mcp-security-gateway
mutation: none
status: operational
contract: [trigger, inputs, plan, guardrails, approval, evidence, verification]
---

# Working lane coordinator

Outside the 100-automation catalog. Copy this prompt into a Cursor Automation. Schedule it every 15 minutes. There is no Working status trigger.

## Prompt

Load `.cursor/skills/levelupworld/agent-window-lanes/SKILL.md`.

Run `node levelupworld/scripts/needs-attention-triage.mjs` on this environment's cloud agents. Keep rows where `lane` is `working`.

- `in_progress`: do not message anyone and do not follow up.
- `stalled_running`: subscribe a timer. The run is still working. Do not send a follow-up.
- `working_over_budget`: one Slack line with the run URL, `correlation_id`, and that reason. No logs.

Ignore `needs_attention` and `read` rows. Those belong to the other two automations.

If tenant is missing, print the JSON and stop.
