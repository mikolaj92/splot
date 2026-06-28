from __future__ import annotations

from typing import Any

from .models import SplotState, Candidate, ConstraintResult, Observation, Signal
from .registry import FunctionContext, FunctionRegistry


def apply_constraints(
    profile: dict[str, Any],
    observations: list[Observation],
    candidates: list[Candidate],
    candidate: Candidate,
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
    signals: list[Signal],
) -> list[ConstraintResult]:
    signal_by_id = {signal.id: signal for signal in signals}
    results: list[ConstraintResult] = []

    for signal_config in profile.get("signals") or []:
        signal = signal_by_id[str(signal_config["id"])]
        if "min" in signal_config and signal.normalized < float(signal_config["min"]):
            results.append(
                ConstraintResult(
                    id=f"{signal.id}.min",
                    severity="block",
                    passed=False,
                    reason=(
                        f"signal {signal.id} normalized value {signal.normalized:.3f} "
                        f"< min {float(signal_config['min']):.3f}"
                    ),
                )
            )
        if "max" in signal_config and signal.normalized > float(signal_config["max"]):
            results.append(
                ConstraintResult(
                    id=f"{signal.id}.max",
                    severity="block",
                    passed=False,
                    reason=(
                        f"signal {signal.id} normalized value {signal.normalized:.3f} "
                        f"> max {float(signal_config['max']):.3f}"
                    ),
                )
            )

    for config in profile.get("constraints") or []:
        severity = str(config.get("severity", "block"))
        if "signal" in config:
            passed, reason = _evaluate_signal_constraint(config, signal_by_id)
            penalty = float(config.get("penalty", 0.0)) if not passed else 0.0
        else:
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
            passed, reason, penalty = _unpack_predicate_result(registry.call(provider, context), config)
        results.append(
            ConstraintResult(
                id=str(config["id"]),
                severity=severity,
                passed=passed,
                reason=reason,
                penalty=penalty,
            )
        )
    return results


def _evaluate_signal_constraint(
    config: dict[str, Any], signals: dict[str, Signal]
) -> tuple[bool, str]:
    signal = signals[str(config["signal"])]
    left = signal.normalized if config.get("use") == "normalized" else signal.value
    right = config.get("value", config.get("threshold"))
    operator = str(config.get("operator", "gte"))
    passed = compare(left, operator, right)
    return passed, f"{signal.id} {operator} {right} was {left}"


def compare(left: Any, operator: str, right: Any) -> bool:
    left_number = _to_float(left)
    right_number = _to_float(right)
    if operator in {"gte", ">="}:
        return left_number >= right_number
    if operator in {"gt", ">"}:
        return left_number > right_number
    if operator in {"lte", "<="}:
        return left_number <= right_number
    if operator in {"lt", "<"}:
        return left_number < right_number
    if operator in {"eq", "=="}:
        return left == right
    if operator in {"neq", "!="}:
        return left != right
    raise ValueError(f"unsupported operator: {operator}")


def _unpack_predicate_result(value: Any, config: dict[str, Any]) -> tuple[bool, str, float]:
    if isinstance(value, dict):
        passed = bool(value.get("passed", value.get("value", False)))
        reason = str(value.get("reason", config.get("reason", config["id"])))
        penalty = float(value.get("penalty", config.get("penalty", 0.0))) if not passed else 0.0
        return passed, reason, penalty
    passed = bool(value)
    reason = str(config.get("reason", config["id"]))
    penalty = float(config.get("penalty", 0.0)) if not passed else 0.0
    return passed, reason, penalty


def _to_float(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

