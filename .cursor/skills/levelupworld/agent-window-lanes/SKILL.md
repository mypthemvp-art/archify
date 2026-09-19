---
name: agent-window-lanes
description: >-
  Covers the Working lane and the full read-automation check. Use with the
  Needs Attention coordinator when the user wants all three Agents Window lanes automated.
---

# Working and read lanes

Needs Attention, Working, and Read are Agents Window groups. They are not Cloud Agent API statuses. `node levelupworld/scripts/needs-attention-triage.mjs` now adds `lane` and `summary`.

## Working

1. Filter `lane === "working"`.
2. Do not follow up a `RUNNING` run. A follow-up while it is in progress is rejected.
3. Under `stallAfterMs`, leave it alone.
4. Between `stallAfterMs` and `workingBudgetMs`, subscribe a timer. Still do not message a person.
5. Over `workingBudgetMs`, page with reason `working_over_budget` and the run URL. No logs.

## Read full check

1. Run `node levelupworld/scripts/check-read-automations.mjs`.
2. It opens every catalog automation with `mutation: none` and checks id, trigger, capability, output, contract sections, read-only instruction, deny list, and skill file.
3. Exit 1 means a finding. Quote `correlation_id` and the finding list.
4. Do not treat plan or apply automations as read automations.

## Shared rails

Subagent types `working-watch` and `read-automation-auditor` are on the allowlist and are readonly. Missing tenant still blocks writes and outbound notices.
