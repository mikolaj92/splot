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

## Fala-shaped stdio

```bash
splot-fala-step < examples/fala-integration/stdin.json
```

Demonstrates how a Fala subprocess host could call Splot and receive a
decision report artifact descriptor without Splot importing Fala.
