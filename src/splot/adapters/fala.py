from __future__ import annotations

from pathlib import Path
from typing import Any

from ..runtime import run_round
from .json_files import read_json, write_json


def arbitration_step(input_manifest: dict[str, Any]) -> dict[str, Any]:
    """Small Fala-shaped adapter without importing Fala.

    Expected keys: profile, observations, candidates, state, now, output_report.
    Real Fala projects can wrap this and turn the report into an Artifact/Event.
    """

    observations = _load_json_or_value(input_manifest.get("observations", []))
    candidates = _load_json_or_value(input_manifest.get("candidates", []))
    state = _load_json_or_value(input_manifest.get("state", {}))
    result = run_round(
        profile=input_manifest["profile"],
        observations=observations,
        candidates=candidates,
        previous_state=state,
        now=input_manifest.get("now"),
    )
    report = result.report.to_dict()
    output_report = input_manifest.get("output_report")
    if output_report:
        write_json(output_report, report)
    return {
        "decision": result.decision.to_dict(),
        "state": result.state.to_dict(),
        "decision_report": report,
        "decision_report_path": output_report,
    }


def _load_json_or_value(value: Any) -> Any:
    if isinstance(value, (str, Path)):
        return read_json(value)
    return value

