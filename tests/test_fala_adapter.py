import unittest
from pathlib import Path

from splot.adapters.fala import arbitration_step


ROOT = Path(__file__).resolve().parents[1]


class FalaAdapterTests(unittest.TestCase):
    def test_adapter_returns_artifacts_events_and_gates(self):
        result = arbitration_step(
            {
                "profile": str(ROOT / "examples/profiles/contract-composer"),
                "candidates": [
                    {
                        "id": "intro_a",
                        "payload": {
                            "section": "intro",
                            "goal_fit": 1,
                            "completeness": 1,
                            "legal_risk": 0,
                            "style_consistency": 1,
                            "no_contradictions": True,
                            "required_definitions_present": False,
                            "jurisdiction_compatible": True,
                        },
                    }
                ],
                "now": "2026-06-28T12:00:00+00:00",
            }
        )

        self.assertEqual(result["events"][0]["type"], "splot.round_completed")
        self.assertTrue(result["artifacts"])
        self.assertTrue(result["gates"])


if __name__ == "__main__":
    unittest.main()

