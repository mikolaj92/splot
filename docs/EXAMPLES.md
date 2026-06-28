# Examples

## Camera

```bash
PYTHONPATH=src python -m splot.cli examples run camera --out decision_report.json
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
