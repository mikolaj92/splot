from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ReportAuditFinding:
    severity: str
    message: str

    def format(self) -> str:
        return f"{self.severity}: {self.message}"


def audit_report(report: dict[str, Any]) -> list[ReportAuditFinding]:
    findings: list[ReportAuditFinding] = []
    for key in (
        "round_id",
        "profile_id",
        "mode",
        "objective_id",
        "decision",
        "evaluations",
        "evidence",
        "belief",
        "updated_state",
    ):
        if key not in report:
            findings.append(ReportAuditFinding("error", f"missing report field: {key}"))

    decision = report.get("decision") or {}
    updated_state = report.get("updated_state") or {}
    state_decision = updated_state.get("previous_decision") or {}
    if decision.get("id") and state_decision.get("id") and decision["id"] != state_decision["id"]:
        findings.append(ReportAuditFinding("error", "updated_state.previous_decision does not match decision"))

    evaluations = report.get("evaluations") or []
    belief = report.get("belief") or {}
    candidate_beliefs = belief.get("candidate_beliefs") or {}
    evaluation_ids = {item.get("candidate_id") for item in evaluations}
    belief_ids = set(candidate_beliefs)
    missing_beliefs = sorted(str(item) for item in evaluation_ids - belief_ids if item)
    if missing_beliefs:
        findings.append(
            ReportAuditFinding("error", f"belief missing candidate(s): {', '.join(missing_beliefs)}")
        )

    evidence = report.get("evidence") or []
    evaluated_with_signals = [item for item in evaluations if item.get("signals")]
    if evaluated_with_signals and not evidence:
        findings.append(ReportAuditFinding("error", "evaluations have signals but report has no evidence"))

    if not report.get("policy_reasons"):
        findings.append(ReportAuditFinding("warn", "policy_reasons is empty"))
    if "value" not in (report.get("uncertainty") or {}):
        findings.append(ReportAuditFinding("warn", "uncertainty.value is missing"))
    return findings


def compare_replay(original: dict[str, Any], replayed: dict[str, Any]) -> list[ReportAuditFinding]:
    findings: list[ReportAuditFinding] = []
    original_decision = original.get("decision") or {}
    replayed_decision = replayed.get("decision") or {}
    for key in ("status", "selected_candidate_id", "selected_candidate_ids"):
        if original_decision.get(key) != replayed_decision.get(key):
            findings.append(
                ReportAuditFinding(
                    "error",
                    f"replay decision {key} differs: {original_decision.get(key)!r} != {replayed_decision.get(key)!r}",
                )
            )
    return findings

