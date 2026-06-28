from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from ..runtime import run_round
from .json_files import read_json, write_json


def arbitration_step(input_manifest: dict[str, Any]) -> dict[str, Any]:
    """Small Fala-shaped adapter without importing Fala.

    Expected keys: profile, observations, candidates, state, now, output_report.
    Real Fala projects can wrap the returned artifacts/events/gates.
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
    output_state = input_manifest.get("output_state")
    if output_state:
        write_json(output_state, result.state.to_dict())
    events = [
        {
            "type": "splot.round_completed",
            "decision_id": result.decision.id,
            "status": result.decision.status,
        }
    ]
    gates = []
    if result.decision.required_human_inputs:
        gates.append(
            {
                "type": "human_decision",
                "decision_id": result.decision.id,
                "inputs": result.decision.required_human_inputs,
            }
        )
    return {
        "decision": result.decision.to_dict(),
        "state": result.state.to_dict(),
        "decision_report": report,
        "decision_report_path": output_report,
        "state_path": output_state,
        "artifacts": [{"kind": "decision_report", "path": output_report, "payload": report}],
        "events": events,
        "gates": gates,
    }


def process_runtime_step(context: dict[str, Any]) -> dict[str, Any]:
    """Run Splot as a Fala process-runtime stdio step.

    Reads profile/observations/candidates/state/feedback from `context["config"]`,
    `context["input"]["values"]`, or `context["input"]["values"]["initial"]`.
    Returns a Fala-compatible ProcessOutput dict.
    """

    payload = _process_payload(context)
    result = run_round(
        profile=payload["profile"],
        observations=payload.get("observations") or [],
        candidates=payload.get("candidates") or [],
        previous_state=payload.get("state") or {},
        now=payload.get("now"),
        feedback=payload.get("feedback"),
    )
    report = result.report.to_dict()
    report_path = _write_process_report(context, report)
    state_path = _write_process_state(context, result.state.to_dict())
    _emit_process_event(
        "splot.decision_committed",
        status="completed",
        data={
            "decision_id": result.decision.id,
            "decision_status": result.decision.status,
            "selected_candidate_id": result.decision.selected_candidate_id,
        },
    )
    if result.decision.required_human_inputs:
        _emit_process_event(
            "splot.human_decision_required",
            status="waiting",
            data={
                "decision_id": result.decision.id,
                "decision_status": result.decision.status,
                "inputs": result.decision.required_human_inputs,
            },
        )

    values = {
        "decision": result.decision.to_dict(),
        "state": result.state.to_dict(),
        "decision_report": report,
        "human_decision_required": bool(result.decision.required_human_inputs),
        "human_decisions": result.decision.required_human_inputs,
    }
    artifacts = [
        _artifact_ref("splot_decision_report", report_path),
        _artifact_ref("splot_state", state_path),
    ]
    metadata = {
        "splot": {
            "profile_id": report["profile_id"],
            "round_id": report["round_id"],
            "decision_id": result.decision.id,
            "status": result.decision.status,
        }
    }
    return _fala_output(values=values, artifacts=artifacts, metadata=metadata)


def run_stdio() -> int:
    """Fala stdio entrypoint."""

    try:
        from fala.sdk import run_stdio as fala_run_stdio  # type: ignore
    except ModuleNotFoundError:
        import sys

        try:
            context = json.loads(sys.stdin.read() or "{}")
            print(json.dumps(process_runtime_step(context), ensure_ascii=False))
            return 0
        except Exception as exc:  # pragma: no cover - same behavior as fala.sdk.run_stdio
            print(str(exc), file=sys.stderr)
            return 1
    return fala_run_stdio(process_runtime_step)


def _load_json_or_value(value: Any) -> Any:
    if isinstance(value, (str, Path)):
        return read_json(value)
    return value


def _process_payload(context: dict[str, Any]) -> dict[str, Any]:
    config = dict(context.get("config") or {})
    values = dict((context.get("input") or {}).get("values") or {})
    initial = dict(values.get("initial") or {})
    merged = {**initial, **values, **config}
    if "profile" not in merged:
        raise ValueError("Splot Fala step requires profile in config or input values")
    return merged


def _artifact_root(context: dict[str, Any]) -> Path:
    try:
        from fala.sdk import artifact_root  # type: ignore

        return artifact_root(context, str(context.get("process_id") or "splot"))
    except ModuleNotFoundError:
        runtime_dir = os.environ.get("PROCESS_RUNTIME_ARTIFACT_DIR")
        if runtime_dir:
            root = Path(runtime_dir)
        else:
            root = Path(".flow-runs/process-artifacts") / str(context.get("run_id") or "run") / str(
                context.get("document_id") or "document"
            ) / str(context.get("process_id") or "splot")
        root.mkdir(parents=True, exist_ok=True)
        return root


def _write_process_report(context: dict[str, Any], report: dict[str, Any]) -> Path:
    path = _artifact_root(context) / "decision_report.json"
    write_json(path, report)
    return path


def _write_process_state(context: dict[str, Any], state: dict[str, Any]) -> Path:
    path = _artifact_root(context) / "state.json"
    write_json(path, state)
    return path


def _artifact_ref(kind: str, path: Path) -> dict[str, Any]:
    try:
        from fala.sdk import artifact  # type: ignore

        return artifact(kind, path)
    except ModuleNotFoundError:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "kind": kind,
            "uri": path.resolve().as_uri(),
            "metadata": {
                "sha256": digest,
                "size_bytes": path.stat().st_size,
                "filename": path.name,
            },
        }


def _fala_output(
    *,
    values: dict[str, Any],
    artifacts: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    try:
        from fala.sdk import output  # type: ignore

        return output(values=values, artifacts=artifacts, metadata=metadata)
    except ModuleNotFoundError:
        return {
            "values": values,
            "artifacts": artifacts,
            "metadata": metadata,
            "output_documents": [],
            "spawn_documents": [],
            "stream_chunks": [],
        }


def _emit_process_event(event_type: str, *, status: str, data: dict[str, Any]) -> None:
    try:
        from fala.sdk import emit_event  # type: ignore

        emit_event(event_type, status=status, data=data)
    except ModuleNotFoundError:
        return
