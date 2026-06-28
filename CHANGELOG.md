# Changelog

Splot follows simple semantic versioning while the API stabilizes:

- patch: bug fixes and documentation-only changes
- minor: backward-compatible profile, CLI, or report additions
- major: breaking changes to public models, CLI, or report schema

## Unreleased

- Added CI, license metadata, report/state/profile schemas, version and digest
  metadata, static HTML report export, report redaction, report comparison, and
  weight explanation helpers.
- Hardened profile diagnostics, composition audit fields, Fala-shaped example,
  and documentation around providers, reports, YAML subset, security, and
  releases.

## 0.1.0

- Initial standalone Splot runtime.
- Folder-based profiles with safe provider references.
- Weighted scoring, constraints, decision policies, stability, composition,
  evidence, belief, state, reports, CLI, examples, and optional Fala-shaped
  integration.
