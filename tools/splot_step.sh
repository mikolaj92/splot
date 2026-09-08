#!/usr/bin/env bash
# Fala-compatible subprocess entry for Splot 0.3+ (Mojo fusion step).
# Host fills candidate payload signals; this only runs one fusion round.
# Expects Fala effector env (FALA_EFFECTOR_*) or SPLOT_REQUEST_PATH.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"

# Mojo binary + std library location (Fala process host uses a sanitized env).
pixi_bin="${FALA_PIXI_ENV:-}"
if [[ -z "$pixi_bin" ]]; then
  if [[ -x "$root/.pixi/envs/default/bin/mojo" ]]; then
    pixi_bin="$root/.pixi/envs/default/bin"
  elif [[ -x "$root/../Fala/.pixi/envs/default/bin/mojo" ]]; then
    pixi_bin="$root/../Fala/.pixi/envs/default/bin"
  fi
fi
if [[ -n "$pixi_bin" ]]; then
  export PATH="$pixi_bin:${PATH:-/usr/bin:/bin}"
  if [[ -z "${CONDA_PREFIX:-}" ]]; then
    export CONDA_PREFIX="$(cd "$pixi_bin/.." && pwd)"
  fi
  if [[ -z "${MODULAR_HOME:-}" ]]; then
    export MODULAR_HOME="${CONDA_PREFIX}/share/max"
  fi
fi

if ! command -v mojo >/dev/null 2>&1; then
  echo '{"ok":false,"error":"mojo not found"}' >&2
  exit 127
fi

if [[ -z "${SPLOT_REQUEST_PATH:-}" && -z "${FALA_EFFECTOR_MANIFEST:-}" ]]; then
  echo '{"ok":false,"error":"splot request path required"}' >&2
  exit 2
fi
if [[ -n "${SPLOT_REQUEST_PATH:-}" && ! -f "$SPLOT_REQUEST_PATH" ]]; then
  echo '{"ok":false,"error":"splot request file not found"}' >&2
  exit 2
fi
if [[ -n "${FALA_EFFECTOR_MANIFEST:-}" && ! -f "$FALA_EFFECTOR_MANIFEST" ]]; then
  echo '{"ok":false,"error":"Fala effector manifest not found"}' >&2
  exit 2
fi
cd "$root"
exec mojo run -I mojo -I vendor/EmberJson mojo/splot/step_main.mojo
