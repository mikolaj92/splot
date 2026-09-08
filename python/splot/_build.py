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


_EMBER_JSON_REV = "951f4ef28d0c2748a30b2c5e43e139411ccca5ef"


def repo_root() -> Path:
    """Splot checkout / install root (contains ``mojo/splot``)."""
    env = os.environ.get("SPLOT_HOME")
    if env:
        return Path(env).expanduser().resolve()
    for candidate in (_PACKAGE_DIR.parents[2], _PACKAGE_DIR.parent, Path.cwd()):
        if (candidate / "mojo" / "splot").is_dir():
            return candidate.resolve()
    raise RuntimeError(
        "Cannot locate Splot Mojo sources. Set SPLOT_HOME to the Splot checkout "
        "(must contain mojo/splot), or develop from a git tree."
    )


def _ensure_ember_json(root: Path) -> Path:
    vendor = root / "vendor" / "EmberJson"
    setup = root / "tools" / "setup_ember_json.sh"
    if not setup.is_file():
        raise RuntimeError(f"missing EmberJson setup script: {setup}")
    proc = subprocess.run(["sh", str(setup)], cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "splot EmberJson setup failed:\n" + (proc.stderr or proc.stdout or "")
        )
    if not (vendor / "emberjson" / "__init__.mojo").is_file():
        raise RuntimeError(f"EmberJson sources missing after setup: {vendor}")
    return vendor


def _source_hash(root: Path) -> str:
    paths = sorted(
        list((_PACKAGE_DIR).glob("*.mojo"))
        + list((root / "mojo" / "splot").rglob("*.mojo"))
        + list((root / "patches").glob("emberjson-*.patch"))
    )
    h = hashlib.sha256()
    h.update(_EMBER_JSON_REV.encode())
    for p in paths:
        h.update(str(p.relative_to(root) if p.is_relative_to(root) else p.name).encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _mojo_env() -> dict[str, str]:
    """Env so ``mojo build`` can find ``std`` and the driver."""
    env = dict(os.environ)
    local_pixi = repo_root() / ".pixi" / "envs" / "default"
    candidates = [
        local_pixi,
        Path(env["CONDA_PREFIX"]) if env.get("CONDA_PREFIX") else None,
        Path.home() / "Developer" / "splot" / ".pixi" / "envs" / "default",
        Path.home() / "Developer" / "OSS" / "Splot" / ".pixi" / "envs" / "default",
        Path.home() / "Developer" / "OSS" / "Fala" / ".pixi" / "envs" / "default",
    ]
    for root in candidates:
        if root is None:
            continue
        mojo_bin = root / "bin" / "mojo"
        import_path = root / "lib" / "mojo"
        if mojo_bin.is_file() and import_path.is_dir():
            env["MODULAR_MAX_PACKAGE_ROOT"] = str(root)
            env["MODULAR_MOJO_MAX_PACKAGE_ROOT"] = str(root)
            env["MODULAR_MOJO_MAX_DRIVER_PATH"] = str(mojo_bin)
            env["MODULAR_MOJO_MAX_IMPORT_PATH"] = str(import_path)
            env["PATH"] = str(root / "bin") + os.pathsep + env.get("PATH", "")
            return env
    try:
        from mojo._package_root import get_package_root  # type: ignore[import-not-found]
        from mojo.run import _sdk_default_env  # type: ignore[import-not-found]

        package_root = get_package_root()
        if package_root is not None:
            return {**_sdk_default_env(), **env}
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
    ember_json = _ensure_ember_json(root)
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
            str(ember_json),
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
