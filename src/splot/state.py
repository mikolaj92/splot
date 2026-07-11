from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .models import SplotState, Belief, CandidateEvaluation, Decision, Evidence


def update_state(
    state: SplotState,
    decision: Decision,
    evaluations: list[CandidateEvaluation],
    now: str,
    stability_memory_updates: dict[str, Any] | None = None,
    feedback: dict[str, Any] | None = None,
    evidence: list[Evidence] | None = None,
    belief: Belief | None = None,
) -> SplotState:
    previous_selected = (state.previous_decision or {}).get("selected_candidate_id")
    updated = SplotState.from_dict(state.to_dict())
    updated.previous_decision = decision.to_dict()
    updated.last_decision_at = now
    if decision.selected_candidate_id and decision.selected_candidate_id != previous_selected:
        updated.last_switch_at = now
    if stability_memory_updates:
        for key, value in stability_memory_updates.items():
            if value is None:
                updated.stability_memory.pop(key, None)
            else:
                updated.stability_memory[key] = value
    updated.open_human_decisions = list(decision.required_human_inputs)
    if decision.status in {"conflict", "request_more_evidence"}:
        _remember_conflict(
            updated.unresolved_conflicts,
            {"decision_id": decision.id, "reason": decision.explanation},
            now,
        )
    updated.candidate_history.append(
        {
            "at": now,
            "decision_id": decision.id,
            "selected_candidate_id": decision.selected_candidate_id,
            "scores": {evaluation.candidate_id: evaluation.score for evaluation in evaluations},
        }
    )
    if evidence:
        updated.evidence_history.extend(
            {
                "at": now,
                "decision_id": decision.id,
                "evidence_id": item.id,
                "candidate_id": item.candidate_id,
                "supports": item.supports,
                "opposes": item.opposes,
                "strength": item.strength,
                "confidence": item.confidence,
                "reasons": item.reasons,
            }
            for item in evidence
        )
        updated.evidence_history = updated.evidence_history[-500:]
    if belief:
        updated.metadata["last_belief"] = belief.to_dict()
        updated.metadata["belief_history"] = belief.history
        for conflict in belief.conflicts:
            _remember_conflict(updated.unresolved_conflicts, conflict, now)
        updated.unresolved_conflicts = updated.unresolved_conflicts[-50:]
    if feedback:
        updated.metadata.setdefault("feedback", []).append(deepcopy(feedback))
        if feedback.get("state_updates"):
            updated.metadata.setdefault("feedback_state_updates", []).append(
                deepcopy(feedback["state_updates"])
            )
        for sid, val in (feedback.get("reliability_updates") or {}).items():
            updated.source_reliability[sid] = max(0.0, min(1.0, float(val)))
    return updated


def _remember_conflict(conflicts: list[dict[str, Any]], entry: dict[str, Any], now: str) -> None:
    key = _conflict_key(entry)
    if any(_conflict_key(item) == key for item in conflicts):
        return
    conflicts.append({**entry, "at": now})


def _conflict_key(conflict: dict[str, Any]) -> str:
    # "at" and "decision_id" vary per round; the rest identifies the conflict.
    payload = {key: value for key, value in conflict.items() if key not in {"at", "decision_id"}}
    return json.dumps(payload, sort_keys=True, default=str)


def load_state_file(path: str | Path | None) -> SplotState:
    if path is None:
        return SplotState()
    state_path = Path(path)
    if not state_path.exists():
        return SplotState()
    return SplotState.from_dict(json.loads(state_path.read_text(encoding="utf-8")))


def write_state_file(path: str | Path, state: SplotState) -> None:
    Path(path).write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
