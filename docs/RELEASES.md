# Releases

Splot uses semantic versioning once public APIs stabilize.

Current status is alpha. Patch releases may tighten validation or report
diagnostics. Minor releases may add profile fields, CLI commands, or report
fields. Major releases are reserved for incompatible model, profile, or report
schema changes.

Release hygiene checklist:

1. Update `CHANGELOG.md`.
2. Keep `pyproject.toml` metadata current.
3. Run `python -m unittest discover -s tests`.
4. Run example CLI commands.
5. Confirm report schemas still validate generated reports.
6. Rebuild `dist/` from clean metadata and inspect wheel/sdist metadata:
   `Requires-Dist` must stay empty, with no direct Git URL dependencies.
