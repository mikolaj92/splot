from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .models import SplotState, Candidate, Evidence, Observation, new_id


Provider = Callable[["FunctionContext"], Any]


@dataclass
class FunctionContext:
    profile: dict[str, Any]
    observations: list[Observation]
    candidates: list[Candidate]
    candidate: Candidate | None
    state: SplotState
    now: str
    config: dict[str, Any]
    report: dict[str, Any] | None = None


class FunctionRegistry:
    """Explicit allowlist for profile-referenced functions."""

    def __init__(self) -> None:
        self._functions: dict[str, Provider] = {}
        self._categories: dict[str, str] = {}

    def register(self, name: str, function: Provider, category: str = "generic") -> None:
        if not name or not isinstance(name, str):
            raise ValueError("registered function name must be a non-empty string")
        self._functions[name] = function
        self._categories[name] = category

    def has(self, name: str) -> bool:
        return name in self._functions

    def get(self, name: str) -> Provider:
        try:
            return self._functions[name]
        except KeyError as exc:
            raise KeyError(f"function is not registered: {name}") from exc

    def call(self, name: str, context: FunctionContext) -> Any:
        return self.get(name)(context)

    def names(self) -> list[str]:
        return sorted(self._functions)

    def names_by_category(self, category: str) -> list[str]:
        return sorted(name for name, item_category in self._categories.items() if item_category == category)

    def category(self, name: str) -> str | None:
        return self._categories.get(name)


def _candidate_value(context: FunctionContext) -> Any:
    candidate = _require_candidate(context)
    field = context.config.get("field") or context.config.get("id")
    if field in candidate.payload:
        return candidate.payload[field]
    if field in candidate.metadata:
        return candidate.metadata[field]
    return context.config.get("default", 0)


def _candidate_flag(context: FunctionContext) -> bool:
    candidate = _require_candidate(context)
    field = context.config.get("field") or context.config.get("id")
    default = bool(context.config.get("default", True))
    return bool(candidate.payload.get(field, candidate.metadata.get(field, default)))


def _candidate_available(context: FunctionContext) -> bool:
    candidate = _require_candidate(context)
    return bool(candidate.payload.get("available", candidate.metadata.get("available", True)))


def _observation_value(context: FunctionContext) -> Any:
    field = context.config.get("field") or context.config.get("id")
    candidate = context.candidate
    candidate_sources = set(candidate.source_ids) if candidate else set()
    for observation in reversed(context.observations):
        source_match = not candidate_sources or observation.wave_id in candidate_sources
        if source_match and field in observation.values:
            return observation.values[field]
    return context.config.get("default", 0)


def _observations_static(context: FunctionContext) -> list[dict[str, Any]]:
    return list(context.config.get("items") or [])


def _candidates_static(context: FunctionContext) -> list[dict[str, Any]]:
    return list(context.config.get("items") or [])


def _candidates_from_observation_values(context: FunctionContext) -> list[dict[str, Any]]:
    field = context.config.get("field", "candidates")
    candidates: list[dict[str, Any]] = []
    for observation in context.observations:
        values = observation.values.get(field) or []
        if isinstance(values, dict):
            values = [values]
        candidates.extend(values)
    return candidates


def _state_is_current(context: FunctionContext) -> float:
    candidate = _require_candidate(context)
    previous = context.state.previous_decision or {}
    return 1.0 if previous.get("selected_candidate_id") == candidate.id else 0.0


def _always_pass(_: FunctionContext) -> bool:
    return True


def _identity_postprocess(context: FunctionContext) -> Any:
    return context.report


def _weighted_scorer(context: FunctionContext) -> dict[str, Any]:
    signals = (context.report or {}).get("signals") or []
    total_weight = sum(float(signal.get("weight", 0.0)) for signal in signals)
    score = (
        sum(float(signal.get("contribution", 0.0)) for signal in signals) / total_weight
        if total_weight
        else 0.0
    )
    return {"score": score, "reason": "weighted signal score"}


def _decision_summary_renderer(context: FunctionContext) -> dict[str, Any]:
    decision = dict(context.report or {})
    selected = decision.get("selected_candidate_id") or decision.get("selected_candidate_ids")
    return {
        "action": {
            "type": "summary",
            "status": decision.get("status"),
            "selected": selected,
        },
        "explanation": f"{decision.get('status')} selected={selected}",
    }


def _payload_evidence(context: FunctionContext) -> list[dict[str, Any]]:
    candidate = _require_candidate(context)
    payload_evidence = candidate.payload.get("evidence") or candidate.metadata.get("evidence") or []
    if isinstance(payload_evidence, dict):
        payload_evidence = [payload_evidence]
    result: list[dict[str, Any]] = []
    for item in payload_evidence:
        result.append(
            Evidence(
                id=str(item.get("id") or new_id("evidence")),
                observation_id=item.get("observation_id"),
                candidate_id=str(item.get("candidate_id") or candidate.id),
                supports=list(item.get("supports") or []),
                opposes=list(item.get("opposes") or []),
                strength=float(item.get("strength", 0.0)),
                confidence=float(item.get("confidence", 1.0)),
                reasons=list(item.get("reasons") or []),
                metadata=dict(item.get("metadata") or {}),
            ).to_dict()
        )
    return result


def _feedback_acceptance_reliability(context: FunctionContext) -> dict[str, Any]:
    feedback = context.report or {}
    accepted = feedback.get("accepted")
    decision = context.state.previous_decision or {}
    selected_ids = decision.get("selected_candidate_ids") or []
    selected_id = decision.get("selected_candidate_id")
    if selected_id and selected_id not in selected_ids:
        selected_ids.append(selected_id)
    delta = float(context.config.get("accepted_delta", 0.02 if accepted else -0.05))
    updates: dict[str, float] = {}
    for source_id in selected_ids:
        current = context.state.source_reliability.get(source_id, 1.0)
        updates[source_id] = max(0.0, min(1.0, current + delta))
    return {"reliability_updates": updates}


def _require_candidate(context: FunctionContext) -> Candidate:
    if context.candidate is None:
        raise ValueError("provider requires a candidate")
    return context.candidate


def builtin_registry() -> FunctionRegistry:
    registry = FunctionRegistry()
    registry.register("candidate.value", _candidate_value, "signal_provider")
    registry.register("candidate.flag", _candidate_flag, "constraint_predicate")
    registry.register("candidate.available", _candidate_available, "constraint_predicate")
    registry.register("candidates.static", _candidates_static, "candidate_provider")
    registry.register(
        "candidates.from_observation_values",
        _candidates_from_observation_values,
        "candidate_provider",
    )
    registry.register("observation.value", _observation_value, "signal_provider")
    registry.register("observations.static", _observations_static, "observation_provider")
    registry.register("state.is_current", _state_is_current, "signal_provider")
    registry.register("always.pass", _always_pass, "constraint_predicate")
    registry.register("evidence.payload", _payload_evidence, "evidence_builder")
    registry.register("score.weighted", _weighted_scorer, "scorer")
    registry.register("decision.render_summary", _decision_summary_renderer, "decision_renderer")
    registry.register("postprocess.identity", _identity_postprocess, "postprocessor")
    registry.register(
        "feedback.acceptance_reliability",
        _feedback_acceptance_reliability,
        "feedback_handler",
    )
    return registry
