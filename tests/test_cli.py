import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "splot.cli", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_profile_validate_command(self):
        result = self.run_cli("profile", "validate", "examples/profiles/player-camera-director")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("valid profile", result.stdout)

    def test_profile_diagnose_command(self):
        result = self.run_cli("profile", "diagnose", "examples/profiles/player-camera-director")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("valid profile", result.stdout)

    def test_decide_writes_report_and_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            state = Path(tmp) / "state.json"
            result = self.run_cli(
                "decide",
                "--profile",
                "examples/profiles/player-camera-director",
                "--input",
                "examples/inputs/camera_round_1.json",
                "--state",
                str(state),
                "--out",
                str(out),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
            saved_state = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(report["decision"]["status"], "kept_previous")
            self.assertEqual(saved_state["previous_decision"]["status"], "kept_previous")

    def test_inspect_explain_and_replay_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            replayed = Path(tmp) / "replayed.json"
            decide = self.run_cli(
                "decide",
                "--profile",
                "examples/profiles/player-camera-director",
                "--input",
                "examples/inputs/camera_round_1.json",
                "--out",
                str(out),
            )
            self.assertEqual(decide.returncode, 0, decide.stderr)

            inspect = self.run_cli("inspect-decision", str(out))
            explain = self.run_cli("explain", str(out))
            replay = self.run_cli(
                "replay-round",
                "--profile",
                "examples/profiles/player-camera-director",
                "--report",
                str(out),
                "--out",
                str(replayed),
                "--compare",
            )
            audit = self.run_cli("audit-report", str(out))

            self.assertEqual(inspect.returncode, 0, inspect.stderr)
            self.assertEqual(explain.returncode, 0, explain.stderr)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertTrue(replayed.exists())

    def test_state_init_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            result = self.run_cli("state", "init", "--out", str(state))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("session_id", json.loads(state.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
