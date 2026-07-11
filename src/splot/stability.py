from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import SplotState, Candidate, CandidateEvaluation, Decision, new_id
from .scoring import evaluation_for


def apply_stability(
    profile: dict[str, Any],
    candidates: list[Candidate],
    evaluations: list[CandidateEvaluation],
    state: SplotState,
    decision: Decision,
    now: str,
) -> tuple[Decision, dict[str, Any], dict[str, Any]]:
    config = profile.get("stability") or {}
    policy = str(config.get("policy", "none"))
    previous = state.previous_decision or {}
    previous_candidate_id = previous.get("selected_candidate_id")
    proposed_candidate_id = decision.selected_candidate_id
    analysis: dict[str, Any] = {
        "policy": policy,
        "previous_candidate_id": previous_candidate_id,
        "proposed_candidate_id": proposed_candidate_id,
        "decision": "accepted",
    }

    if policy == "none" or decision.status not in {"selected", "routed"}:
        return decision, analysis, {}
    if not previous_candidate_id or proposed_candidate_id == previous_candidate_id:
        analysis["decision"] = "same_or_first_candidate"
        return decision, analysis, _clear_pending(policy)

    proposed_eval = evaluation_for(evaluations, proposed_candidate_id)
    previous_eval = evaluation_for(evaluations, previous_candidate_id)
    proposed_score = proposed_eval.score if proposed_eval else decision.confidence
    previous_score = previous_eval.score if previous_eval else float(previous.get("confidence", 0.0))
    switching_cost = _candidate_switching_cost(candidates, proposed_candidate_id) + float(
        config.get("switching_cost", 0.0)
    )
    score_margin = proposed_score - previous_score - switching_cost
    analysis.update(
        {
            "previous_score": previous_score,
            "proposed_score": proposed_score,
            "switching_cost": switching_cost,
            "score_margin": score_margin,
        }
    )

    min_hold_ms = float(config.get("min_hold_ms", config.get("duration_ms", 0.0)))
    if min_hold_ms and not _elapsed(now, state.last_decision_at, min_hold_ms):
        return _keep_previous(
            profile, state, previous_score, now, f"min_hold_ms has not passed ({min_hold_ms:.0f}ms)"
        ), _analysis(analysis, "keep_previous_min_hold"), {}

    cooldown_ms = float(config.get("cooldown_ms", 0.0))
    if cooldown_ms and not _elapsed(now, state.last_switch_at, cooldown_ms):
        return _keep_previous(
            profile, state, previous_score, now, f"cooldown has not passed ({cooldown_ms:.0f}ms)"
        ), _analysis(analysis, "keep_previous_cooldown"), {}

    if policy == "debounce":
        required_rounds = int(config.get("rounds", 2))
        memory = dict(state.stability_memory)
        count = int(memory.get("pending_count", 0)) + 1 if memory.get("pending_candidate_id") == proposed_candidate_id else 1
        update = {"pending_candidate_id": proposed_candidate_id, "pending_count": count, "pending_since": now}
        analysis["pending_count"] = count
        analysis["required_rounds"] = required_rounds
        if count < required_rounds:
            return _keep_previous(
                profile, state, previous_score, now, f"debounce needs {required_rounds} rounds"
            ), _analysis(analysis, "keep_previous_debounce"), update
        return decision, _analysis(analysis, "debounce_passed"), {"pending_candidate_id": None, "pending_count": 0}

    if policy == "hold_then_recheck":
        hold_ms = float(config.get("hold_ms", config.get("duration_ms", 0.0)))
        memory = dict(state.stability_memory)
        same_pending = memory.get("pending_candidate_id") == proposed_candidate_id
        pending_since = memory.get("pending_since") if same_pending else now
        update = {"pending_candidate_id": proposed_candidate_id, "pending_since": pending_since}
        analysis["hold_ms"] = hold_ms
        analysis["pending_since"] = pending_since
        if hold_ms and not _elapsed(now, pending_since, hold_ms):
            return _keep_previous(
                profile, state, previous_score, now, f"hold_then_recheck waiting {hold_ms:.0f}ms"
            ), _analysis(analysis, "keep_previous_hold_then_recheck"), update
        return decision, _analysis(analysis, "hold_then_recheck_passed"), {"pending_candidate_id": None}

    min_improvement = float(config.get("min_improvement", 0.0))
    if policy in {"hysteresis", "prefer_current_when_close", "switching_cost"} and score_margin < min_improvement:
        return _keep_previous(
            profile,
            state,
            previous_score,
            now,
            f"score margin {score_margin:.3f} < min_improvement {min_improvement:.3f}",
        ), _analysis(analysis, "keep_previous_hysteresis"), {}

    analysis["min_improvement"] = min_improvement
    return decision, _analysis(analysis, "switch_allowed"), _clear_pending(policy)


def _keep_previous(
    profile: dict[str, Any],
    state: SplotState,
    confidence: float,
    now: str,
    reason: str,
) -> Decision:
    previous = state.previous_decision or {}
    previous_id = previous.get("selected_candidate_id")
    return Decision(
        id=new_id("decision"),
        status="kept_previous",
        objective_id=str((profile.get("objective") or {}).get("id", profile.get("id", ""))),
        selected_candidate_id=previous_id,
        selected_candidate_ids=[previous_id] if previous_id else [],
        previous_decision_id=previous.get("id"),
        action=previous.get("action"),
        confidence=confidence,
        uncertainty=max(0.0, min(1.0, 1.0 - confidence)),
        policy_reason=reason,
        explanation=f"kept previous candidate {previous_id}: {reason}",
        created_at=now,
        metadata={
            "selected_source_ids": list((previous.get("metadata") or {}).get("selected_source_ids") or [])
        },
    )


def _analysis(analysis: dict[str, Any], decision: str) -> dict[str, Any]:
    updated = dict(analysis)
    updated["decision"] = decision
    return updated


def _candidate_switching_cost(candidates: list[Candidate], candidate_id: str | None) -> float:
    for candidate in candidates:
        if candidate.id == candidate_id:
            return candidate.switching_cost
    return 0.0


def _elapsed(now: str, then: str | None, required_ms: float) -> bool:
    if not then:
        return True
    return (_parse_time(now) - _parse_time(then)).total_seconds() * 1000 >= required_ms


def _parse_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _clear_pending(policy: str) -> dict[str, Any]:
    if policy in {"debounce", "hold_then_recheck"}:
        return {"pending_candidate_id": None, "pending_count": 0, "pending_since": None}
    return {}

