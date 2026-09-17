# LevelUpWorld automation blueprints

These markdown files are **instruction routines** for Cursor Automations and local agents.

Cursor Automations are configured in the product UI / `/automate` skill today; this directory is the repository source of truth for prompts, triggers, guardrails, and mutation classes so they can be reviewed in PRs and pasted or synced into Automations.

| Range | Plugin | Skill |
|---|---|---|
| A001–A010 | Secure PR Guardian | `secure-pr-guardian` |
| A011–A020 | MCP Security Gateway | `mcp-security-gateway` |
| A021–A030 | Production Triage Copilot | `production-triage-copilot` |
| A031–A040 | Database Change Guardian | `database-change-guardian` |
| A041–A050 | GitOps Release Controller | `gitops-release-controller` |
| A051–A060 | Compliance Evidence Engine | `compliance-evidence-engine` |
| A061–A070 | Developer Productivity Router | `levelupworld-catalog-router` (blueprint-only) |
| A071–A080 | Platform Observability Analyst | `levelupworld-catalog-router` (blueprint-only) |
| A081–A090 | Secure Connector Factory | `levelupworld-catalog-router` (blueprint-only) |
| A091–A100 | Knowledge & Docs Copilot | `levelupworld-catalog-router` (+ `archify` for A092) |

Full catalog: [`levelupworld/docs/CATALOG.md`](../../levelupworld/docs/CATALOG.md)

## Creating a Cursor Automation from a blueprint

1. Open the blueprint (for example `a022-incident-timeline.md`).
2. In Cursor, run `/automate` or visit cursor.com/automations.
3. Copy the trigger + agent instructions from the blueprint.
4. Attach only the MCP tools allowed by the blueprint mutation class.
5. Keep budgets and the project policy hooks enabled.
