import unittest

from splot import run_round


class ProviderHookTests(unittest.TestCase):
    def test_observation_candidate_provider_scorer_and_renderer(self):
        profile = {
            "version": 1,
            "id": "hooks",
            "mode": "select_one",
            "objective": {"id": "objective"},
            "observation_providers": [
                {
                    "provider": "observations.static",
                    "items": [
                        {
                            "id": "obs",
                            "values": {
                                "candidates": [
                                    {"id": "a", "payload": {"score": 0.8}},
                                    {"id": "b", "payload": {"score": 0.4}},
                                ]
                            },
                        }
                    ],
                }
            ],
            "candidate_providers": [
                {"provider": "candidates.from_observation_values", "field": "candidates"}
            ],
            "signals": [
                {"id": "score", "provider": "candidate.value", "field": "score", "weight": 1}
            ],
            "scoring": {"provider": "score.weighted"},
            "decision": {
                "policy": "constrained_weighted_score",
                "renderer": "decision.render_summary",
            },
        }

        result = run_round(profile, now="2026-06-28T12:00:00+00:00")

        self.assertEqual(result.decision.selected_candidate_id, "a")
        self.assertEqual(result.decision.action["type"], "summary")
        self.assertEqual(len(result.report.observations), 1)
        self.assertEqual(len(result.report.candidates), 2)


if __name__ == "__main__":
    unittest.main()

