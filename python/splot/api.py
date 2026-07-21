"""Thin Python API over the Mojo fusion engine.

Happy path only: ``load_profile`` + ``fuse``. All logic lives in ``mojo/splot``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from splot._build import ensure_native

ProfileLike = str | Path | Mapping[str, Any]
CandidateLike = Mapping[str, Any]
StateLike = Mapping[str, Any] | None
ReadersLike = Mapping[str, Any] | None


def load_profile(path: str | Path) -> str:
    """Return an absolute profile path for ``fuse`` (TOML only)."""
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"splot profile not found: {p}")
    if p.suffix.lower() in {".yaml", ".yml"}:
        raise ValueError("splot: YAML profiles are not supported; use profile.toml")
    return str(p.resolve())


def fuse(
    *,
    profile: ProfileLike,
    candidates: Sequence[CandidateLike],
    state: StateLike = None,
    readers: ReadersLike = None,
    now: str | None = None,
    include_evaluations: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """One fusion round. Returns ``(decision, new_state)`` as plain dicts."""
    if not candidates:
        raise ValueError("splot.fuse: candidates must be non-empty")

    request: dict[str, Any] = {
        "candidates": [dict(c) for c in candidates],
    }
    if isinstance(profile, Mapping):
        request["profile_object"] = dict(profile)
    else:
        p = Path(profile)
        request["profile"] = load_profile(p) if p.is_file() else str(profile)

    if state is not None:
        request["state"] = dict(state)
    if readers is not None:
        request["readers"] = dict(readers)
    if now is not None:
        request["now"] = now
    if include_evaluations:
        request["include_evaluations"] = True

    envelope = fuse_json(request)
    decision = envelope.get("decision")
    new_state = envelope.get("state")
    if not isinstance(decision, dict) or not isinstance(new_state, dict):
        raise RuntimeError("splot: missing decision/state in fusion result")
    return decision, new_state


def fuse_json(request_json: str | Mapping[str, Any]) -> dict[str, Any]:
    """Low-level: same JSON envelope as ``tools/splot_step.sh`` / ``fusion_step``."""
    if isinstance(request_json, Mapping):
        payload = json.dumps(request_json)
    else:
        payload = request_json
    native = ensure_native()
    raw = native.fuse_json(payload)
    if not isinstance(raw, str):
        raw = str(raw)
    out = json.loads(raw)
    if not isinstance(out, dict):
        raise RuntimeError("splot: fuse_json result is not an object")
    return out
