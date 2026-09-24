#!/usr/bin/env bash
# Cloud Agent install: prepare every runnable component in the repository.
# Runs after the source tree is checked out. Must be idempotent and terminate.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "==> Archify CLI / renderer dependencies (archify/)"
( cd archify && npm ci )

echo "==> Registry web catalog dependencies (levelupworld/registry/web/, Next.js)"
( cd levelupworld/registry/web && npm ci )

echo "==> Registry gateway dependencies (levelupworld/registry/gateway/, FastAPI)"
# The base image ships Python 3.12 as an externally-managed interpreter with no
# python3-venv, so install into the per-user site with --break-system-packages.
# This keeps the gateway (and its pytest suite) runnable without extra system
# packages; ~/.local/bin holds the uvicorn/pytest entry points.
python3 -m pip install --break-system-packages --user \
  -r levelupworld/registry/gateway/requirements.txt pytest

echo "install complete"
