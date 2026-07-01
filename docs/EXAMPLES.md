# Examples

## Camera

```bash
PYTHONPATH=src python -m splot.cli examples run camera --out decision_report.json
PYTHONPATH=src python -m splot.cli audit-report decision_report.json
PYTHONPATH=src python -m splot.cli report validate decision_report.json
PYTHONPATH=src python -m splot.cli explain-weights decision_report.json
PYTHONPATH=src python -m splot.cli export-html decision_report.json --out report.html --redact
PYTHONPATH=src python -m splot.cli replay-round --profile examples/profiles/player-camera-director --report decision_report.json --compare
```

Demonstrates weighted scoring, blocking constraints, current-candidate bonus,
hysteresis, cooldown, feedback handler wiring, stale-source behavior, and
keeping the current candidate when close.

## Contract Compose

```bash
PYTHONPATH=src python -m splot.cli examples run contract-compose
```

Demonstrates section-by-section composition with compatibility rules and a
human-decision point. The core reads generic section slots and flags; it
performs no legal analysis.

## Route

```bash
PYTHONPATH=src python -m splot.cli examples run route
```

Demonstrates route selection from candidates.

## Uncertainty

```bash
PYTHONPATH=src python -m splot.cli examples run uncertainty
```

Demonstrates close-score ambiguity producing `request_more_evidence`.

## Fala-shaped step

```bash
splot-fala-step < examples/fala-integration/stdin.json
```

Maps a Fala-shaped input (carriers and observations) into a Splot round and
returns a Fala step output: a `splot.decision_report` artifact, a
`splot.decision_committed` event descriptor, and a `splot.human_decision` gate
descriptor when the decision needs a human — without Splot importing Fala. See
`docs/FALA_INTEGRATION.md`.
