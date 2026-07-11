from __future__ import annotations

from typing import Any

from .models import SplotState, Candidate, CandidateEvaluation, Decision, new_id
from .scoring import evaluation_for


UNCERTAINTY_STATUS = {
    "fallback": "fallback",
    "no_candidate": "no_candidate",
    "human_decision": "needs_human_decision",
    "request_more_evidence": "request_more_evidence",
    "conflict": "conflict",
    "rejected_all": "rejected_all",
}


def decide_from_evaluations(
    profile: dict[str, Any],
    candidates: list[Candidate],
    evaluations: list[CandidateEvaluation],
    state: SplotState,
    now: str,
) -> Decision:
    objective_id = str((profile.get("objective") or {}).get("id", profile.get("id", "")))
    previous = state.previous_decision or {}
    previous_id = previous.get("selected_candidate_id")
    decision_config = profile.get("decision") or {}
    policy = str(decision_config.get("policy", "constrained_weighted_score"))
    eligible = list(evaluations) if policy == "weighted_score" else [item for item in evaluations if item.eligible]
    rejected = [
        {"candidate_id": item.candidate_id, "reasons": item.rejected_reasons}
        for item in evaluations
        if item.rejected_reasons
    ]

    if not evaluations:
        return _uncertain_decision(
            profile, "when_no_candidate", objective_id, previous, now, rejected, "no candidates"
        )
    if not eligible:
        return _uncertain_decision(
            profile,
            "when_constraints_block_all",
            objective_id,
            previous,
            now,
            rejected,
            "all candidates blocked",
        )

    ranked = sorted(eligible, key=lambda item: item.score, reverse=True)
    best = ranked[0]
    close_margin = float(decision_config.get("close_margin", 0.05))
    second = ranked[1] if len(ranked) > 1 else None
    margin = best.score - second.score if second else 1.0

    previous_eval = evaluation_for(evaluations, previous_id)
    if (
        decision_config.get("tie_breaker") == "keep_current"
        and previous_eval
        and previous_eval.eligible
        and best.candidate_id != previous_id
        and best.score - previous_eval.score <= close_margin
    ):
        return _keep_previous(objective_id, previous, now, previous_eval.score, "tie_breaker_keep_current")

    if (policy == "require_human_when_ambiguous" or margin <= close_margin) and second:
        behavior = "human_decision" if policy == "require_human_when_ambiguous" else _uncertainty_behavior(
            profile, "when_close", "select_best_anyway"
        )
        if behavior == "keep_previous" and previous_id:
            return _keep_previous(
                objective_id,
                previous,
                now,
                previous_eval.score if previous_eval else best.score,
                f"close_scores_margin_{margin:.3f}",
            )
        if behavior != "select_best_anyway":
            return _uncertain_decision(
                profile,
                "when_close",
                objective_id,
                previous,
                now,
                rejected,
                f"top candidates are close: margin {margin:.3f}",
                behavior_override=behavior,
            )

    if best.human_decisions:
        candidate = _candidate_by_id(candidates, best.candidate_id)
        return Decision(
            id=new_id("decision"),
            status="needs_human_decision",
            objective_id=objective_id,
            selected_candidate_id=best.candidate_id,
            selected_candidate_ids=[best.candidate_id],
            previous_decision_id=previous.get("id"),
            action=_action_for_candidate(profile, candidate),
            confidence=best.score,
            uncertainty=1.0 - best.score,
            policy_reason="candidate_requires_human_decision",
            explanation="best candidate requires human input",
            rejected_candidates=rejected,
            warnings=best.warnings,
            required_human_inputs=best.human_decisions,
            created_at=now,
            metadata={"selected_source_ids": _candidate_source_ids(candidate)},
        )

    candidate = _candidate_by_id(candidates, best.candidate_id)
    status = _status_for_mode(profile, candidate)
    return Decision(
        id=new_id("decision"),
        status=status,
        objective_id=objective_id,
        selected_candidate_id=best.candidate_id,
        selected_candidate_ids=[best.candidate_id],
        previous_decision_id=previous.get("id"),
        action=_action_for_candidate(profile, candidate),
        confidence=best.score,
        uncertainty=max(0.0, min(1.0, 1.0 - best.score)),
        policy_reason=f"{policy}_selected_highest_score",
        explanation=f"selected {best.candidate_id} with score {best.score:.3f}",
        rejected_candidates=rejected,
        warnings=best.warnings,
        created_at=now,
        metadata={
            "score_margin": margin,
            "second_candidate_id": second.candidate_id if second else None,
            "selected_source_ids": _candidate_source_ids(candidate),
        },
    )


