from __future__ import annotations

from typing import Any

from .models import SplotState, Candidate, Observation, VerifierResult
from .registry import FunctionContext, FunctionRegistry


def apply_verifiers(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    candidate: Candidate,
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
) -> list[VerifierResult]:
    results: list[VerifierResult] = []
    for config in profile.get("verifiers") or []:
        provider = config.get("provider", "always.pass")
        context = FunctionContext(
            profile=profile,
            observations=observations,
            candidates=candidates,
            candidate=candidate,
            state=state,
            now=now,
            config=config,
        )
        provided = registry.call(provider, context)
        if isinstance(provided, dict):
            passed = bool(provided.get("passed", provided.get("value", False)))
            reason = str(provided.get("reason", config.get("reason", config.get("id", provider))))
        else:
            passed = bool(provided)
            reason = str(config.get("reason", config.get("id", provider)))
        results.append(VerifierResult(id=str(config.get("id", provider)), passed=passed, reason=reason))
    return results

