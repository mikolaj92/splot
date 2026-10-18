#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
pixi run --locked full-smoke
uv run --locked --extra dev pytest -q
