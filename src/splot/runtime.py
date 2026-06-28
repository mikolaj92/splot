from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .belief import build_belief
from .composition import decide_composition
from .evidence import build_evidence
from .feedback import apply_feedback_handlers
from .models import (
    SplotState,
    Belief,
    Candidate,
    Decision,
    DecisionReport,
    Evidence,
    Observation,
    new_id,
)
from .policies import decide_from_evaluations
from .profile import SplotProfile, load_profile, validate_profile
from .registry import FunctionContext, FunctionRegistry, builtin_registry
from .reports import apply_report_postprocessors
from .scoring import evaluate_candidates
from .stability import apply_stability
from .state import update_state


@dataclass
class RoundResult:
    decision: Decision
    state: SplotState
    report: DecisionReport


def run_round(
    profile: str | dict[str, Any] | SplotProfile,
    observations: list[dict[str, Any] | Observation] | None = None,
    candidates: list[dict[str, Any] | Candidate] | None = None,
    previous_state: dict[str, Any] | SplotState | None = None,
    registry: FunctionRegistry | None = None,
    now: str | datetime | None = None,
    feedback: dict[str, Any] | None = None,
) -> RoundResult:
    registry = registry or builtin_registry()
    loaded_profile = load_profile(profile)
    validate_profile(loaded_profile, registry=registry)
    now_text = _now_text(now)
    state = previous_state if isinstance(previous_state, SplotState) else SplotState.from_dict(previous_state)
    state.objective_id = loaded_profile.objective_id
    feedback = apply_feedback_handlers(loaded_profile.raw, feedback, state, registry, now_text)
    observation_models = [_observation(item) for item in observations or []]
    candidate_models = [_candidate(item) for item in candidates or []]
    if not candidate_models:
        candidate_models = _load_candidates_from_provider(
            loaded_profile.raw, observation_models, state, registry, now_text
        )

    evaluations = evaluate_candidates(
        loaded_profile.raw, observation_models, candidate_models, state, registry, now_text
    )
    stale_sources = _apply_source_staleness(
        loaded_profile.raw,
        observation_models,
        candidate_models,
        evaluations,
    )
    evidence = build_evidence(
        loaded_profile.raw,
        observation_models,
        candidate_models,
        evaluations,
        state,
        registry,
        now_text,
    )
    belief = build_belief(
        loaded_profile.raw,
        observation_models,
        candidate_models,
        evaluations,
        evidence,
        state,
        now_text,
    )
    if loaded_profile.mode == "compose":
        stale_decision = _stale_source_decision(loaded_profile.raw, stale_sources, state, now_text)
        if stale_decision:
            decision = stale_decision
            stability_analysis = {
                "policy": "source_staleness",
                "decision": decision.status,
                "stale_sources": stale_sources,
            }
        else:
            decision, stability_analysis = decide_composition(
                loaded_profile.raw, candidate_models, evaluations, state, now_text
            )
        stability_updates: dict[str, Any] = {}
    else:
        stale_decision = _stale_source_decision(loaded_profile.raw, stale_sources, state, now_text)
        if stale_decision:
            decision = stale_decision
            stability_analysis = {
                "policy": "source_staleness",
                "decision": decision.status,
                "stale_sources": stale_sources,
            }
            stability_updates = {}
        else:
            proposed = decide_from_evaluations(
                loaded_profile.raw, candidate_models, evaluations, state, now_text
            )
            decision, stability_analysis, stability_updates = apply_stability(
                loaded_profile.raw, candidate_models, evaluations, state, proposed, now_text
            )

    updated_state = update_state(
        state,
        decision,
        evaluations,
        now_text,
        stability_updates,
        feedback,
        evidence=evidence,
        belief=belief,
    )
    report = _build_report(
        loaded_profile,
        observation_models,
        candidate_models,
        evidence,
        belief,
        evaluations,
        stability_analysis,
        decision,
        state,
        updated_state,
        now_text,
    )
    report = apply_report_postprocessors(loaded_profile.raw, report, updated_state, registry, now_text)
    return RoundResult(decision=decision, state=updated_state, report=report)


