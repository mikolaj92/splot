from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SPLOT_VERSION = "0.1.0"
PROFILE_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
STATE_SCHEMA_VERSION = 1


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def digest_profile(profile_raw: dict[str, Any], profile_path: Path | None = None) -> str:
    payload: dict[str, Any] = {"profile": profile_raw}
    if profile_path is not None and profile_path.exists():
        sidecars: dict[str, str] = {}
        for path in sorted(profile_path.glob("*.md")):
            sidecars[path.name] = path.read_text(encoding="utf-8")
        payload["sidecars"] = sidecars
    return digest_value(payload)


def digest_round_input(
    observations: list[Any],
    candidates: list[Any],
    previous_state: dict[str, Any],
    feedback: dict[str, Any] | None,
) -> str:
    return digest_value(
        {
            "observations": observations,
            "candidates": candidates,
            "previous_state": previous_state,
            "feedback": feedback or {},
        }
    )
