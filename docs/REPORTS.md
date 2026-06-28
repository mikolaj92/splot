# Reports

Every Splot round emits a JSON `DecisionReport`. It is the audit artifact for
the round, not just a debug dump.

Reports include:

- `splot_version`
- `profile_version`
- `profile_digest`
- `profile_schema_version`
- `report_schema_version`
- `input_digest`
- observations, candidates, evidence, belief, evaluations, stability, decision,
  state updates, warnings, and human decision requirements

Validate and inspect:

```bash
splot report validate decision_report.json
splot audit-report decision_report.json
splot inspect-decision decision_report.json
splot explain decision_report.json
splot explain-weights decision_report.json
splot export-html decision_report.json --out report.html
splot compare-reports old.json new.json
```

`export-html` writes a standalone local HTML file. It uses no server and no
external JavaScript or CSS.
