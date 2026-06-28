import tempfile
import unittest
from pathlib import Path

from splot import ProfileError, builtin_registry, diagnose_profile, load_profile, validate_profile


ROOT = Path(__file__).resolve().parents[1]


class ProfileLoadingTests(unittest.TestCase):
    def test_valid_profile_loads_sidecars(self):
        profile = load_profile(ROOT / "examples/profiles/player-camera-director")

        self.assertEqual(profile.id, "player_camera_director")
        self.assertIn("objective.md", profile.sidecars)
        validate_profile(profile, registry=builtin_registry())

    def test_invalid_signal_reference_fails(self):
        with self.assertRaisesRegex(ProfileError, "unknown signal"):
            load_profile(
                {
                    "version": 1,
                    "id": "bad",
                    "mode": "select_one",
                    "objective": {"id": "objective"},
                    "signals": [{"id": "known", "provider": "candidate.value", "weight": 1}],
                    "constraints": [{"id": "bad_ref", "signal": "missing"}],
                }
            )

    def test_invalid_stability_config_fails(self):
        with self.assertRaisesRegex(ProfileError, "non-negative"):
            load_profile(
                {
                    "version": 1,
                    "id": "bad",
                    "mode": "select_one",
                    "objective": {"id": "objective"},
                    "signals": [{"id": "score", "weight": 1}],
                    "stability": {"policy": "hysteresis", "min_improvement": -0.1},
                }
            )

    def test_invalid_weights_fail(self):
        with self.assertRaisesRegex(ProfileError, "non-negative"):
            load_profile(
                {
                    "version": 1,
                    "id": "bad",
                    "mode": "select_one",
                    "objective": {"id": "objective"},
                    "signals": [{"id": "score", "weight": -1}],
                }
            )

    def test_missing_required_field_fails(self):
        with self.assertRaisesRegex(ProfileError, "missing required field"):
            load_profile({"version": 1, "id": "bad", "objective": {"id": "objective"}})

    def test_yaml_folder_profile_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "profile.yaml").write_text(
                """
version: 1
id: tiny
mode: select_one
objective:
  id: objective
signals:
  - id: score
    provider: candidate.value
    field: score
    weight: 1
""",
                encoding="utf-8",
            )
            (path / "objective.md").write_text("# Tiny\n", encoding="utf-8")

            profile = load_profile(path)

            self.assertEqual(profile.raw["signals"][0]["id"], "score")
            self.assertIn("objective.md", profile.sidecars)

    def test_diagnose_profile_reports_file_and_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "profile.yaml").write_text(
                """
version: 1
id: bad
mode: select_one
objective:
  id: objective
signals:
  - id: score
    provider: missing.provider
    weight: 1
""",
                encoding="utf-8",
            )

            diagnostics = diagnose_profile(path, registry=builtin_registry())

            self.assertEqual(len(diagnostics), 1)
            self.assertIn("missing.provider", diagnostics[0].message)
            self.assertEqual(diagnostics[0].line, 9)


if __name__ == "__main__":
    unittest.main()
