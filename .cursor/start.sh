#!/usr/bin/env bash
# Cloud Agent start: re-assert environment invariants on every boot.
# Must be idempotent and terminate (no long-running processes here).
set -euo pipefail

# The Cloud Agent injects a managed git credential rewrite that turns every
# github.com URL into an authenticated "x-access-token@github.com" form so the
# agent can push. That rewrite is applied by `git remote get-url`.
#
# Archify's repository-evidence tests (archify/test/repository-evidence.test.mjs)
# create throwaway local repositories with placeholder origins under
# github.com/example/*, then read them back with `git remote get-url` and compare
# to the authored URL. The managed rewrite corrupts those placeholder origins and
# makes the tests fail in Cloud only (normal CI has no such rewrite).
#
# Re-assert identity rewrites for the example/* placeholder namespace so the
# token is NOT injected for those throwaway repos. Real repositories (e.g. the
# checked-out project) still receive the managed push token, so `git push`
# keeps working. This runs every boot, after the managed config is injected.
for base in \
  "https://github.com/example/" \
  "git@github.com:example/" \
  "ssh://git@github.com/example/"; do
  git config --global --replace-all "url.${base}.insteadOf" "$base"
done

echo "start complete"
