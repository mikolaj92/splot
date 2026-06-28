from __future__ import annotations

from typing import Any

from .models import SplotState, Candidate, CandidateEvaluation, Decision, new_id


def decide_composition(
    profile: dict[str, Any],
    candidates: list[Candidate],
    evaluations: list[CandidateEvaluation],
    state: SplotState,
    now: str,
) -> tuple[Decision, dict[str, Any]]:
    objective_id = str((profile.get("objective") or {}).get("id", profile.get("id", "")))
    previous = state.previous_decision or {}
    sections = (profile.get("composition") or {}).get("sections") or []
    selected_by_section: dict[str, str] = {}
    missing_required: list[str] = []
    warnings: list[str] = []
    human_decisions: list[str] = []
    rejected: list[dict[str, Any]] = []

    for section in sections:
        section_id = str(section["id"])
        section_candidates = [
            evaluation
            for evaluation in evaluations
            if _candidate_section(candidates, evaluation.candidate_id) == section_id
        ]
        eligible = [evaluation for evaluation in section_candidates if evaluation.eligible]
        for evaluation in section_candidates:
            if evaluation.rejected_reasons:
                rejected.append({"candidate_id": evaluation.candidate_id, "reasons": evaluation.rejected_reasons})
        if not eligible:
            if section.get("required", False):
                missing_required.append(section_id)
            continue
        best = sorted(eligible, key=lambda item: item.score, reverse=True)[0]
        selected_by_section[section_id] = best.candidate_id
        warnings.extend(best.warnings)
        human_decisions.extend(best.human_decisions)

    plan = {
        "unit": (profile.get("composition") or {}).get("unit", "section"),
        "selected_by_section": selected_by_section,
        "missing_required": missing_required,
    }
    status = "composed"
    if missing_required or human_decisions:
        status = "needs_human_decision"
    selected_ids = list(selected_by_section.values())
    confidence = _mean(
        [evaluation.score for evaluation in evaluations if evaluation.candidate_id in set(selected_ids)]
    )
    decision = Decision(
        id=new_id("decision"),
        status=status,
        objective_id=objective_id,
        selected_candidate_id=None,
        selected_candidate_ids=selected_ids,
        previous_decision_id=previous.get("id"),
        action={"type": "compose", "plan": plan},
        confidence=confidence,
        uncertainty=1.0 - confidence,
        policy_reason="section_by_section_composition",
        explanation=f"selected {len(selected_ids)} composition parts",
        rejected_candidates=rejected,
        warnings=warnings + [f"missing required section: {item}" for item in missing_required],
        required_human_inputs=human_decisions
        + [f"missing required section: {item}" for item in missing_required],
        created_at=now,
    )
    return decision, {"policy": "section_by_section_composition", "decision": status, **plan}


def _candidate_section(candidates: list[Candidate], candidate_id: str) -> str | None:
    for candidate in candidates:
        if candidate.id == candidate_id:
            return candidate.payload.get("section") or candidate.payload.get("slot")
    return None


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0

