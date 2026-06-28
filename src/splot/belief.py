from __future__ import annotations

from typing import Any

from .evidence import evidence_for_candidate
from .models import SplotState, Belief, Candidate, CandidateEvaluation, Evidence, Observation, new_id


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
    candidate_beliefs: dict[str, dict[str, Any]] = {}
    for evaluation in evaluations:
        items = evidence_for_candidate(evidence, evaluation.candidate_id)
        support = sum(item.strength * item.confidence for item in items if item.supports)
        opposition = sum(item.strength * item.confidence for item in items if item.opposes)
        candidate_beliefs[evaluation.candidate_id] = {
            "score": evaluation.score,
            "raw_score": evaluation.raw_score,
            "eligible": evaluation.eligible,
            "support": round(support, 6),
            "opposition": round(opposition, 6),
            "confidence": round(max(0.0, min(1.0, evaluation.score)), 6),
            "warnings": list(evaluation.warnings),
            "rejected_reasons": list(evaluation.rejected_reasons),
            "human_decisions": list(evaluation.human_decisions),
        }

    uncertainty, conflicts = _uncertainty_and_conflicts(profile, evaluations)
    stale_sources = _stale_sources(observations, profile)
    source_reliability = _source_reliability(profile, candidates, state)
    history = list((state.metadata.get("belief_history") if state.metadata else []) or [])
    history.append({"at": now, "candidate_count": len(candidates), "evidence_count": len(evidence)})

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
        },
    )


def _uncertainty_and_conflicts(
    profile: dict[str, Any],
    evaluations: list[CandidateEvaluation],
) -> tuple[float, list[dict[str, Any]]]:
    eligible = sorted((item for item in evaluations if item.eligible), key=lambda item: item.score, reverse=True)
    if not evaluations:
        return 1.0, [{"kind": "no_candidate", "reason": "no candidates provided"}]
    if not eligible:
        return 1.0, [{"kind": "blocked_all", "reason": "all candidates are ineligible"}]
    best = eligible[0]
    second = eligible[1] if len(eligible) > 1 else None
    uncertainty = max(0.0, min(1.0, 1.0 - best.score))
    conflicts: list[dict[str, Any]] = []
    if second:
        close_margin = float((profile.get("decision") or {}).get("close_margin", 0.05))
        margin = best.score - second.score
        uncertainty = max(uncertainty, max(0.0, close_margin - margin))
        if margin <= close_margin:
            conflicts.append(
                {
                    "kind": "close_scores",
                    "candidate_ids": [best.candidate_id, second.candidate_id],
                    "score_margin": round(margin, 6),
                    "close_margin": close_margin,
                }
            )
    blocked = [item for item in evaluations if item.rejected_reasons]
    if blocked:
        conflicts.append(
            {
                "kind": "blocked_candidates",
                "candidate_ids": [item.candidate_id for item in blocked],
            }
        )
    return uncertainty, conflicts


def _stale_sources(observations: list[Observation], profile: dict[str, Any]) -> list[str]:
    stale: set[str] = set()
    for observation in observations:
        if observation.metadata.get("stale") or observation.values.get("stale"):
            stale.add(observation.wave_id or observation.id)
    for wave in profile.get("waves") or []:
        if wave.get("stale"):
            stale.add(str(wave["id"]))
    return sorted(stale)


def _source_reliability(
    profile: dict[str, Any],
    candidates: list[Candidate],
    state: SplotState,
) -> dict[str, float]:
    reliability: dict[str, float] = {}
    for wave in profile.get("waves") or []:
        if "id" in wave:
            reliability[str(wave["id"])] = float(wave.get("reliability", 1.0))
    reliability.update(state.source_reliability)
    for candidate in candidates:
        for source_id in candidate.source_ids:
            reliability.setdefault(source_id, 1.0)
    return reliability

