# Security

Splot profiles are configuration, not code. They reference provider names that
must already be registered in Python. Profiles cannot import modules, run shell
commands, or define loops/side effects.

Reports may contain payloads or metadata from domain providers. For local debug
exports, use redaction:

```bash
splot redact-report decision_report.json --out redacted.json
splot redact-report decision_report.json --out redacted.json --field decision.explanation
splot export-html decision_report.json --out report.html --redact --field metadata.api_key
```

Default redaction masks keys named `api_key`, `authorization`, `password`,
`secret`, or `token` anywhere in the report. Explicit fields use dot paths and
`*` for list items, for example `candidates.*.payload.secret`.

This is leak prevention for reports, not a secrets manager.
