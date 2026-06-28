from __future__ import annotations

from typing import Any

from .models import SplotState, Candidate, CandidateEvaluation, Evidence, Observation, new_id
from .registry import FunctionContext, FunctionRegistry


def build_evidence(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    evaluations: list[CandidateEvaluation],
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
) -> list[Evidence]:
    configs = profile.get("evidence") or profile.get("evidence_builders") or []
    if not configs:
        return _default_signal_evidence(evaluations, now)

    evidence: list[Evidence] = []
    for config in configs:
        provider = config.get("provider")
        if not provider:
            continue
        if config.get("scope", "candidate") == "round":
            context = FunctionContext(
                profile=profile,
                observations=observations,
                candidates=candidates,
                candidate=None,
                state=state,
                now=now,
                config=config,
            )
            evidence.extend(_coerce_evidence(registry.call(provider, context)))
            continue
        for candidate in candidates:
            context = FunctionContext(
                profile=profile,
                observations=observations,
                candidates=candidates,
                candidate=candidate,
                state=state,
                now=now,
                config=config,
            )
            evidence.extend(_coerce_evidence(registry.call(provider, context)))

    return evidence or _default_signal_evidence(evaluations, now)


def evidence_for_candidate(evidence: list[Evidence], candidate_id: str) -> list[Evidence]:
    return [item for item in evidence if item.candidate_id == candidate_id]


def _default_signal_evidence(evaluations: list[CandidateEvaluation], now: str) -> list[Evidence]:
    evidence: list[Evidence] = []
    for evaluation in evaluations:
        for signal in evaluation.signals:
            supports = [signal.id] if signal.normalized >= 0.5 else []
            opposes = [signal.id] if signal.normalized < 0.5 else []
            strength = abs(signal.normalized - 0.5) * 2
            evidence.append(
                Evidence(
                    id=new_id("evidence"),
                    candidate_id=evaluation.candidate_id,
                    supports=supports,
                    opposes=opposes,
                    strength=round(strength, 6),
                    confidence=signal.confidence,
                    reasons=[
                        signal.reason
                        or f"{signal.id} normalized={signal.normalized:.3f} contribution={signal.contribution:.3f}"
                    ],
                    metadata={
                        "created_at": now,
                        "signal_id": signal.id,
                        "normalized": signal.normalized,
                        "weight": signal.weight,
                        "contribution": signal.contribution,
                    },
                )
            )
        for reason in evaluation.rejected_reasons:
            evidence.append(
                Evidence(
                    id=new_id("evidence"),
                    candidate_id=evaluation.candidate_id,
                    opposes=["eligibility"],
                    strength=1.0,
                    confidence=1.0,
                    reasons=[reason],
                    metadata={"created_at": now, "kind": "rejection"},
                )
            )
    return evidence


def _coerce_evidence(value: Any) -> list[Evidence]:
    if value is None:
        return []
    if isinstance(value, Evidence):
        return [value]
    if isinstance(value, dict):
        return [Evidence.from_dict(value)]
    if isinstance(value, list):
        result: list[Evidence] = []
        for item in value:
            result.extend(_coerce_evidence(item))
        return result
    raise TypeError(f"evidence provider returned unsupported value: {type(value).__name__}")

