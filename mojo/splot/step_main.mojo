"""CLI entry: run one fusion step from a JSON request file or stdin path.

Usage:
  mojo run -I mojo -I vendor/EmberJson mojo/splot/step_main.mojo <request.json>
  mojo run ... mojo/splot/step_main.mojo --  # reads path from FALA_EFFECTOR_MANIFEST

When FALA_EFFECTOR_OUTPUT_DIR is set (Fala subprocess contract), writes
output/result.json with the step result object.

The host must already have filled candidate payload signals (any evaluator).
"""

from std.pathlib import Path
from std.os import getenv
from emberjson import Value, to_string
from splot.adapters_fala import fusion_step
from splot.json_util import parse_json


def _write_result(text: String) raises:
    var out_dir = getenv("FALA_EFFECTOR_OUTPUT_DIR")
    if out_dir.byte_length() == 0:
        print(text)
        return
    var result_path = out_dir + "/result.json"
    # Fala effector contract: result.json is a JSON object (the decision envelope).
    Path(result_path).write_text(text)


def main() raises:
    var path = String("")
    # Prefer argv-style: first non-flag argument after program name is request path.
    # Mojo main does not always expose argv the same way; use env + default fixture.
    var env_path = getenv("SPLOT_REQUEST_PATH")
    if env_path.byte_length() > 0:
        path = env_path
    else:
        var manifest = getenv("FALA_EFFECTOR_MANIFEST")
        if manifest.byte_length() > 0 and Path(manifest).exists():
            # Effector manifest from Fala: use input JSON from sibling input/request.json
            # or the manifest's input field if present.
            var input_dir = getenv("FALA_EFFECTOR_INPUT_DIR")
            var request_file = input_dir + "/request.json"
            if Path(request_file).exists():
                path = request_file
            else:
                # The manifest may carry the fusion payload directly under input.
                var man_text = Path(manifest).read_text()
                var man = parse_json(man_text)
                if man.is_object() and "input" in man.object():
                    var inp = man.object()["input"].copy()
                    if inp.is_object() and (
                        "profile" in inp.object()
                        or "candidates" in inp.object()
                        or "carriers" in inp.object()
                    ):
                        var out = fusion_step(to_string(inp))
                        _write_result(out)
                        return
                raise Error("splot: Fala manifest has no fusion request input")

    if path == "":
        raise Error("splot: request path required")

    var text = Path(path).read_text()
    var out = fusion_step(text)
    _write_result(out)
