#!/usr/bin/env bash
# Run a Mojo smoke with EmberJson. Prefers local pixi; falls back to Fala pixi env.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
target="${1:?mojo file}"
case "$target" in
  /*) file="$target" ;;
  *) file="$root/$target" ;;
esac

run_mojo() {
  mojo run -I "$root/mojo" -I "$root/vendor/EmberJson" "$file"
}

if command -v pixi >/dev/null 2>&1 && [[ -f "$root/pixi.toml" ]]; then
  # shellcheck disable=SC1091
  cd "$root"
  # If pixi env exists for splot, use it; else fall through
  if pixi run -- true 2>/dev/null; then
    exec pixi run -- bash -c "mojo run -I mojo -I vendor/EmberJson \"$file\""
  fi
fi

# Fallback: Fala workspace pixi env (dev machine layout)
fala_pixi="${FALA_PIXI_ENV:-$root/../Fala/.pixi/envs/default/bin}"
if [[ -x "$fala_pixi/mojo" ]]; then
  export PATH="$fala_pixi:$PATH"
  cd "$root"
  exec mojo run -I mojo -I vendor/EmberJson "$file"
fi

echo "mojo not found; install pixi deps or set FALA_PIXI_ENV" >&2
exit 1
