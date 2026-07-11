"""Condensed decision summary: many signals in, one low-entropy signal out.

The pack is what a downstream LLM (or human) should read instead of the full
report. Every omission is recorded under "omitted" — nothing is dropped
silently — and sensitive keys are always redacted.
"""

from __future__ import annotations

import json
from typing import Any

from .redaction import redact_value


def build_context_pack(
    report: dict[str, Any],
    *,
    max_bytes: int = 8000,
    top_evidence: int = 5,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    decision = report.get("decision") or {}
    action = decision.get("action")
    winner_ids = set(
        [decision["selected_candidate_id"]]
        if decision.get("selected_candidate_id")
        else decision.get("selected_candidate_ids") or []
    )
    evidence_entries = sorted(
        (
            _evidence_entry(item)
            for item in report.get("evidence") or []
            if item.get("candidate_id") in winner_ids
        ),
        key=lambda entry: (
            -(float(entry.get("strength", 0.0)) * float(entry.get("confidence", 1.0))),
            json.dumps(entry, sort_keys=True, default=str),
        ),
    )
    omitted: dict[str, int] = {}
    included = evidence_entries[: max(0, top_evidence)]
    if len(evidence_entries) > len(included):
        omitted["evidence"] = len(evidence_entries) - len(included)

    pack: dict[str, Any] = {
        "kind": "splot.context_pack",
        "provenance": {
            "splot_version": report.get("splot_version"),
            "profile_id": report.get("profile_id"),
            "profile_digest": report.get("profile_digest"),
            "input_digest": report.get("input_digest"),
            "mode": report.get("mode"),
            "objective_id": report.get("objective_id"),
            "created_at": report.get("created_at"),
        },
        "decision": {
            "status": decision.get("status"),
            "selected_candidate_id": decision.get("selected_candidate_id"),
            "selected_candidate_ids": decision.get("selected_candidate_ids") or [],
            "selected_source_ids": (decision.get("metadata") or {}).get("selected_source_ids") or [],
            "action": action,
            "confidence": decision.get("confidence"),
            "explanation": decision.get("explanation"),
            "policy_reason": decision.get("policy_reason"),
            "required_human_inputs": decision.get("required_human_inputs") or [],
        },
        "uncertainty": report.get("uncertainty") or {},
        "evidence": included,
        "omitted": omitted,
    }
    if isinstance(action, dict) and action.get("type") == "compose":
        # The composed payload is the condensed form of a compose action; the
        # full plan stays in the report.
        pack["composed_payload"] = (action.get("plan") or {}).get("composed_payload")
        pack["decision"]["action"] = {"type": "compose"}

    pack = redact_value(pack, fields)
    omitted = pack["omitted"]
    while _byte_size(pack) > max_bytes and pack["evidence"]:
        pack["evidence"].pop()
        omitted["evidence"] = omitted.get("evidence", 0) + 1
    if _byte_size(pack) > max_bytes and "composed_payload" in pack:
        del pack["composed_payload"]
        omitted["composed_payload"] = 1
    if _byte_size(pack) > max_bytes and pack["decision"].get("explanation"):
        pack["decision"]["explanation"] = None
        omitted["explanation"] = 1
    return pack


def _evidence_entry(item: dict[str, Any]) -> dict[str, Any]:
    # Evidence ids are uuid4-based, so they are excluded to keep packs
    # byte-comparable across replays.
    return {
        "candidate_id": item.get("candidate_id"),
        "observation_id": item.get("observation_id"),
        "supports": item.get("supports") or [],
        "opposes": item.get("opposes") or [],
        "strength": item.get("strength", 0.0),
        "confidence": item.get("confidence", 1.0),
        "reasons": item.get("reasons") or [],
    }


def _byte_size(pack: dict[str, Any]) -> int:
    return len(json.dumps(pack, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8"))
