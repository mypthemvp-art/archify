# Mutation expansion observe gate

Before expanding beyond `github-write` dry-run / non-prod PR create, observe staging metrics.

## API

```http
GET /api/v1/metrics/mutations
```

Returns process-lifetime counts for mutation-shaped audit events, deny rate, grants consumed, and dual-approval request volume.

## Gate

Do **not** expand mutations until:

1. Staging has exercised approval-bound invokes (grants consumed ≥ 1 in the window you care about).
2. Deny path is proven (failed args_hash / wrong env show up as denies).
3. Dual approval + step-up works for any production-bound request.
4. `github-write` remains dry-run (`GITHUB_WRITE_DRY_RUN=1`) until a named security review lifts it per repo allowlist.
5. Hook bypass proof CI is green on the same commit.

`expansion_ready` in the metrics payload is a coarse heuristic — human review still required.