def _uncertain_decision(
    profile: dict[str, Any],
    behavior_key: str,
    objective_id: str,
    previous: dict[str, Any],
    now: str,
    rejected: list[dict[str, Any]],
    reason: str,
    behavior_override: str | None = None,
) -> Decision:
    behavior = behavior_override or _uncertainty_behavior(profile, behavior_key, "no_candidate")
    if behavior == "keep_previous" and previous.get("selected_candidate_id"):
        return _keep_previous(objective_id, previous, now, float(previous.get("confidence", 0.0)), reason)
    status = UNCERTAINTY_STATUS.get(behavior, behavior)
    return Decision(
        id=new_id("decision"),
        status=status,
        objective_id=objective_id,
        selected_candidate_id=None,
        previous_decision_id=previous.get("id"),
        confidence=0.0,
        uncertainty=1.0,
        policy_reason=f"{behavior_key}:{behavior}",
        explanation=reason,
        rejected_candidates=rejected,
        warnings=[reason],
        created_at=now,
    )


def _uncertainty_behavior(profile: dict[str, Any], key: str, default: str) -> str:
    return str((profile.get("uncertainty") or {}).get(key, default))


def _keep_previous(
    objective_id: str,
    previous: dict[str, Any],
    now: str,
    confidence: float,
    reason: str,
) -> Decision:
    previous_id = previous.get("selected_candidate_id")
    return Decision(
        id=new_id("decision"),
        status="kept_previous",
        objective_id=objective_id,
        selected_candidate_id=previous_id,
        selected_candidate_ids=[previous_id] if previous_id else [],
        previous_decision_id=previous.get("id"),
        action=previous.get("action"),
        confidence=confidence,
        uncertainty=max(0.0, min(1.0, 1.0 - confidence)),
        policy_reason=reason,
        explanation=f"kept previous candidate {previous_id}: {reason}",
        created_at=now,
        metadata={"selected_source_ids": _previous_source_ids(previous)},
    )


def _candidate_by_id(candidates: list[Candidate], candidate_id: str) -> Candidate | None:
    for candidate in candidates:
        if candidate.id == candidate_id:
            return candidate
    return None


def _candidate_source_ids(candidate: Candidate | None) -> list[str]:
    return list(candidate.source_ids) if candidate else []


def _previous_source_ids(previous: dict[str, Any]) -> list[str]:
    return list((previous.get("metadata") or {}).get("selected_source_ids") or [])


def _status_for_mode(profile: dict[str, Any], candidate: Candidate | None) -> str:
    mode = str(profile.get("mode", "select_one"))
    if mode == "route":
        return "routed"
    if mode == "regulate" and candidate:
        action = candidate.proposed_action or candidate.payload.get("action")
        if action in {
            "waiting",
            "request_more_evidence",
            "fallback",
            "rejected_all",
            "needs_human_decision",
        }:
            return str(action)
    return "selected"


def _action_for_candidate(profile: dict[str, Any], candidate: Candidate | None) -> dict[str, Any] | None:
    if candidate is None:
        return None
    action = candidate.proposed_action or candidate.payload.get("action")
    if action:
        return {"type": action, "candidate_id": candidate.id}
    if profile.get("mode") == "route":
        return {"type": "route", "route_id": candidate.id, "payload": candidate.payload}
    return {"type": "select", "candidate_id": candidate.id}
