import json
import unittest
from pathlib import Path

from splot import run_round
from splot.context_pack import build_context_pack


ROOT = Path(__file__).resolve().parents[1]

PROFILE = {
    "version": 1,
    "id": "pack",
    "mode": "select_one",
    "objective": {"id": "objective"},
    "signals": [{"id": "score", "provider": "candidate.value", "field": "score", "weight": 1}],
    "decision": {"policy": "constrained_weighted_score"},
    "evidence": [{"provider": "evidence.payload"}],
}

CANDIDATES = [
    {
        "id": "a",
        "source_ids": ["source_a"],
        "payload": {
            "score": 0.9,
            "evidence": [
                {"supports": ["objective"], "strength": 0.9, "reasons": ["fresh telemetry"]},
                {"supports": ["objective"], "strength": 0.5, "reasons": ["secondary reading"]},
            ],
        },
    },
    {"id": "b", "source_ids": ["source_b"], "payload": {"score": 0.2}},
]


def _report_dict():
    result = run_round(
        PROFILE,
        candidates=CANDIDATES,
        previous_state={"session_id": "replay"},
        now="2026-06-28T12:00:00+00:00",
    )
    return result.report.to_dict()


class ContextPackTests(unittest.TestCase):
    def test_pack_carries_provenance_decision_and_uncertainty(self):
        report = _report_dict()
        pack = build_context_pack(report)

        self.assertEqual(pack["kind"], "splot.context_pack")
        self.assertEqual(pack["provenance"]["profile_digest"], report["profile_digest"])
        self.assertEqual(pack["provenance"]["input_digest"], report["input_digest"])
        self.assertEqual(pack["decision"]["selected_candidate_id"], "a")
        self.assertEqual(pack["decision"]["selected_source_ids"], ["source_a"])
        self.assertEqual(pack["uncertainty"], report["uncertainty"])
        self.assertEqual(pack["omitted"], {})
        self.assertEqual(pack["evidence"][0]["reasons"], ["fresh telemetry"])

    def test_pack_records_omissions_instead_of_truncating(self):
        report = _report_dict()
        pack = build_context_pack(report, top_evidence=1)
        self.assertEqual(pack["omitted"], {"evidence": 1})
        self.assertEqual(len(pack["evidence"]), 1)

        tight = build_context_pack(report, max_bytes=1200)
        self.assertEqual(tight["omitted"].get("evidence"), 2)
        self.assertEqual(tight["evidence"], [])
        self.assertLessEqual(
            len(json.dumps(tight, sort_keys=True, ensure_ascii=False).encode("utf-8")), 1200
        )

    def test_pack_redacts_by_default_and_by_field(self):
        report = _report_dict()
        report["decision"]["metadata"]["token"] = "hunter2"
        pack = build_context_pack(report, fields=["decision.explanation"])

        self.assertEqual(pack["decision"]["explanation"], "[REDACTED]")
        self.assertNotIn("hunter2", json.dumps(pack))

    def test_pack_is_byte_identical_across_replays(self):
        first = build_context_pack(_report_dict())
        second = build_context_pack(_report_dict())

        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        )

    def test_compose_mode_includes_composed_payload(self):
        result = run_round(
            profile=ROOT / "examples/profiles/contract-composer",
            candidates=[
                {
                    "id": "intro_a",
                    "payload": {
                        "section": "intro",
                        "goal_fit": 1,
                        "completeness": 1,
                        "legal_risk": 0,
                        "style_consistency": 1,
                        "no_contradictions": True,
                        "required_definitions_present": True,
                        "jurisdiction_compatible": True,
                    },
                }
            ],
            now="2026-06-28T12:00:00+00:00",
        )
        pack = build_context_pack(result.report.to_dict())

        self.assertEqual(pack["decision"]["action"], {"type": "compose"})
        self.assertIn("intro", pack["composed_payload"])

    def test_postprocessor_embeds_pack_in_decision(self):
        profile = {**PROFILE, "postprocess": [{"provider": "postprocess.context_pack"}]}
        result = run_round(profile, candidates=CANDIDATES, now="2026-06-28T12:00:00+00:00")

        report_pack = result.report.decision["metadata"]["context_pack"]
        self.assertEqual(report_pack["kind"], "splot.context_pack")
        # The Decision object handed to adapters carries the same pack.
        self.assertEqual(result.decision.metadata["context_pack"], report_pack)


if __name__ == "__main__":
    unittest.main()
