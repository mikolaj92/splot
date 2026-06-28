from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import SplotState
from .registry import FunctionContext, FunctionRegistry


def apply_feedback_handlers(
    profile: dict[str, Any],
    feedback: dict[str, Any] | None,
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
) -> dict[str, Any] | None:
    if feedback is None:
        return None
    merged = deepcopy(feedback)
    for config in profile.get("feedback_handlers") or []:
        context = FunctionContext(
            profile=profile,
            observations=[],
            candidates=[],
            candidate=None,
            state=state,
            now=now,
            config=config,
            report=merged,
        )
        update = registry.call(config["provider"], context)
        if update:
            _merge_feedback_update(merged, update)
    return merged


def _merge_feedback_update(feedback: dict[str, Any], update: dict[str, Any]) -> None:
    for key in ("state_updates", "reliability_updates", "metadata"):
        if isinstance(update.get(key), dict):
            feedback.setdefault(key, {}).update(update[key])
    for key, value in update.items():
        if key not in {"state_updates", "reliability_updates", "metadata"}:
            feedback[key] = value

