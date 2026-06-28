import unittest

from splot import audit_report, compare_replay, run_round


class ReportTests(unittest.TestCase):
    def test_report_includes_rejections_contributions_stability_and_uncertainty(self):
        result = run_round(
            {
                "version": 1,
                "id": "report",
                "mode": "select_one",
                "objective": {"id": "objective"},
                "signals": [
                    {"id": "score", "provider": "candidate.value", "field": "score", "weight": 1, "min": 0.5}
                ],
                "decision": {"policy": "constrained_weighted_score"},
                "stability": {"policy": "none"},
            },
            candidates=[
                {"id": "bad", "payload": {"score": 0.2}},
                {"id": "good", "payload": {"score": 0.8}},
            ],
            now="2026-06-28T12:00:00+00:00",
        )

        report = result.report.to_dict()
        self.assertEqual(report["decision"]["selected_candidate_id"], "good")
        self.assertEqual(report["evaluations"][1]["signals"][0]["contribution"], 0.8)
        self.assertTrue(report["evaluations"][0]["rejected_reasons"])
        self.assertEqual(report["stability"]["policy"], "none")
        self.assertIn("value", report["uncertainty"])

    def test_report_audit_and_replay_compare(self):
        result = run_round(
            {
                "version": 1,
                "id": "audit",
                "mode": "select_one",
                "objective": {"id": "objective"},
                "signals": [{"id": "score", "provider": "candidate.value", "field": "score", "weight": 1}],
                "decision": {"policy": "constrained_weighted_score"},
            },
            candidates=[{"id": "good", "payload": {"score": 0.8}}],
            now="2026-06-28T12:00:00+00:00",
        )
        report = result.report.to_dict()

        self.assertEqual(audit_report(report), [])
        self.assertEqual(compare_replay(report, report), [])

        broken = {**report, "evidence": []}
        self.assertTrue(audit_report(broken))


if __name__ == "__main__":
    unittest.main()
