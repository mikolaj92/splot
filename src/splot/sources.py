"""Source (wave) helpers shared by scoring, belief, and runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import SplotState, Candidate, Observation


def source_reliability_map(
    profile: dict[str, Any],
    candidates: list[Candidate],
    state: SplotState,
) -> dict[str, float]:
    reliability: dict[str, float] = {}
    for wave in profile.get("waves") or []:
        if "id" in wave:
            reliability[str(wave["id"])] = float(wave.get("reliability", 1.0))
    reliability.update(state.source_reliability)
    for candidate in candidates:
        for source_id in candidate.source_ids:
            reliability.setdefault(source_id, 1.0)
    return reliability


def candidate_reliability(candidate: Candidate, reliability: dict[str, float]) -> float:
    if not candidate.source_ids:
        return 1.0
    return min(reliability.get(source_id, 1.0) for source_id in candidate.source_ids)


def stale_source_ids(
    profile: dict[str, Any],
    observations: list[Observation],
    now: str,
) -> list[str]:
    """Sources flagged stale manually or older than their wave's max_age_seconds.

    A wave that declares max_age_seconds counts as stale unless at least one of
    its observations carries a parseable timestamp within the age limit. `now`
    is a free-form round label, so an unparseable one leaves every age unknown.
    """
    stale: set[str] = set()
    for observation in observations:
        if observation.metadata.get("stale") or observation.values.get("stale"):
            stale.add(observation.wave_id or observation.id)

    youngest_age: dict[str, float] = {}
    now_time = _parse_time_or_none(now)
    for observation in observations:
        if now_time is None or not observation.wave_id:
            continue
        observed = observation.observed_at or observation.window_end
        if not observed:
            continue
        observed_time = _parse_time_or_none(str(observed))
        if observed_time is None:
            continue
        age = (now_time - observed_time).total_seconds()
        current = youngest_age.get(observation.wave_id)
        if current is None or age < current:
            youngest_age[observation.wave_id] = age

    for wave in profile.get("waves") or []:
        wave_id = str(wave.get("id", ""))
        if not wave_id:
            continue
        if wave.get("stale"):
            stale.add(wave_id)
        max_age = wave.get("max_age_seconds")
        if max_age is None:
            continue
        age = youngest_age.get(wave_id)
        if age is None or age > float(max_age):
            stale.add(wave_id)
    return sorted(stale)


def _parse_time_or_none(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
