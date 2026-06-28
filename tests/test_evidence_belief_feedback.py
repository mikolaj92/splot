import unittest

from splot import MemoryStateStore, SplotState, builtin_registry, run_round
from splot.storage import JsonFileStateStore


BASE_PROFILE = {
    "version": 1,
    "id": "trace",
    "mode": "select_one",
    "objective": {"id": "objective"},
    "signals": [{"id": "score", "provider": "candidate.value", "field": "score", "weight": 1}],
    "decision": {"policy": "constrained_weighted_score"},
    "feedback_handlers": [{"provider": "feedback.acceptance_reliability"}],
}


class EvidenceBeliefFeedbackTests(unittest.TestCase):
    def test_round_report_includes_evidence_and_belief(self):
        result = run_round(
            BASE_PROFILE,
            candidates=[
                {"id": "a", "source_ids": ["source_a"], "payload": {"score": 0.9}},
                {"id": "b", "source_ids": ["source_b"], "payload": {"score": 0.3}},
            ],
            now="2026-06-28T12:00:00+00:00",
        )
        report = result.report.to_dict()

        self.assertTrue(report["evidence"])
        self.assertEqual(report["belief"]["candidate_beliefs"]["a"]["score"], 0.9)
        self.assertIn("last_belief", result.state.metadata)
        self.assertTrue(result.state.evidence_history)

    def test_payload_evidence_provider_is_allowed(self):
        profile = {**BASE_PROFILE, "evidence": [{"provider": "evidence.payload"}]}
        result = run_round(
            profile,
            candidates=[
                {
                    "id": "a",
                    "payload": {
                        "score": 0.9,
                        "evidence": {
                            "supports": ["objective"],
                            "strength": 0.8,
                            "reasons": ["payload evidence"],
                        },
                    },
                }
            ],
            registry=builtin_registry(),
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertEqual(result.report.evidence[0]["reasons"], ["payload evidence"])

    def test_feedback_handler_updates_reliability(self):
        first = run_round(
            BASE_PROFILE,
            candidates=[{"id": "a", "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )
        second = run_round(
            BASE_PROFILE,
            candidates=[{"id": "a", "payload": {"score": 1}}],
            previous_state=first.state,
            feedback={"decision_id": first.decision.id, "accepted": False},
            now="2026-06-28T12:01:00+00:00",
        )

        self.assertLess(second.state.source_reliability["a"], 1.0)

    def test_stale_source_can_request_more_evidence(self):
        profile = {
            **BASE_PROFILE,
            "uncertainty": {"when_source_stale": "request_more_evidence"},
        }

        result = run_round(
            profile,
            observations=[{"id": "obs", "wave_id": "source_a", "values": {"stale": True}}],
            candidates=[{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertEqual(result.decision.status, "request_more_evidence")
        self.assertEqual(result.report.uncertainty["stale_sources"], ["source_a"])

    def test_state_stores_round_trip(self):
        memory = MemoryStateStore()
        state = SplotState(session_id="s")
        memory.save(state)
        self.assertEqual(memory.load("s").session_id, "s")

        # Path-backed store is covered lightly; JSON details are covered by state tests.
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            store = JsonFileStateStore(Path(tmp) / "state.json")
            store.save(state)
            self.assertEqual(store.load().session_id, "s")


if __name__ == "__main__":
    unittest.main()
