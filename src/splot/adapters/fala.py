"""Fala-shaped adapter for the Splot arbitration runtime.

Splot stays standalone: nothing here imports Fala at module load time. When
Fala is installed its ``fala.sdk`` helpers are used; otherwise identical,
import-free fallbacks run so the same descriptors are produced without Fala.

Boundary (see ``docs/FALA_INTEGRATION.md``):

- Fala owns the information-flow runtime: Carrier, Observation, Artifact, Event,
  Process, Run, Gate, Projection, SQLite persistence, filesystem artifacts.
- Splot owns arbitration: waves/observations -> evidence -> belief/state ->
  candidates -> arbitration -> stabilization -> decision -> feedback/trace.

Archetype mapping:

- Fala Carrier      -> Splot Wave / candidate source
- Fala Observation  -> Splot Observation
- Fala Artifact     -> evidence snapshot / ``decision_report``
- Fala Event        -> ``splot.decision_committed``
- Fala Gate         -> human decision requirement
- Fala Projection   -> decision history / current arbitration state
- Fala RuntimeRef   -> another wave / runtime source
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from ..models import Candidate, Observation
from ..runtime import RoundResult, run_round
from .json_files import read_json, write_json

DECISION_COMMITTED_EVENT = "splot.decision_committed"
HUMAN_DECISION_GATE = "splot.human_decision"
DECISION_OBSERVATION = "splot.decision"
DECISION_REPORT_ARTIFACT = "splot.decision_report"
STATE_ARTIFACT = "splot.state"

_OBSERVATION_FIELDS = {
    "id",
    "wave_id",
    "observed_at",
    "window_start",
    "window_end",
    "values",
    "confidence",
    "metadata",
}


# --- Fala -> Splot input mapping --------------------------------------------


def carrier_to_candidate(carrier: dict[str, Any]) -> dict[str, Any]:
    """Map a Fala carrier to a Splot candidate source."""
    carrier = dict(carrier)
    carrier_id = str(carrier.get("id") or carrier.get("carrier_id") or "carrier")
    cand_kind = str(carrier.get("carrier_type") or carrier.get("kind") or "generic")
    meta = dict(carrier.get("metadata") or {})
    if "kind" not in meta:
        meta["kind"] = cand_kind
    return {
        "id": carrier_id,
        "source_ids": [carrier_id],
        "payload": dict(carrier.get("payload") or {}),
        "metadata": meta,
    }


def fala_observation_to_splot(observation: dict[str, Any], index: int = 0) -> dict[str, Any]:
    """Map a Fala observation (``carrier_id``, ``kind``, ``values``) to Splot."""
    data = dict(observation)
    if "carrier_id" in data and "wave_id" not in data:
        data["wave_id"] = data.get("carrier_id")
    data["id"] = str(data.get("id") or f"observation_{index}")
    obs_kind = data.pop("kind", None) or data.get("carrier_type")
    filtered = {key: value for key, value in data.items() if key in _OBSERVATION_FIELDS}
    if obs_kind:
        filtered.setdefault("metadata", {})
        filtered["metadata"] = dict(filtered.get("metadata") or {})
        filtered["metadata"].setdefault("kind", obs_kind)
    return filtered

def _as_observation(value: Any, index: int) -> Observation:
    if isinstance(value, Observation):
        return value
    return Observation.from_dict(fala_observation_to_splot(dict(value), index))


def _as_candidate(value: Any) -> Candidate:
    if isinstance(value, Candidate):
        return value
    return Candidate.from_dict(dict(value))


def _prepare_observations(payload: dict[str, Any]) -> list[Observation]:
    raw = _load_json_or_value(payload.get("observations", [])) or []
    return [_as_observation(item, index) for index, item in enumerate(raw)]


def _prepare_candidates(payload: dict[str, Any]) -> list[Candidate]:
    candidates = _load_json_or_value(payload.get("candidates", [])) or []
    if not candidates:
        carriers = _load_json_or_value(payload.get("carriers", [])) or []
        candidates = [carrier_to_candidate(dict(carrier)) for carrier in carriers]
    return [_as_candidate(item) for item in candidates]

def _fala_observations(observations: list[Observation], result: RoundResult) -> list[dict[str, Any]]:
    """Fala-shaped observations: passed-through readings plus the decision."""
    out: list[dict[str, Any]] = [
        {
            "kind": (observation.metadata or {}).get("kind", "generic"),
            "carrier_id": observation.wave_id,
            "values": observation.values,
            "confidence": observation.confidence,
            "metadata": observation.metadata,
        }
        for observation in observations
    ]
    decision = result.decision
    out.append(
        {
            "kind": DECISION_OBSERVATION,
            "values": {
                "status": decision.status,
                "selected_candidate_id": decision.selected_candidate_id,
                "selected_candidate_ids": list(decision.selected_candidate_ids),
                "confidence": decision.confidence,
                "uncertainty": decision.uncertainty,
            },
            "metadata": {"round_id": result.report.round_id, "decision_id": decision.id},
        }
    )
    return out


def _fala_events(result: RoundResult) -> list[dict[str, Any]]:
    decision = result.decision
    return [
        {
            "type": DECISION_COMMITTED_EVENT,
            "decision_id": decision.id,
            "status": decision.status,
            "selected_candidate_id": decision.selected_candidate_id,
        }
    ]


def _fala_gates(result: RoundResult) -> list[dict[str, Any]]:
    decision = result.decision
    if not decision.required_human_inputs:
        return []
    return [
        {
            "kind": HUMAN_DECISION_GATE,
            "status": "open",
            "decision_id": decision.id,
            "values": {"inputs": list(decision.required_human_inputs)},
        }
    ]


def arbitration_step(input_manifest: dict[str, Any]) -> dict[str, Any]:
    """Import-free, host-agnostic Fala-shaped arbitration step.

    Accepts a manifest with ``profile`` plus either Splot ``candidates`` or Fala
    ``carriers``, optional ``observations`` (Splot or Fala shaped), ``state``,
    ``feedback``, ``now``, and optional ``output_report`` / ``output_state``
    paths. Returns descriptors any host (Fala or not) can commit: ``decision``,
    ``state``, ``decision_report``, ``observations``, ``artifacts``, ``events``,
    and human-decision ``gates``.
    """

    payload = dict(input_manifest)
    observations = _prepare_observations(payload)
    result = run_round(
        profile=payload["profile"],
        observations=observations,
        candidates=_prepare_candidates(payload),
        previous_state=_load_json_or_value(payload.get("state", {})) or {},
        now=payload.get("now"),
        feedback=payload.get("feedback"),
    )
    report = result.report.to_dict()
    output_report = payload.get("output_report")
    if output_report:
        write_json(output_report, report)
    output_state = payload.get("output_state")
    if output_state:
        write_json(output_state, result.state.to_dict())
    return {
        "decision": result.decision.to_dict(),
        "state": result.state.to_dict(),
        "decision_report": report,
        "decision_report_path": output_report,
        "state_path": output_state,
        "observations": _fala_observations(observations, result),
        "artifacts": [
            {"kind": DECISION_REPORT_ARTIFACT, "path": output_report, "payload": report}
        ],
        "events": _fala_events(result),
        "gates": _fala_gates(result),
    }


def process_runtime_step(context: dict[str, Any]) -> dict[str, Any]:
    """Run Splot as a Fala process step and return a Fala step output.

    Reads ``profile`` from ``context["config"]`` and arbitration inputs from
    ``context["input"]["needs"]`` (Fala) or ``context["input"]["values"]``.
    Returns the Fala ``{values, observations, artifacts, metadata}`` output; the
    ``decision_report`` and ``state`` are written as artifacts and a
    ``splot.decision_committed`` event plus any human-decision gate are surfaced
    in ``values`` for the runtime to commit.
    """

    payload = _process_payload(context)
    observations = _prepare_observations(payload)
    result = run_round(
        profile=payload["profile"],
        observations=observations,
        candidates=_prepare_candidates(payload),
        previous_state=payload.get("state") or {},
        now=payload.get("now"),
        feedback=payload.get("feedback"),
    )
    report = result.report.to_dict()
    report_path = _write_process_report(context, report)
    state_path = _write_process_state(context, result.state.to_dict())
    gates = _fala_gates(result)
    values = {
        "decision": result.decision.to_dict(),
        "state": result.state.to_dict(),
        "decision_report": report,
        "human_decision_required": bool(gates),
        "human_decisions": list(result.decision.required_human_inputs),
        "events": _fala_events(result),
        "gates": gates,
    }
    artifacts = [
        _artifact_ref(DECISION_REPORT_ARTIFACT, report_path),
        _artifact_ref(STATE_ARTIFACT, state_path),
    ]
    metadata = {
        "splot": {
            "profile_id": report["profile_id"],
            "round_id": report["round_id"],
            "decision_id": result.decision.id,
            "status": result.decision.status,
        }
    }
    return _fala_output(
        values=values,
        observations=_fala_observations(observations, result),
        artifacts=artifacts,
        metadata=metadata,
    )


def run_stdio() -> int:
    """``splot-fala-step`` entrypoint.

    With Fala installed, run as a manifest step (``FALA_STEP_MANIFEST`` ->
    ``FALA_STEP_OUTPUT_DIR/result.json``). Standalone, read a JSON context from
    stdin and print the Fala step output to stdout.
    """

    try:
        from fala.sdk import run_manifest_step  # type: ignore
    except ModuleNotFoundError:
        try:
            context = json.loads(sys.stdin.read() or "{}")
            print(json.dumps(process_runtime_step(context), ensure_ascii=False))
            return 0
        except Exception as exc:  # pragma: no cover - defensive stdio guard
            print(str(exc), file=sys.stderr)
            return 1
    return run_manifest_step(process_runtime_step)


# --- helpers ----------------------------------------------------------------


def _load_json_or_value(value: Any) -> Any:
    if isinstance(value, (str, Path)):
        return read_json(value)
    return value


def _process_payload(context: dict[str, Any]) -> dict[str, Any]:
    input_block = dict(context.get("input") or {})
    values = dict(input_block.get("values") or {})
    initial = dict(values.get("initial") or {})
    needs = dict(input_block.get("needs") or {})
    input_scalars = {
        key: value
        for key, value in input_block.items()
        if key not in {"values", "needs"}
    }
    config = dict(context.get("config") or {})
    merged = {**context, **input_scalars, **needs, **initial, **values, **config}
    if "profile" not in merged:
        raise ValueError("Splot Fala step requires profile in config or input values")
    return merged


def _artifact_root(context: dict[str, Any]) -> Path:
    # FALA_STEP_OUTPUT_DIR is intentionally not used as the artifact root: under a
    # real Fala worker it is an ephemeral per-step temp dir that is removed once
    # result.json is read back, so artifacts written there would leave dangling
    # file:// URIs in the committed process output. Write to a durable location.
    configured = os.environ.get("PROCESS_RUNTIME_ARTIFACT_DIR")
    if configured:
        root = Path(configured)
        root.mkdir(parents=True, exist_ok=True)
        return root
    root = (
        Path(".flow-runs/process-artifacts")
        / str(context.get("run_id") or "run")
        / str(context.get("document_id") or context.get("carrier_id") or "document")
        / str(context.get("process_id") or "splot")
    )
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
    path = Path(path)
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
    observations: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    try:
        from fala.sdk import output  # type: ignore
    except ModuleNotFoundError:
        return {
            "values": values,
            "observations": observations,
            "artifacts": artifacts,
            "metadata": metadata,
        }
    return output(
        values=values,
        observations=observations,
        artifacts=artifacts,
        metadata=metadata,
    )