def _build_report(
    profile: SplotProfile,
    observations: list[Observation],
    candidates: list[Candidate],
    evidence: list[Evidence],
    belief: Belief,
    evaluations: list[Any],
    stability: dict[str, Any],
    decision: Decision,
    previous_state: SplotState,
    updated_state: SplotState,
    now: str,
) -> DecisionReport:
    warnings = list(decision.warnings)
    for evaluation in evaluations:
        warnings.extend(evaluation.warnings)
    return DecisionReport(
        round_id=new_id("round"),
        profile_id=profile.id,
        mode=profile.mode,
        objective_id=profile.objective_id,
        created_at=now,
        previous_decision=previous_state.previous_decision,
        observations=[item.to_dict() for item in observations],
        candidates=[item.to_dict() for item in candidates],
        evidence=[item.to_dict() for item in evidence],
        belief=belief.to_dict(),
        evaluations=[item.to_dict() for item in evaluations],
        stability=stability,
        decision=decision.to_dict(),
        uncertainty={
            "value": max(decision.uncertainty, belief.uncertainty),
            "decision_uncertainty": decision.uncertainty,
            "belief_uncertainty": belief.uncertainty,
            "conflicts": belief.conflicts,
            "stale_sources": belief.stale_sources,
            "reasons": decision.warnings,
        },
        policy_reasons=[decision.policy_reason],
        previous_state=previous_state.to_dict(),
        updated_state=updated_state.to_dict(),
        warnings=warnings,
        human_decisions=list(decision.required_human_inputs),
        state_updates={
            "previous_decision": updated_state.previous_decision,
            "last_decision_at": updated_state.last_decision_at,
            "last_switch_at": updated_state.last_switch_at,
            "stability_memory": updated_state.stability_memory,
        },
    )


def _load_candidates_from_provider(
    profile: dict[str, Any],
    observations: list[Observation],
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
) -> list[Candidate]:
    config = profile.get("candidate") or {}
    provider = config.get("provider")
    if not provider:
        return []
    context = FunctionContext(
        profile=profile,
        observations=observations,
        candidates=[],
        candidate=None,
        state=state,
        now=now,
        config=config,
    )
    provided = registry.call(provider, context)
    return [_candidate(item) for item in provided or []]


def _apply_source_staleness(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    evaluations: list[Any],
) -> list[str]:
    stale_sources = set()
    for observation in observations:
        if observation.metadata.get("stale") or observation.values.get("stale"):
            stale_sources.add(observation.wave_id or observation.id)
    for wave in profile.get("waves") or []:
        if wave.get("stale"):
            stale_sources.add(str(wave["id"]))
    if not stale_sources:
        return []

    behavior = str((profile.get("uncertainty") or {}).get("when_source_stale", "ignore"))
    if behavior not in {"penalize", "block"}:
        return sorted(stale_sources)

    penalty = float((profile.get("uncertainty") or {}).get("stale_penalty", 0.25))
    candidates_by_id = {candidate.id: candidate for candidate in candidates}
    for evaluation in evaluations:
        candidate = candidates_by_id.get(evaluation.candidate_id)
        if not candidate or not stale_sources.intersection(candidate.source_ids):
            continue
        reason = f"candidate uses stale source: {', '.join(sorted(stale_sources.intersection(candidate.source_ids)))}"
        if behavior == "block":
            evaluation.eligible = False
            evaluation.rejected_reasons.append(reason)
        else:
            evaluation.score = max(0.0, evaluation.score - penalty)
            evaluation.warnings.append(reason)
    return sorted(stale_sources)


def _stale_source_decision(
    profile: dict[str, Any],
    stale_sources: list[str],
    state: SplotState,
    now: str,
) -> Decision | None:
    behavior = str((profile.get("uncertainty") or {}).get("when_source_stale", "ignore"))
    if not stale_sources or behavior != "request_more_evidence":
        return None
    previous = state.previous_decision or {}
    return Decision(
        id=new_id("decision"),
        status="request_more_evidence",
        objective_id=str((profile.get("objective") or {}).get("id", profile.get("id", ""))),
        previous_decision_id=previous.get("id"),
        confidence=0.0,
        uncertainty=1.0,
        policy_reason="when_source_stale:request_more_evidence",
        explanation=f"stale sources present: {', '.join(stale_sources)}",
        warnings=[f"stale sources present: {', '.join(stale_sources)}"],
        created_at=now,
    )


def _candidate(value: dict[str, Any] | Candidate) -> Candidate:
    return value if isinstance(value, Candidate) else Candidate.from_dict(value)


def _observation(value: dict[str, Any] | Observation) -> Observation:
    return value if isinstance(value, Observation) else Observation.from_dict(value)


def _now_text(value: str | datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return value
