import unittest

from splot import run_round


BASE_PROFILE = {
    "version": 1,
    "id": "constraints",
    "mode": "select_one",
    "objective": {"id": "objective"},
    "signals": [{"id": "score", "provider": "candidate.value", "field": "score", "weight": 1}],
    "decision": {"policy": "constrained_weighted_score"},
}


class ConstraintTests(unittest.TestCase):
    def test_weighted_score_reports_constraints_but_does_not_block(self):
        profile = {
            **BASE_PROFILE,
            "decision": {"policy": "weighted_score"},
            "constraints": [
                {
                    "id": "available",
                    "provider": "candidate.flag",
                    "field": "available",
                    "severity": "block",
                    "reason": "blocked",
                }
            ],
        }

        result = run_round(
            profile,
            candidates=[
                {"id": "blocked_high", "payload": {"score": 1, "available": False}},
                {"id": "eligible_low", "payload": {"score": 0.1, "available": True}},
            ],
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertEqual(result.decision.selected_candidate_id, "blocked_high")
        self.assertFalse(result.report.to_dict()["evaluations"][0]["eligible"])

    def test_block_warn_human_and_penalize_constraints(self):
        profile = {
            **BASE_PROFILE,
            "constraints": [
                {
                    "id": "available",
                    "provider": "candidate.flag",
                    "field": "available",
                    "severity": "block",
                    "reason": "blocked",
                },
                {
                    "id": "warning",
                    "provider": "candidate.flag",
                    "field": "warn_ok",
                    "severity": "warn",
                    "reason": "warned",
                },
                {
                    "id": "human",
                    "provider": "candidate.flag",
                    "field": "human_ok",
                    "severity": "human_decision",
                    "reason": "human needed",
                },
                {
                    "id": "penalty",
                    "provider": "candidate.flag",
                    "field": "penalty_ok",
                    "severity": "penalize",
                    "penalty": 0.2,
                    "reason": "penalized",
                },
            ],
        }

        result = run_round(
            profile,
            candidates=[
                {
                    "id": "blocked",
                    "payload": {
                        "score": 1,
                        "available": False,
                        "warn_ok": True,
                        "human_ok": True,
                        "penalty_ok": True,
                    },
                },
                {
                    "id": "human",
                    "payload": {
                        "score": 0.9,
                        "available": True,
                        "warn_ok": False,
                        "human_ok": False,
                        "penalty_ok": False,
                    },
                },
            ],
            now="2026-06-28T12:00:00+00:00",
        )

        blocked_eval = result.report.to_dict()["evaluations"][0]
        human_eval = result.report.to_dict()["evaluations"][1]
        self.assertFalse(blocked_eval["eligible"])
        self.assertEqual(result.decision.status, "needs_human_decision")
        self.assertIn("warned", human_eval["warnings"])
        self.assertLess(human_eval["score"], human_eval["raw_score"])


if __name__ == "__main__":
    unittest.main()
