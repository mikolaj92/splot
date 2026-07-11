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

    def test_feedback_handler_updates_reliability_of_sources(self):
        candidates = [{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}]
        first = run_round(
            BASE_PROFILE,
            candidates=candidates,
            now="2026-06-28T12:00:00+00:00",
        )
        self.assertEqual(first.decision.metadata["selected_source_ids"], ["source_a"])

        second = run_round(
            BASE_PROFILE,
            candidates=candidates,
            previous_state=first.state,
            feedback={"decision_id": first.decision.id, "accepted": False},
            now="2026-06-28T12:01:00+00:00",
        )

        self.assertLess(second.state.source_reliability["source_a"], 1.0)
        self.assertNotIn("a", second.state.source_reliability)

    def test_feedback_handler_ignores_missing_acceptance(self):
        candidates = [{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}]
        first = run_round(
            BASE_PROFILE,
            candidates=candidates,
            now="2026-06-28T12:00:00+00:00",
        )
        second = run_round(
            BASE_PROFILE,
            candidates=candidates,
            previous_state=first.state,
            feedback={"decision_id": first.decision.id},
            now="2026-06-28T12:01:00+00:00",
        )

        self.assertNotIn("source_a", second.state.source_reliability)

    def test_feedback_handler_acceptance_recovers_reliability(self):
        candidates = [{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}]
        first = run_round(
            BASE_PROFILE,
            candidates=candidates,
            now="2026-06-28T12:00:00+00:00",
        )
        rejected = run_round(
            BASE_PROFILE,
            candidates=candidates,
            previous_state=first.state,
            feedback={"decision_id": first.decision.id, "accepted": False},
            now="2026-06-28T12:01:00+00:00",
        )
        accepted = run_round(
            BASE_PROFILE,
            candidates=candidates,
            previous_state=rejected.state,
            feedback={"decision_id": rejected.decision.id, "accepted": True},
            now="2026-06-28T12:02:00+00:00",
        )

        self.assertGreater(
            accepted.state.source_reliability["source_a"],
            rejected.state.source_reliability["source_a"],
        )

    def test_low_evidence_confidence_lifts_belief_uncertainty(self):
        profile = {**BASE_PROFILE, "evidence": [{"provider": "evidence.payload"}]}
        result = run_round(
            profile,
            candidates=[
                {
                    "id": "a",
                    "payload": {
                        "score": 0.9,
                        "evidence": {"supports": ["objective"], "strength": 1.0, "confidence": 0.2},
                    },
                }
            ],
            now="2026-06-28T12:00:00+00:00",
        )
        belief = result.report.belief

        self.assertAlmostEqual(belief["candidate_beliefs"]["a"]["evidence_confidence"], 0.2)
        self.assertGreaterEqual(belief["uncertainty"], 0.8)

    def test_unreliable_source_lifts_belief_uncertainty(self):
        profile = {**BASE_PROFILE, "waves": [{"id": "source_a", "reliability": 0.4}]}
        result = run_round(
            profile,
            candidates=[{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )
        belief = result.report.belief

        self.assertAlmostEqual(belief["candidate_beliefs"]["a"]["source_reliability_min"], 0.4)
        self.assertGreaterEqual(belief["uncertainty"], 0.6)

    def test_uncertainty_components_explain_value(self):
        profile = {**BASE_PROFILE, "waves": [{"id": "source_a", "reliability": 0.4}]}
        result = run_round(
            profile,
            candidates=[{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )
        uncertainty = result.report.uncertainty

        self.assertAlmostEqual(uncertainty["components"]["source_reliability_gap"], 0.6)
        self.assertEqual(uncertainty["dominant_component"], "source_reliability_gap")
        self.assertAlmostEqual(uncertainty["value"], max(uncertainty["components"].values()))

    def test_silent_sources_reported(self):
        profile = {**BASE_PROFILE, "waves": [{"id": "source_a"}, {"id": "source_b"}]}
        result = run_round(
            profile,
            observations=[{"id": "obs", "wave_id": "source_a", "values": {"score": 1}}],
            candidates=[{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertEqual(result.report.uncertainty["silent_sources"], ["source_b"])

    def test_input_disagreement_reported(self):
        profile = {**BASE_PROFILE, "evidence": [{"provider": "evidence.payload"}]}
        result = run_round(
            profile,
            candidates=[
                {
                    "id": "a",
                    "payload": {
                        "score": 0.9,
                        "evidence": [
                            {"supports": ["objective"], "strength": 0.6},
                            {"opposes": ["objective"], "strength": 0.4},
                        ],
                    },
                }
            ],
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertAlmostEqual(
            result.report.belief["candidate_beliefs"]["a"]["input_disagreement"], 0.4
        )

    def test_contested_candidate_conflict(self):
        profile = {**BASE_PROFILE, "evidence": [{"provider": "evidence.payload"}]}
        result = run_round(
            profile,
            candidates=[
                {
                    "id": "a",
                    "payload": {
                        "score": 0.9,
                        "evidence": [
                            {"supports": ["objective"], "strength": 0.6},
                            {"opposes": ["objective"], "strength": 0.4},
                        ],
                    },
                }
            ],
            now="2026-06-28T12:00:00+00:00",
        )
        conflicts = result.report.belief["conflicts"]

        contested = [item for item in conflicts if item["kind"] == "contested_candidate"]
        self.assertEqual(contested[0]["candidate_ids"], ["a"])

    def test_contested_threshold_is_configurable(self):
        profile = {
            **BASE_PROFILE,
            "evidence": [{"provider": "evidence.payload"}],
            "belief": {"contested_threshold": 0.5},
        }
        result = run_round(
            profile,
            candidates=[
                {
                    "id": "a",
                    "payload": {
                        "score": 0.9,
                        "evidence": [
                            {"supports": ["objective"], "strength": 0.6},
                            {"opposes": ["objective"], "strength": 0.4},
                        ],
                    },
                }
            ],
            now="2026-06-28T12:00:00+00:00",
        )
        conflicts = result.report.belief["conflicts"]

        self.assertFalse([item for item in conflicts if item["kind"] == "contested_candidate"])

    def test_conflicts_surface_in_belief_and_persist_across_rounds(self):
        close_candidates = [
            {"id": "a", "payload": {"score": 0.9}},
            {"id": "b", "payload": {"score": 0.89}},
        ]
        first = run_round(
            BASE_PROFILE,
            candidates=close_candidates,
            now="2026-06-28T12:00:00+00:00",
        )
        self.assertTrue(
            [item for item in first.report.belief["conflicts"] if item["kind"] == "close_scores"]
        )

        repeat = run_round(
            BASE_PROFILE,
            candidates=close_candidates,
            previous_state=first.state,
            now="2026-06-28T12:01:00+00:00",
        )
        close = [item for item in repeat.report.belief["conflicts"] if item["kind"] == "close_scores"]
        self.assertEqual(len(close), 1)
        self.assertEqual(close[0]["score_margin"], 0.01)

        # Conflicts reflect current uncertainty conditions computed in belief each round.
        # They are not stored as history inside state (state holds only continuity for the next reduction step).
        # When conditions resolve, the next round produces an empty conflicts list for that kind.
        clear_round = run_round(
            BASE_PROFILE,
            candidates=[{"id": "a", "payload": {"score": 1}}],
            previous_state=repeat.state,
            now="2026-06-28T12:02:00+00:00",
        )
        self.assertFalse(
            [item for item in clear_round.report.belief["conflicts"] if item["kind"] == "close_scores"]
        )
        candidates = [{"id": "a", "payload": {"score": 0.9}}]
        first = run_round(BASE_PROFILE, candidates=candidates, now="2026-06-28T12:00:00+00:00")
        second = run_round(
            BASE_PROFILE,
            candidates=candidates,
            previous_state=first.state,
            now="2026-06-28T12:01:00+00:00",
        )

        belief = second.report.belief
        self.assertEqual(belief["candidate_beliefs"]["a"]["rounds_seen"], 2)
        self.assertEqual(belief["metadata"]["winner_streak"], 2)
        last_entry = belief["history"][-1]
        self.assertEqual(last_entry["top_candidate_id"], "a")
        self.assertEqual(last_entry["uncertainty"], belief["uncertainty"])

    def test_belief_smoothing_blends_previous_rounds(self):
        profile = {
            **BASE_PROFILE,
            "belief": {"smoothing": 0.5},
            "evidence": [{"provider": "evidence.payload"}],
        }

        def candidates(strength):
            return [
                {
                    "id": "a",
                    "payload": {
                        "score": 0.9,
                        "evidence": {"supports": ["objective"], "strength": strength},
                    },
                }
            ]

        first = run_round(profile, candidates=candidates(0.8), now="2026-06-28T12:00:00+00:00")
        self.assertEqual(first.report.belief["candidate_beliefs"]["a"]["support"], 0.8)

        second = run_round(
            profile,
            candidates=candidates(0.4),
            previous_state=first.state,
            now="2026-06-28T12:01:00+00:00",
        )
        # 0.5 * previous (0.8) + 0.5 * current (0.4)
        self.assertEqual(second.report.belief["candidate_beliefs"]["a"]["support"], 0.6)

    def test_winner_streak_reduces_uncertainty(self):
        profile = {**BASE_PROFILE, "belief": {"stability_step": 0.05, "stability_cap": 0.08}}
        candidates = [{"id": "a", "payload": {"score": 0.7}}]

        result = run_round(profile, candidates=candidates, now="2026-06-28T12:00:00+00:00")
        base_uncertainty = result.report.belief["uncertainty"]
        self.assertNotIn("uncertainty_reduction", result.report.belief["metadata"])

        for minute in (1, 2):
            result = run_round(
                profile,
                candidates=candidates,
                previous_state=result.state,
                now=f"2026-06-28T12:0{minute}:00+00:00",
            )

        belief = result.report.belief
        self.assertEqual(belief["metadata"]["winner_streak"], 3)
        # streak 3 -> (3 - 1) * 0.05 capped at 0.08
        reduction = belief["metadata"]["uncertainty_reduction"]
        self.assertEqual(reduction["value"], 0.08)
        self.assertEqual(reduction["reason"], "top candidate stable for 3 rounds")
        self.assertEqual(belief["uncertainty"], round(base_uncertainty - 0.08, 6))
        self.assertEqual(result.report.uncertainty["reduction"], reduction)

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

    def test_old_observation_marks_source_stale(self):
        profile = {
            **BASE_PROFILE,
            "waves": [{"id": "source_a", "max_age_seconds": 60}],
            "uncertainty": {"when_source_stale": "penalize", "stale_penalty": 0.5},
        }

        result = run_round(
            profile,
            observations=[
                {"id": "obs", "wave_id": "source_a", "observed_at": "2026-06-28T11:50:00+00:00"}
            ],
            candidates=[{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertEqual(result.report.uncertainty["stale_sources"], ["source_a"])
        self.assertAlmostEqual(result.decision.confidence, 0.5)

    def test_fresh_observation_is_not_stale(self):
        profile = {
            **BASE_PROFILE,
            "waves": [{"id": "source_a", "max_age_seconds": 60}],
            "uncertainty": {"when_source_stale": "penalize"},
        }

        result = run_round(
            profile,
            observations=[
                {"id": "obs", "wave_id": "source_a", "observed_at": "2026-06-28T11:59:30+00:00"}
            ],
            candidates=[{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertEqual(result.report.uncertainty["stale_sources"], [])
        self.assertAlmostEqual(result.decision.confidence, 1.0)

    def test_wave_with_max_age_and_no_observations_is_stale(self):
        profile = {
            **BASE_PROFILE,
            "waves": [{"id": "source_a", "max_age_seconds": 60}],
        }

        result = run_round(
            profile,
            candidates=[{"id": "a", "source_ids": ["source_a"], "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertEqual(result.report.uncertainty["stale_sources"], ["source_a"])

    def test_candidate_without_sources_depends_on_all_sources(self):
        profile = {
            **BASE_PROFILE,
            "uncertainty": {"when_source_stale": "block"},
        }

        result = run_round(
            profile,
            observations=[{"id": "obs", "wave_id": "source_a", "values": {"stale": True}}],
            candidates=[{"id": "a", "payload": {"score": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertNotEqual(result.decision.status, "selected")
        self.assertIn("stale source", result.report.evaluations[0]["rejected_reasons"][0])

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
