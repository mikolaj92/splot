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
    Path(result_path).write_text(text)


def main() raises:
    var path = String("")
    var env_path = getenv("SPLOT_REQUEST_PATH")
    if env_path.byte_length() > 0:
        path = env_path
    else:
        var manifest = getenv("FALA_EFFECTOR_MANIFEST")
        if manifest.byte_length() > 0 and Path(manifest).exists():
            var input_dir = getenv("FALA_EFFECTOR_INPUT_DIR")
            var request_file = input_dir + "/request.json"
            if Path(request_file).exists():
                path = request_file
            else:
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
                raise Error("splot: request path required")

    if path == "":
        raise Error("splot: request path required")

    var text = Path(path).read_text()
    var out = fusion_step(text)
    _write_result(out)
