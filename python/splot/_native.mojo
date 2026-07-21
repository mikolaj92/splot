"""Python extension: thin Mojo surface for Splot fusion.

Compile as a shared library (see ``_build.py``). JSON in / JSON out — same
contract as ``fusion_step`` / ``tools/splot_step.sh``. No dual engine.
"""

from std.os import abort
from std.python import PythonObject
from std.python.bindings import PythonModuleBuilder
from splot.adapters_fala import fusion_step


def fuse_json(request: PythonObject) raises -> PythonObject:
    """Run one fusion round. ``request`` is a JSON object string."""
    var s = String(py=request)
    var out = fusion_step(s)
    return PythonObject(out)


@export
def PyInit__native() abi("C") -> PythonObject:
    try:
        var m = PythonModuleBuilder("_native")
        m.def_function[fuse_json]("fuse_json")
        return m.finalize()
    except e:
        abort(String("splot._native init failed: ", e))
