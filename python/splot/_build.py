"""Compile ``_native.mojo`` against the Mojo engine with correct -I paths."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

_PACKAGE_DIR = Path(__file__).resolve().parent
_NATIVE_MOJO = _PACKAGE_DIR / "_native.mojo"
_CACHE_DIR_NAME = "__mojocache__"


def repo_root() -> Path:
    """Splot checkout / install root (contains ``mojo/splot`` + ``vendor/EmberJson``)."""
    env = os.environ.get("SPLOT_HOME")
    if env:
        return Path(env).expanduser().resolve()
    for candidate in (_PACKAGE_DIR.parents[2], _PACKAGE_DIR.parent, Path.cwd()):
        if (candidate / "mojo" / "splot").is_dir() and (
            candidate / "vendor" / "EmberJson"
        ).is_dir():
            return candidate.resolve()
    raise RuntimeError(
        "Cannot locate Splot Mojo sources. Set SPLOT_HOME to the Splot checkout "
        "(must contain mojo/splot and vendor/EmberJson), or develop from a git tree."
    )


def _source_hash(root: Path) -> str:
    paths = sorted(
        list((_PACKAGE_DIR).glob("*.mojo"))
        + list((root / "mojo" / "splot").rglob("*.mojo"))
        + list((root / "vendor" / "EmberJson").rglob("*.mojo"))
    )
    h = hashlib.sha256()
    for p in paths:
        h.update(str(p.relative_to(root) if p.is_relative_to(root) else p.name).encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _mojo_env() -> dict[str, str]:
    env = dict(os.environ)
    # Prefer Modular SDK layout when present (mojo pip/conda package).
    try:
        from mojo._package_root import get_package_root  # type: ignore[import-not-found]
        from mojo.run import _sdk_default_env  # type: ignore[import-not-found]

        root = get_package_root()
        if root is not None:
            env = {**_sdk_default_env(), **env}
    except Exception:
        pass
    return env


def _mojo_bin(env: dict[str, str]) -> str:
    for key in ("MODULAR_MOJO_MAX_DRIVER_PATH", "MOJO"):
        p = env.get(key)
        if p and Path(p).is_file():
            return p
    found = shutil.which("mojo", path=env.get("PATH"))
    if found:
        return found
    # Sibling Fala pixi (common OSS layout)
    fala = Path.home() / "Developer" / "OSS" / "Fala" / ".pixi" / "envs" / "default" / "bin" / "mojo"
    if fala.is_file():
        return str(fala)
    raise RuntimeError(
        "mojo executable not found. Install Mojo (pixi/conda modular) or set PATH."
    )


def ensure_native() -> ModuleType:
    """Build (if needed) and load the ``_native`` extension module."""
    if not _NATIVE_MOJO.is_file():
        raise RuntimeError(f"missing {_NATIVE_MOJO}")

    root = repo_root()
    digest = _source_hash(root)
    cache_dir = _PACKAGE_DIR / _CACHE_DIR_NAME
    cache_dir.mkdir(exist_ok=True)
    so_path = cache_dir / f"_native.hash-{digest}.so"

    if not so_path.is_file():
        # Drop stale artifacts
        for old in cache_dir.glob("_native.hash-*.so"):
            old.unlink(missing_ok=True)
        env = _mojo_env()
        mojo = _mojo_bin(env)
        cmd = [
            mojo,
            "build",
            str(_NATIVE_MOJO),
            "--emit",
            "shared-lib",
            "-I",
            str(root / "mojo"),
            "-I",
            str(root / "vendor" / "EmberJson"),
            "-o",
            str(so_path),
        ]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                "splot native build failed:\n"
                + (proc.stderr or proc.stdout or f"exit {proc.returncode}")
            )

    spec = importlib.util.spec_from_file_location("splot._native", so_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load extension {so_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["splot._native"] = mod
    spec.loader.exec_module(mod)
    return mod
