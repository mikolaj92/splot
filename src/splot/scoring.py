from __future__ import annotations

from typing import Any

from .constraints import apply_constraints
from .models import SplotState, Candidate, CandidateEvaluation, Observation
from .registry import FunctionRegistry
from .signals import build_signals
from .verifiers import apply_verifiers


def evaluate_candidates(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
) -> list[CandidateEvaluation]:
    return [
        evaluate_candidate(profile, observations, candidates, candidate, state, registry, now)
        for candidate in candidates
    ]


def evaluate_candidate(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    candidate: Candidate,
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
) -> CandidateEvaluation:
    signals = build_signals(profile, observations, candidates, candidate, state, registry, now)
    constraints = apply_constraints(
        profile, observations, candidates, candidate, state, registry, now, signals
    )
    verifiers = apply_verifiers(profile, observations, candidates, candidate, state, registry, now)

    raw_score = _score_candidate(profile, observations, candidates, candidate, state, registry, now, signals)
    penalty = sum(result.penalty for result in constraints if not result.passed)
    score = max(0.0, min(1.0, raw_score - penalty))

    rejected_reasons: list[str] = []
    warnings: list[str] = []
    human_decisions: list[str] = []
    for result in constraints:
        if result.passed:
            continue
        if result.severity == "block":
            rejected_reasons.append(result.reason)
        elif result.severity == "warn":
            warnings.append(result.reason)
        elif result.severity == "human_decision":
            human_decisions.append(result.reason)
        elif result.severity == "penalize":
            warnings.append(result.reason)
    for result in verifiers:
        if not result.passed:
            rejected_reasons.append(result.reason)

    return CandidateEvaluation(
        candidate_id=candidate.id,
        eligible=not rejected_reasons,
        score=score,
        raw_score=raw_score,
        signals=signals,
        constraints=constraints,
        verifiers=verifiers,
        warnings=warnings,
        rejected_reasons=rejected_reasons,
        human_decisions=human_decisions,
    )


def _score_candidate(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    candidate: Candidate,
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
    signals: list[Any],
) -> float:
    scoring = profile.get("scoring") or {}
    provider = scoring.get("provider")
    if provider:
        from .registry import FunctionContext

        context = FunctionContext(
            profile=profile,
            observations=observations,
            candidates=candidates,
            candidate=candidate,
            state=state,
            now=now,
            config=scoring,
            report={"signals": [signal.to_dict() for signal in signals]},
        )
        provided = registry.call(provider, context)
        if isinstance(provided, dict):
            return max(0.0, min(1.0, float(provided.get("score", 0.0))))
        return max(0.0, min(1.0, float(provided)))
    total_weight = sum(signal.weight for signal in signals)
    return sum(signal.contribution for signal in signals) / total_weight if total_weight else 0.0


def evaluation_for(evaluations: list[CandidateEvaluation], candidate_id: str | None) -> CandidateEvaluation | None:
    for evaluation in evaluations:
        if evaluation.candidate_id == candidate_id:
            return evaluation
    return None
