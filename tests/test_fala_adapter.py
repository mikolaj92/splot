import unittest
import json
import os
import tempfile
from pathlib import Path

from splot.adapters.fala import (
    arbitration_step,
    carrier_to_candidate,
    fala_observation_to_splot,
    process_runtime_step,
)


ROOT = Path(__file__).resolve().parents[1]


class FalaMappingTests(unittest.TestCase):
    def test_carrier_maps_to_candidate_source(self):
        candidate = carrier_to_candidate(
            {
                "id": "camera_1",
                "carrier_type": "splot.wave",
                "payload": {"visibility": 0.9},
                "metadata": {"origin": "sensor"},
            }
        )
        self.assertEqual(candidate["id"], "camera_1")
        self.assertEqual(candidate["source_ids"], ["camera_1"])
        self.assertEqual(candidate["kind"], "splot.wave")
        self.assertEqual(candidate["payload"], {"visibility": 0.9})

    def test_fala_observation_maps_carrier_id_to_wave_id(self):
        observation = fala_observation_to_splot(
            {"carrier_id": "camera_1", "kind": "reading", "values": {"lux": 5}}, index=0
        )
        self.assertEqual(observation["wave_id"], "camera_1")
        self.assertEqual(observation["id"], "observation_0")
        self.assertNotIn("carrier_id", observation)


class FalaAdapterTests(unittest.TestCase):
    def test_adapter_returns_observations_events_artifacts_and_gates(self):
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

        self.assertEqual(result["events"][0]["type"], "splot.decision_committed")
        self.assertEqual(result["artifacts"][0]["kind"], "splot.decision_report")
        self.assertTrue(result["observations"])
        self.assertEqual(result["observations"][-1]["kind"], "splot.decision")
        self.assertTrue(result["gates"])
        self.assertEqual(result["gates"][0]["kind"], "splot.human_decision")

    def test_adapter_accepts_fala_carriers_and_observations(self):
        result = arbitration_step(
            {
                "profile": str(ROOT / "examples/profiles/player-camera-director"),
                "carriers": [
                    {
                        "id": "camera_1",
                        "carrier_type": "splot.wave",
                        "payload": {
                            "visibility": 0.9,
                            "face_angle": 0.7,
                            "sharpness": 0.8,
                            "occlusion": 0.1,
                            "available": True,
                        },
                    }
                ],
                "observations": [
                    {"carrier_id": "camera_1", "kind": "reading", "values": {"lux": 42}}
                ],
                "now": "2026-06-28T12:00:00+00:00",
            }
        )

        self.assertEqual(result["decision"]["status"], "selected")
        self.assertEqual(result["decision"]["selected_candidate_id"], "camera_1")
        self.assertEqual(result["events"][0]["type"], "splot.decision_committed")
        self.assertEqual(result["observations"][0]["carrier_id"], "camera_1")
        self.assertEqual(result["gates"], [])

    def test_process_runtime_step_returns_fala_step_output(self):
        old_artifact_dir = os.environ.get("PROCESS_RUNTIME_ARTIFACT_DIR")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PROCESS_RUNTIME_ARTIFACT_DIR"] = tmp
            result = process_runtime_step(
                {
                    "run_id": "run",
                    "process_id": "splot_step",
                    "config": {"profile": str(ROOT / "examples/profiles/player-camera-director")},
                    "input": {
                        "needs": {
                            "now": "2026-06-28T12:00:00+00:00",
                            "carriers": [
                                {
                                    "id": "camera_1",
                                    "carrier_type": "splot.wave",
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
                }
            )
        if old_artifact_dir is None:
            os.environ.pop("PROCESS_RUNTIME_ARTIFACT_DIR", None)
        else:
            os.environ["PROCESS_RUNTIME_ARTIFACT_DIR"] = old_artifact_dir

        self.assertEqual(set(result), {"values", "observations", "artifacts", "metadata"})
        self.assertEqual(result["values"]["decision"]["status"], "selected")
        self.assertEqual(result["values"]["events"][0]["type"], "splot.decision_committed")
        self.assertEqual(result["artifacts"][0]["kind"], "splot.decision_report")
        self.assertEqual(result["artifacts"][1]["kind"], "splot.state")
        self.assertTrue(result["artifacts"][0]["uri"].startswith("file://"))

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
        self.assertEqual(result["artifacts"][0]["kind"], "splot.decision_report")


if __name__ == "__main__":
    unittest.main()
