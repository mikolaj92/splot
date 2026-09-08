#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
mise exec pixi -- pixi run full-smoke
uv run pytest -q
