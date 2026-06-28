import unittest
from pathlib import Path

from splot import SplotState, run_round
from splot.profile import load_profile
from splot.schemas import (
    validate_decision_report_data,
    validate_profile_data,
    validate_state_data,
)


ROOT = Path(__file__).resolve().parents[1]


class SchemaValidationTests(unittest.TestCase):
    def test_report_profile_and_state_validate(self):
        profile = load_profile(ROOT / "examples/profiles/player-camera-director")
        result = run_round(
            profile=profile,
            candidates=[{"id": "camera_1", "source_ids": ["camera_1"], "payload": {"visibility": 1}}],
            now="2026-06-28T12:00:00+00:00",
        )
        report = result.report.to_dict()

        validate_profile_data(profile.raw)
        validate_decision_report_data(report)
        validate_state_data(SplotState().to_dict())
        self.assertEqual(report["report_schema_version"], 1)
        self.assertEqual(report["profile_schema_version"], 1)
        self.assertEqual(report["profile_version"], 1)
        self.assertEqual(len(report["profile_digest"]), 64)
        self.assertEqual(len(report["input_digest"]), 64)


if __name__ == "__main__":
    unittest.main()
