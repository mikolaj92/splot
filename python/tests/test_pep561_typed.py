"""PEP 561: Typing :: Typed means the installed package ships py.typed."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_source_tree_has_py_typed_marker() -> None:
    assert (ROOT / "python" / "splot" / "py.typed").is_file()


def test_wheel_ships_py_typed_marker(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist)],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    wheels = list(dist.glob("splot-*.whl"))
    assert len(wheels) == 1, wheels
    with zipfile.ZipFile(wheels[0]) as zf:
        names = zf.namelist()
    assert "splot/py.typed" in names
