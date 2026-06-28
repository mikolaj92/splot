import unittest
from pathlib import Path

from splot import run_round


ROOT = Path(__file__).resolve().parents[1]


class CompositionTests(unittest.TestCase):
    def test_section_by_section_composition_and_human_decision(self):
        result = run_round(
            profile=ROOT / "examples/profiles/contract-composer",
            candidates=[
                {
                    "id": "intro_a",
                    "payload": {
                        "section": "intro",
                        "goal_fit": 1,
                        "completeness": 1,
                        "legal_risk": 0,
                        "style_consistency": 1,
                        "no_contradictions": True,
                        "required_definitions_present": True,
                        "jurisdiction_compatible": True,
                    },
                },
                {
                    "id": "scope_a",
                    "payload": {
                        "section": "scope",
                        "goal_fit": 1,
                        "completeness": 1,
                        "legal_risk": 0,
                        "style_consistency": 1,
                        "no_contradictions": True,
                        "required_definitions_present": True,
                        "jurisdiction_compatible": True,
                    },
                },
                {
                    "id": "comp_a",
                    "payload": {
                        "section": "compensation",
                        "goal_fit": 1,
                        "completeness": 1,
                        "legal_risk": 0,
                        "style_consistency": 1,
                        "no_contradictions": True,
                        "required_definitions_present": False,
                        "jurisdiction_compatible": True,
                    },
                },
            ],
            now="2026-06-28T12:00:00+00:00",
        )

        plan = result.decision.action["plan"]
        self.assertEqual(result.decision.status, "needs_human_decision")
        self.assertEqual(plan["selected_by_section"]["intro"], "intro_a")
        self.assertIn("ip", plan["missing_required"])
        self.assertTrue(result.decision.required_human_inputs)


if __name__ == "__main__":
    unittest.main()
