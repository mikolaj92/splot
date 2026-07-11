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
    if belief:
        updated.metadata["last_belief"] = belief.to_dict()
        updated.metadata["belief_history"] = belief.history
    if feedback:
        updated.metadata.setdefault("feedback", []).append(deepcopy(feedback))
        if feedback.get("state_updates"):
            updated.metadata.setdefault("feedback_state_updates", []).append(
                deepcopy(feedback["state_updates"])
            )
        for sid, val in (feedback.get("reliability_updates") or {}).items():
            updated.source_reliability[sid] = max(0.0, min(1.0, float(val)))
    return updated

def load_state_file(path: str | Path | None) -> SplotState:
    if path is None:
        return SplotState()
    state_path = Path(path)
    if not state_path.exists():
        return SplotState()
    return SplotState.from_dict(json.loads(state_path.read_text(encoding="utf-8")))

def write_state_file(path: str | Path, state: SplotState) -> None:
    Path(path).write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
