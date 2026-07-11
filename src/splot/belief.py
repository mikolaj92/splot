from __future__ import annotations

from typing import Any

from .evidence import evidence_for_candidate
from .models import SplotState, Belief, Candidate, CandidateEvaluation, Evidence, Observation, new_id
from .sources import candidate_reliability, source_reliability_map, stale_source_ids


def build_belief(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    evaluations: list[CandidateEvaluation],
    evidence: list[Evidence],
    state: SplotState,
    now: str,
) -> Belief:
    objective_id = str((profile.get("objective") or {}).get("id", profile.get("id", "")))
    source_reliability = source_reliability_map(profile, candidates, state)
    belief_config = profile.get("belief") or {}
    smoothing = float(belief_config.get("smoothing", 0.0))
    previous = (state.metadata or {}).get("last_belief") or {}
    previous_beliefs = previous.get("candidate_beliefs") or {}
    candidates_by_id = {candidate.id: candidate for candidate in candidates}
    candidate_beliefs: dict[str, dict[str, Any]] = {}
    for evaluation in evaluations:
        items = evidence_for_candidate(evidence, evaluation.candidate_id)
        support = sum(item.strength * item.confidence for item in items if item.supports)
        opposition = sum(item.strength * item.confidence for item in items if item.opposes)
        prior = previous_beliefs.get(evaluation.candidate_id) or {}
        if smoothing and prior:
            support = smoothing * float(prior.get("support") or 0.0) + (1.0 - smoothing) * support
            opposition = (
                smoothing * float(prior.get("opposition") or 0.0) + (1.0 - smoothing) * opposition
            )
        strength_total = sum(item.strength for item in items)
        evidence_confidence = (
            sum(item.strength * item.confidence for item in items) / strength_total
            if strength_total
            else None
        )
        candidate = candidates_by_id.get(evaluation.candidate_id)
        reliability_min = candidate_reliability(candidate, source_reliability) if candidate else 1.0
        contested_mass = support + opposition
        candidate_beliefs[evaluation.candidate_id] = {
            "score": evaluation.score,
            "raw_score": evaluation.raw_score,
            "eligible": evaluation.eligible,
            "support": round(support, 6),
            "opposition": round(opposition, 6),
            "input_disagreement": round(opposition / contested_mass, 6) if contested_mass else None,
            "rounds_seen": int(prior.get("rounds_seen") or 0) + 1,
            "confidence": round(max(0.0, min(1.0, evaluation.score)), 6),
            "evidence_confidence": round(evidence_confidence, 6) if evidence_confidence is not None else None,
            "source_reliability_min": round(reliability_min, 6),
            "warnings": list(evaluation.warnings),
            "rejected_reasons": list(evaluation.rejected_reasons),
            "human_decisions": list(evaluation.human_decisions),
        }

    components, conflicts = _uncertainty_components(profile, evaluations, candidate_beliefs)
    uncertainty = max(components.values())
    top_candidate_id, winner_streak, reduction = _winner_stability(
        belief_config, evaluations, previous
    )
    if reduction:
        uncertainty = max(0.0, uncertainty - reduction)
    stale_sources = stale_source_ids(profile, observations, now)
    history = list((state.metadata.get("belief_history") if state.metadata else []) or [])
    history.append(
        {
            "at": now,
            "candidate_count": len(candidates),
            "evidence_count": len(evidence),
            "top_candidate_id": top_candidate_id,
            "uncertainty": round(uncertainty, 6),
        }
    )

    return Belief(
        id=new_id("belief"),
        objective_id=objective_id,
        candidate_beliefs=candidate_beliefs,
        uncertainty=round(uncertainty, 6),
        conflicts=conflicts,
        stale_sources=stale_sources,
        source_reliability=source_reliability,
        previous_decision=state.previous_decision,
        history=history[-50:],
        metadata={
            "created_at": now,
            "observation_count": len(observations),
            "candidate_count": len(candidates),
            "evidence_count": len(evidence),
            "uncertainty_components": {key: round(value, 6) for key, value in components.items()},
            "top_candidate_id": top_candidate_id,
            "winner_streak": winner_streak,
            **(
                {
                    "uncertainty_reduction": {
                        "value": round(reduction, 6),
                        "reason": f"top candidate stable for {winner_streak} rounds",
                    }
                }
                if reduction
                else {}
            ),
        },
    )


def _winner_stability(
    belief_config: dict[str, Any],
    evaluations: list[CandidateEvaluation],
    previous: dict[str, Any],
) -> tuple[str | None, int, float]:
    """Streak of rounds the same candidate stayed on top, and the explicit
    uncertainty reduction it earns (opt-in via belief.stability_step)."""
    eligible = sorted(
        (item for item in evaluations if item.eligible), key=lambda item: item.score, reverse=True
    )
    if not eligible:
        return None, 0, 0.0
    top = eligible[0].candidate_id
    previous_metadata = previous.get("metadata") or {}
    streak = 1
    if previous_metadata.get("top_candidate_id") == top:
        streak = int(previous_metadata.get("winner_streak") or 0) + 1
    step = float(belief_config.get("stability_step", 0.0))
    cap = float(belief_config.get("stability_cap", 0.2))
    reduction = min(cap, (streak - 1) * step)
    return top, streak, reduction


def _uncertainty_components(
    profile: dict[str, Any],
    evaluations: list[CandidateEvaluation],
    candidate_beliefs: dict[str, dict[str, Any]],
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Named uncertainty components; belief uncertainty is their maximum."""
    if not evaluations:
        return {"no_candidate": 1.0}, [{"kind": "no_candidate", "reason": "no candidates provided"}]
    eligible = sorted((item for item in evaluations if item.eligible), key=lambda item: item.score, reverse=True)
    if not eligible:
        return {"blocked_all": 1.0}, [{"kind": "blocked_all", "reason": "all candidates are ineligible"}]
    best = eligible[0]
    second = eligible[1] if len(eligible) > 1 else None
    components = {"score_residual": max(0.0, min(1.0, 1.0 - best.score))}
    conflicts: list[dict[str, Any]] = []
    if second:
        close_margin = float((profile.get("decision") or {}).get("close_margin", 0.05))
        margin = best.score - second.score
        components["close_margin_gap"] = max(0.0, close_margin - margin)
        if margin <= close_margin:
            conflicts.append(
                {
                    "kind": "close_scores",
                    "candidate_ids": [best.candidate_id, second.candidate_id],
                    "score_margin": round(margin, 6),
                    "close_margin": close_margin,
                }
            )
    winner_belief = candidate_beliefs[best.candidate_id]
    if winner_belief["evidence_confidence"] is not None:
        components["evidence_confidence_gap"] = max(0.0, 1.0 - winner_belief["evidence_confidence"])
    components["source_reliability_gap"] = max(0.0, 1.0 - winner_belief["source_reliability_min"])
    blocked = [item for item in evaluations if item.rejected_reasons]
    if blocked:
        conflicts.append(
            {
                "kind": "blocked_candidates",
                "candidate_ids": [item.candidate_id for item in blocked],
            }
        )
    contested_threshold = float((profile.get("belief") or {}).get("contested_threshold", 0.25))
    contested = [
        candidate_id
        for candidate_id, item in candidate_beliefs.items()
        if min(item["support"], item["opposition"]) > contested_threshold
    ]
    if contested:
        conflicts.append(
            {
                "kind": "contested_candidate",
                "candidate_ids": contested,
                "contested_threshold": contested_threshold,
            }
        )
    return components, conflicts

