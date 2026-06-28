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
    conflicts: list[dict[str, Any]] = []
    blocked_by_slot: dict[str, list[dict[str, Any]]] = {}
    human_by_slot: dict[str, list[str]] = {}

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
                blocked = {"candidate_id": evaluation.candidate_id, "reasons": evaluation.rejected_reasons}
                rejected.append(blocked)
                blocked_by_slot.setdefault(section_id, []).append(blocked)
            if evaluation.human_decisions:
                human_by_slot.setdefault(section_id, []).extend(evaluation.human_decisions)
        if not eligible:
            if section.get("required", False):
                missing_required.append(section_id)
            continue
        best = sorted(eligible, key=lambda item: item.score, reverse=True)[0]
        selected_by_section[section_id] = best.candidate_id
        warnings.extend(best.warnings)
        human_decisions.extend(best.human_decisions)

    selected_ids = list(selected_by_section.values())
    selected_set = set(selected_ids)
    for candidate in candidates:
        if candidate.id not in selected_set:
            continue
        missing_dependencies = [item for item in candidate.dependencies if item not in selected_set]
        if missing_dependencies:
            conflicts.append(
                {
                    "kind": "missing_dependency",
                    "candidate_id": candidate.id,
                    "missing": missing_dependencies,
                    "scope": "dependency",
                }
            )

    for rule in (profile.get("composition") or {}).get("compatibility") or []:
        conflict = _evaluate_compatibility_rule(rule, selected_set)
        if conflict:
            conflict["scope"] = "compatibility"
            conflicts.append(conflict)

    for rule in (profile.get("composition") or {}).get("global_constraints") or []:
        conflict = _evaluate_compatibility_rule(rule, selected_set)
        if conflict:
            conflict["scope"] = "global"
            conflicts.append(conflict)

    for conflict in conflicts:
        severity = conflict.get("severity", "human_decision")
        reason = conflict.get("reason", conflict["kind"])
        if severity == "warn":
            warnings.append(reason)
        elif severity == "block":
            rejected.append({"candidate_id": None, "reasons": [reason]})
        else:
            human_decisions.append(reason)

    plan = {
        "unit": (profile.get("composition") or {}).get("unit", "section"),
        "selected_by_section": selected_by_section,
        "selected_candidate_by_slot": selected_by_section,
        "missing_required": missing_required,
        "missing_required_slots": missing_required,
        "blocked_candidates_by_slot": blocked_by_slot,
        "human_decisions_by_slot": human_by_slot,
        "global_conflicts": [item for item in conflicts if item.get("scope") in {"global", "dependency"}],
        "compatibility_explanations": conflicts,
        "composed_payload_schema_version": 1,
        "composed_payload": _composed_payload(candidates, selected_by_section),
        "conflicts": conflicts,
    }
    status = "composed"
    if any(item.get("severity") == "block" for item in conflicts):
        status = "conflict"
    elif missing_required or human_decisions:
        status = "needs_human_decision"
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


def _composed_payload(
    candidates: list[Candidate],
    selected_by_section: dict[str, str],
) -> dict[str, Any]:
    by_id = {candidate.id: candidate for candidate in candidates}
    return {
        section: by_id[candidate_id].payload
        for section, candidate_id in selected_by_section.items()
        if candidate_id in by_id
    }


def _evaluate_compatibility_rule(rule: dict[str, Any], selected_ids: set[str]) -> dict[str, Any] | None:
    severity = rule.get("severity", "human_decision")
    reason = rule.get("reason") or rule.get("id") or "composition constraint"
    if "forbid_together" in rule:
        candidate_ids = set(rule["forbid_together"])
        if candidate_ids.issubset(selected_ids):
            return {
                "kind": "forbid_together",
                "candidate_ids": sorted(candidate_ids),
                "severity": severity,
                "reason": reason,
            }
    if "require_together" in rule:
        candidate_ids = set(rule["require_together"])
        overlap = candidate_ids & selected_ids
        if overlap and not candidate_ids.issubset(selected_ids):
            return {
                "kind": "require_together",
                "candidate_ids": sorted(candidate_ids),
                "selected": sorted(overlap),
                "missing": sorted(candidate_ids - selected_ids),
                "severity": severity,
                "reason": reason,
            }
    return None
