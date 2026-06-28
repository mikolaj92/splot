import unittest
import json
import os
import tempfile
from pathlib import Path

from splot.adapters.fala import arbitration_step, process_runtime_step


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

    def test_process_runtime_step_returns_fala_process_output(self):
        old_artifact_dir = os.environ.get("PROCESS_RUNTIME_ARTIFACT_DIR")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PROCESS_RUNTIME_ARTIFACT_DIR"] = tmp
            result = process_runtime_step(
                {
                    "pipeline_id": "pipeline",
                    "run_id": "run",
                    "document_id": "doc",
                    "process_id": "splot_step",
                    "attempt": 1,
                    "config": {"profile": str(ROOT / "examples/profiles/player-camera-director")},
                    "input": {
                        "values": {
                            "initial": {
                                "now": "2026-06-28T12:00:00+00:00",
                                "candidates": [
                                    {
                                        "id": "camera_1",
                                        "payload": {
                                            "visibility": 0.8,
                                            "face_angle": 0.8,
                                            "sharpness": 0.8,
                                            "occlusion": 0.1,
                                            "available": True,
                                        },
                                    }
                                ],
                            }
                        },
                        "artifacts": [],
                    },
                }
            )
        if old_artifact_dir is None:
            os.environ.pop("PROCESS_RUNTIME_ARTIFACT_DIR", None)
        else:
            os.environ["PROCESS_RUNTIME_ARTIFACT_DIR"] = old_artifact_dir

        self.assertIn("values", result)
        self.assertIn("artifacts", result)
        self.assertEqual(result["values"]["decision"]["status"], "selected")
        self.assertEqual(result["artifacts"][0]["kind"], "splot_decision_report")

    def test_fala_integration_example_payload_runs(self):
        old_artifact_dir = os.environ.get("PROCESS_RUNTIME_ARTIFACT_DIR")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PROCESS_RUNTIME_ARTIFACT_DIR"] = tmp
            payload = json.loads((ROOT / "examples/fala-integration/stdin.json").read_text(encoding="utf-8"))
            result = process_runtime_step(payload)
        if old_artifact_dir is None:
            os.environ.pop("PROCESS_RUNTIME_ARTIFACT_DIR", None)
        else:
            os.environ["PROCESS_RUNTIME_ARTIFACT_DIR"] = old_artifact_dir

        self.assertEqual(result["values"]["decision"]["status"], "selected")
        self.assertEqual(result["artifacts"][0]["kind"], "splot_decision_report")


if __name__ == "__main__":
    unittest.main()
