from __future__ import annotations

from typing import Any

from .models import DecisionReport, SplotState
from .registry import FunctionContext, FunctionRegistry


def apply_report_postprocessors(
    profile: dict[str, Any],
    report: DecisionReport,
    state: SplotState,
    registry: FunctionRegistry,
    now: str,
) -> DecisionReport:
    current = report.to_dict()
    for config in profile.get("postprocess") or []:
        provider = config.get("provider")
        if not provider:
            continue
        context = FunctionContext(
            profile=profile,
            observations=[],
            candidates=[],
            candidate=None,
            state=state,
            now=now,
            config=config,
            report=current,
        )
        processed = registry.call(provider, context)
        if isinstance(processed, DecisionReport):
            current = processed.to_dict()
        elif isinstance(processed, dict):
            current = processed
    return DecisionReport(**current)

