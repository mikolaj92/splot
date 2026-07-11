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

Remaining uncertainty is accounted for by name, never hidden:

- `uncertainty.value` is the maximum of named `components` (`score_residual`,
  `close_margin_gap`, `evidence_confidence_gap`, `source_reliability_gap`,
  `decision`, ...); `dominant_component` names the biggest one
- `conflicts` (close scores, contested candidates, blocked candidates) are computed live per round in belief and surfaced under `uncertainty.conflicts` (and `belief.conflicts`); they are not stored as history in state. State holds only continuity needed for the next entropy-reduction step: previous decision, stability memory, source reliability.
- `stale_sources` lists sources flagged stale; `silent_sources` lists declared
  waves that sent no observation this round
- `reduction` appears when the same candidate stayed on top across rounds and
  earned an explicit, recorded uncertainty reduction
- per-candidate belief carries `support`, `opposition`, `input_disagreement`,
  and `rounds_seen`, `source_reliability` (per-source trust from feedback),
  and `stale_sources` (source IDs whose observations exceeded `max_age_seconds`)

`build_context_pack` (or `splot context-pack report.json`) condenses a report
into one deterministic, LLM-ready JSON signal: provenance, decision,
uncertainty, and the strongest evidence for the winner. Anything cut by the
byte budget or evidence cap is counted in the `omitted` registry — nothing is
dropped silently — and the default redaction of sensitive keys has no off
switch. Size it with `--max-bytes` (LLM context costs roughly 4 bytes per
token). The pack is the `postprocess.context_pack` postprocessor, not a
decision renderer: renderers run before the report exists, while the pack
summarizes the finished report.

```bash
splot context-pack decision_report.json --max-bytes 8000 --top-evidence 5
```

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
