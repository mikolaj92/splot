import unittest

from splot.html_report import render_html_report
from splot.runtime import run_round


class HtmlReportTests(unittest.TestCase):
    def test_html_report_escapes_and_redacts(self):
        result = run_round(
            {
                "version": 1,
                "id": "html",
                "mode": "select_one",
                "objective": {"id": "objective"},
                "signals": [{"id": "score", "provider": "candidate.value", "field": "score", "weight": 1}],
                "decision": {"policy": "constrained_weighted_score"},
            },
            candidates=[{"id": "winner", "payload": {"score": 1, "secret": "<token>"}}],
            now="2026-06-28T12:00:00+00:00",
        )

        html = render_html_report(
            result.report.to_dict(),
            redact=True,
            fields=["decision.explanation", "state_updates.previous_decision.explanation"],
        )

        self.assertIn("Splot Decision Report", html)
        self.assertIn("dominant=", html)
        self.assertIn("selected", html)
        self.assertIn("[REDACTED]", html)
        self.assertNotIn("selected winner with score", html)


if __name__ == "__main__":
    unittest.main()
