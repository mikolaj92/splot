from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .composition import decide_composition
from .models import (
    SplotState,
    Candidate,
    Decision,
    DecisionReport,
    Observation,
    new_id,
)
from .policies import decide_from_evaluations
from .profile import SplotProfile, load_profile, validate_profile
from .registry import FunctionContext, FunctionRegistry, builtin_registry
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
    observation_models = [_observation(item) for item in observations or []]
    candidate_models = [_candidate(item) for item in candidates or []]
    if not candidate_models:
        candidate_models = _load_candidates_from_provider(
            loaded_profile.raw, observation_models, state, registry, now_text
        )

    evaluations = evaluate_candidates(
        loaded_profile.raw, observation_models, candidate_models, state, registry, now_text
    )
    if loaded_profile.mode == "compose":
        decision, stability_analysis = decide_composition(
            loaded_profile.raw, candidate_models, evaluations, state, now_text
        )
        stability_updates: dict[str, Any] = {}
    else:
        proposed = decide_from_evaluations(
            loaded_profile.raw, candidate_models, evaluations, state, now_text
        )
        decision, stability_analysis, stability_updates = apply_stability(
            loaded_profile.raw, candidate_models, evaluations, state, proposed, now_text
        )

    updated_state = update_state(state, decision, evaluations, now_text, stability_updates, feedback)
    report = _build_report(
        loaded_profile,
        observation_models,
        candidate_models,
        evaluations,
        stability_analysis,
        decision,
        state,
        updated_state,
        now_text,
    )
    return RoundResult(decision=decision, state=updated_state, report=report)


def _build_report(
    profile: SplotProfile,
    observations: list[Observation],
    candidates: list[Candidate],
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
        evidence=[],
        evaluations=[item.to_dict() for item in evaluations],
        stability=stability,
        decision=decision.to_dict(),
        uncertainty={"value": decision.uncertainty, "reasons": decision.warnings},
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

