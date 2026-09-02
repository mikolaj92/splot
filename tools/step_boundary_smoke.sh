#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

stderr_file="$(mktemp)"
trap 'rm -f "$stderr_file"' EXIT
if env -u SPLOT_REQUEST_PATH -u FALA_EFFECTOR_MANIFEST -u FALA_EFFECTOR_INPUT_DIR -u FALA_EFFECTOR_OUTPUT_DIR ./tools/splot_step.sh > /dev/null 2>"$stderr_file"; then
  echo "step boundary smoke: missing request unexpectedly succeeded" >&2
  exit 1
fi
grep -F '"ok":false' "$stderr_file" >/dev/null
grep -F 'request path required' "$stderr_file" >/dev/null
if grep -F 'cam_a' "$stderr_file" >/dev/null; then
  echo "step boundary smoke: fixture decision leaked into missing-request error" >&2
  exit 1
fi

output="$(SPLOT_REQUEST_PATH=examples/fixtures/player_camera_director.request.json ./tools/splot_step.sh)"
printf '%s' "$output" | grep -F '"selected_candidate_id":"cam_a"' >/dev/null
printf '%s
' "splot step boundary smoke ok"
