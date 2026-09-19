---
name: needs-attention-coordinator
description: >-
  Coordinates the Needs Attention path: classify cloud-agent runs, keep
  subagents inside rails, and page a person only for human-only blockers.
  Use when the user asks to automate Needs Attention or unstick subagents.
---

# Needs Attention coordinator

Needs Attention is an Agents Window group, not a Cloud Agent lifecycle status. Cursor Automations cannot trigger on it, and Cloud Agent MCP cannot approve a prompt or send a follow-up to another run.

## What is automated

1. `subagentStart` denies any subagent that is not on `.cursor/needs-attention/rails.json`. `ask` is not available here; Cursor treats it as deny.
2. `subagentStop` submits one fixed follow-up when a completed subagent stopped to ask. The follow-up does not copy the subagent summary. Human-only blockers do not auto-continue.
3. `stop` retries an errored parent turn, up to `errorRetries`, and does nothing on abort or a normal completion.
4. `node levelupworld/scripts/needs-attention-triage.mjs` classifies a fleet snapshot into `continue`, `watch`, `page_human`, or `ignore`.

## Routine

1. Read the rails file. If tenant is missing, classify only; do not write, notify, or resume.
2. List runs with Cloud Agent MCP. Fetch events only for runs that are `ERROR`, `IDLE` without a PR, `INSTALL_FAILED`, or quiet past `stallAfterMs`.
3. Pipe `{ tenant, now, agents, eventsById }` through the triage script. Keep its `correlation_id`.
4. For `page_human`, name the `human_only` code and the run URL. Do not include logs that may contain secrets.
5. For `continue`, start a new automation run or tell the parent to keep going under the resolver subagent. Do not POST to the Cloud Agents API from a shell.
6. For `watch`, subscribe to a timer or the PR. Do not ping a person.
7. For `ignore`, say nothing.

## Not in scope

- Clicking Allow on a local approval prompt.
- Answering a plan-mode gate.
- Adding an environment secret. That remains `request-environment-setup-actions` and a person.
- The Working lane and the read-automation full check. Those are `.cursor/automations/working-coordinator.md` and `.cursor/automations/read-automation-check.md`.
