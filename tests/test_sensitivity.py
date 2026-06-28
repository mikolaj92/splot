import unittest

from splot.runtime import run_round
from splot.sensitivity import explain_weights, format_weight_explanation


class SensitivityTests(unittest.TestCase):
    def test_explain_weights_reports_margin_and_top_contributors(self):
        result = run_round(
            {
                "version": 1,
                "id": "weights",
                "mode": "select_one",
                "objective": {"id": "objective"},
                "signals": [
                    {"id": "fit", "provider": "candidate.value", "field": "fit", "weight": 0.75},
                    {"id": "risk", "provider": "candidate.value", "field": "risk", "prefer": "lower", "weight": 0.25},
                ],
                "decision": {"policy": "constrained_weighted_score"},
            },
            candidates=[
                {"id": "a", "payload": {"fit": 1.0, "risk": 0.0}},
                {"id": "b", "payload": {"fit": 0.5, "risk": 0.0}},
            ],
            now="2026-06-28T12:00:00+00:00",
        )

        summary = explain_weights(result.report.to_dict())

        self.assertEqual(summary["winner"], "a")
        self.assertEqual(summary["runner_up"], "b")
        self.assertGreater(summary["score_margin"], 0)
        self.assertEqual(summary["top_signal_contributors"][0]["id"], "fit")
        self.assertIn("top_signal_contributors", format_weight_explanation(summary))


if __name__ == "__main__":
    unittest.main()
