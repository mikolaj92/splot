from __future__ import annotations

from typing import Any


def explain_weights(report: dict[str, Any]) -> dict[str, Any]:
    evaluations = sorted(report.get("evaluations") or [], key=lambda item: item.get("score", 0), reverse=True)
    decision = report.get("decision") or {}
    decision_selected = decision.get("selected_candidate_id")
    if not decision_selected and decision.get("selected_candidate_ids"):
        decision_selected = decision["selected_candidate_ids"][0]
    winner = next((item for item in evaluations if item.get("candidate_id") == decision_selected), None)
    winner = winner or (evaluations[0] if evaluations else {})
    runner_up = next((item for item in evaluations if item.get("candidate_id") != winner.get("candidate_id")), {})
    top_signals = sorted(
        winner.get("signals") or [],
        key=lambda item: abs(float(item.get("contribution", 0.0))),
        reverse=True,
    )
    changed_constraints = [
        {
            "candidate_id": item.get("candidate_id"),
            "constraints": [
                constraint
                for constraint in item.get("constraints") or []
                if not constraint.get("passed", True)
            ],
        }
        for item in evaluations
    ]
    changed_constraints = [item for item in changed_constraints if item["constraints"]]
    margin = None
    if winner and runner_up:
        margin = float(winner.get("score", 0.0)) - float(runner_up.get("score", 0.0))
    uncertainty = report.get("uncertainty") or {}
    return {
        "winner": winner.get("candidate_id"),
        "top_evaluated_candidate": evaluations[0].get("candidate_id") if evaluations else None,
        "runner_up": runner_up.get("candidate_id"),
        "score_margin": margin,
        "uncertainty": uncertainty.get("value"),
        "uncertainty_components": uncertainty.get("components") or {},
        "dominant_uncertainty_component": uncertainty.get("dominant_component"),
        "top_signal_contributors": [
            {
                "id": item.get("id"),
                "weight": item.get("weight"),
                "normalized": item.get("normalized"),
                "contribution": item.get("contribution"),
            }
            for item in top_signals
        ],
        "constraints_that_changed_result": changed_constraints,
        "stability": report.get("stability") or {},
        "policy_reasons": report.get("policy_reasons") or [],
    }


def format_weight_explanation(summary: dict[str, Any]) -> str:
    lines = [
        f"winner: {summary.get('winner')}",
        f"top_evaluated_candidate: {summary.get('top_evaluated_candidate')}",
        f"runner_up: {summary.get('runner_up')}",
        f"score_margin: {summary.get('score_margin')}",
        f"uncertainty: {summary.get('uncertainty')} "
        f"(dominant: {summary.get('dominant_uncertainty_component')})",
    ]
    lines.append("top_signal_contributors:")
    for item in summary.get("top_signal_contributors") or []:
        lines.append(
            f"- {item.get('id')}: contribution={item.get('contribution')} "
            f"normalized={item.get('normalized')} weight={item.get('weight')}"
        )
    if summary.get("constraints_that_changed_result"):
        lines.append("constraints_that_changed_result:")
        for item in summary["constraints_that_changed_result"]:
            lines.append(f"- {item['candidate_id']}: {len(item['constraints'])} constraint(s)")
    if summary.get("stability"):
        stability = summary["stability"]
        lines.append(f"stability: {stability.get('decision')} ({stability.get('policy')})")
    return "\n".join(lines)
