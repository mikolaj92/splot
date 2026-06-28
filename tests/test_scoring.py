import unittest

from splot import SplotState, Candidate, builtin_registry
from splot.scoring import evaluate_candidates


class ScoringTests(unittest.TestCase):
    def test_weighted_higher_lower_and_boolean(self):
        profile = {
            "signals": [
                {"id": "quality", "provider": "candidate.value", "field": "quality", "weight": 0.5},
                {
                    "id": "risk",
                    "provider": "candidate.value",
                    "field": "risk",
                    "weight": 0.3,
                    "prefer": "lower",
                },
                {
                    "id": "ready",
                    "provider": "candidate.value",
                    "field": "ready",
                    "weight": 0.2,
                    "prefer": "boolean",
                },
            ]
        }
        candidates = [
            Candidate(id="a", payload={"quality": 0.8, "risk": 0.1, "ready": True}),
            Candidate(id="b", payload={"quality": 0.7, "risk": 0.5, "ready": True}),
        ]

        evaluations = evaluate_candidates(
            profile, [], candidates, SplotState(), builtin_registry(), "2026-06-28T12:00:00+00:00"
        )

        self.assertGreater(evaluations[0].score, evaluations[1].score)
        self.assertAlmostEqual(evaluations[0].signals[1].normalized, 0.9)
        self.assertAlmostEqual(evaluations[0].signals[2].normalized, 1.0)

    def test_signal_min_threshold_blocks(self):
        profile = {
            "signals": [
                {
                    "id": "quality",
                    "provider": "candidate.value",
                    "field": "quality",
                    "weight": 1,
                    "min": 0.6,
                }
            ]
        }
        candidates = [Candidate(id="a", payload={"quality": 0.4})]

        evaluation = evaluate_candidates(
            profile, [], candidates, SplotState(), builtin_registry(), "2026-06-28T12:00:00+00:00"
        )[0]

        self.assertFalse(evaluation.eligible)
        self.assertIn("min", evaluation.rejected_reasons[0])


if __name__ == "__main__":
    unittest.main()
