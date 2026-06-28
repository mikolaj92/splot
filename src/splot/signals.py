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
        value, normalized, confidence, reason = _unpack_provider_result(provided)
        if normalized is None:
            normalized = normalize_signal(
                value=value,
                prefer=str(config.get("prefer", "higher")),
                target=config.get("target"),
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
        )
        signals.append(signal)
    return signals


def normalize_signal(value: Any, prefer: str = "higher", target: Any | None = None) -> float:
    if prefer == "boolean":
        return 1.0 if bool(value) else 0.0
    numeric = _to_float(value)
    if prefer == "lower":
        return 1.0 - clamp01(numeric)
    if prefer == "target":
        target_value = _to_float(0.5 if target is None else target)
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


def _unpack_provider_result(value: Any) -> tuple[Any, float | None, float, str | None]:
    if isinstance(value, dict):
        return (
            value.get("value"),
            value.get("normalized"),
            float(value.get("confidence", 1.0)),
            value.get("reason"),
        )
    return value, None, 1.0, None

