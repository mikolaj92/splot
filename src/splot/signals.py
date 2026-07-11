from __future__ import annotations

from typing import Any

from .models import SplotState, Candidate, Observation, Signal
from .registry import FunctionContext, FunctionRegistry


def build_signals(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    candidate: Candidate,
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
) -> list[Signal]:
    signals: list[Signal] = []
    for config in profile.get("signals") or []:
        provider = config.get("provider", "candidate.value")
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
        value, normalized, confidence, reason, sources = _unpack_provider_result(provided)
        sources = _known_sources(sources, observations)
        if normalized is None:
            normalized = normalize_signal(
                value=value,
                prefer=str(config.get("prefer", "higher")),
                target=config.get("target"),
                value_range=config.get("range"),
            )
        weight = float(config.get("weight", 1.0))
        signal = Signal(
            id=str(config["id"]),
            value=value,
            normalized=normalized,
            weight=weight,
            prefer=str(config.get("prefer", "higher")),
            confidence=confidence,
            reason=reason,
            contribution=normalized * weight,
            sources=sources,
        )
        signals.append(signal)
    return signals


def normalize_signal(
    value: Any,
    prefer: str = "higher",
    target: Any | None = None,
    value_range: Any | None = None,
) -> float:
    if prefer == "boolean":
        return 1.0 if bool(value) else 0.0
    numeric = _to_float(value)
    if value_range:
        low, high = float(value_range[0]), float(value_range[1])
        numeric = (numeric - low) / (high - low)
    if prefer == "lower":
        return 1.0 - clamp01(numeric)
    if prefer == "target":
        target_value = _to_float(0.5 if target is None else target)
        if value_range:
            target_value = (target_value - low) / (high - low)
        return 1.0 - clamp01(abs(numeric - target_value))
    return clamp01(numeric)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _to_float(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _unpack_provider_result(
    value: Any,
) -> tuple[Any, float | None, float, str | None, Any]:
    if isinstance(value, dict):
        return (
            value.get("value"),
            value.get("normalized"),
            float(value.get("confidence", 1.0)),
            value.get("reason"),
            value.get("sources"),
        )
    return value, None, 1.0, None, None


def _known_sources(sources: Any, observations: list[Observation]) -> list[dict[str, Any]]:
    """Keep only attribution that points at an observation of this round.

    A provider result is arbitrary candidate payload, so `sources` may be
    anything; attribution that cannot be verified is dropped rather than
    carried into evidence.
    """
    if not isinstance(sources, list):
        return []
    waves = {observation.id: observation.wave_id for observation in observations}
    return [
        {"observation_id": entry["observation_id"], "wave_id": waves[entry["observation_id"]]}
        for entry in sources
        if isinstance(entry, dict) and entry.get("observation_id") in waves
    ]

