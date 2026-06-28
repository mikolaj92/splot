import tempfile
import unittest
from pathlib import Path

from splot import ProfileError, builtin_registry, diagnose_profile, load_profile


class ProfileDiagnosticsTests(unittest.TestCase):
    def test_duplicate_constraint_id_fails_validation(self):
        with self.assertRaisesRegex(ProfileError, "duplicate constraint id"):
            load_profile(
                {
                    "version": 1,
                    "id": "bad",
                    "mode": "select_one",
                    "objective": {"id": "objective"},
                    "signals": [{"id": "score", "weight": 1}],
                    "constraints": [{"id": "same"}, {"id": "same"}],
                }
            )

    def test_diagnose_warns_for_declared_sidecars_and_yaml_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "profile.yaml").write_text(
                """
version: 1
id: diag
mode: select_one
objective:
  id: objective
sidecars: [objective.md]
signals:
  - id: score
    provider: candidate.value
    weight: 1
""",
                encoding="utf-8",
            )
            (path / "extra.md").write_text("extra", encoding="utf-8")

            diagnostics = diagnose_profile(path, registry=builtin_registry())

            messages = [item.message for item in diagnostics]
            self.assertIn("declared sidecar is missing: objective.md", messages)
            self.assertIn("Markdown sidecar is not declared: extra.md", messages)
            self.assertFalse(any(item.severity == "error" for item in diagnostics))


if __name__ == "__main__":
    unittest.main()
