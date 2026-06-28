# Splot

Splot is a small, standalone information arbitration runtime. It takes many
partial observations or candidate projections, scores them with registered
functions, applies constraints and stability rules, and emits an explainable
decision report.

It is not a video director, legal merger, workflow engine, queue, streaming
system, rules-language clone, or LLM agent framework. Domain work lives in
registered Python functions; profiles only reference safe function names.

## Core Archetype

```
waves / observations -> evidence -> belief/state -> candidates
-> arbitration -> stabilization -> decision -> feedback / trace
```

The current package lives at `src/splot`. Fala integration is optional and is
only a thin adapter in `splot.adapters.fala`.

## Quick Run

```bash
PYTHONPATH=src python -m splot.cli profile validate examples/profiles/player-camera-director
PYTHONPATH=src python -m splot.cli examples run camera --out decision_report.json
PYTHONPATH=src python -m splot.cli explain decision_report.json
PYTHONPATH=src python -m splot.cli replay-round --profile examples/profiles/player-camera-director --report decision_report.json
PYTHONPATH=src python -m splot.cli examples run contract-compose
PYTHONPATH=src python -m unittest discover -s tests
```

## Programmatic Usage

```python
from splot import builtin_registry, run_round

result = run_round(
    profile="examples/profiles/player-camera-director",
    observations=[],
    candidates=[
        {"id": "a", "payload": {"visibility": 0.9, "available": True}},
        {"id": "b", "payload": {"visibility": 0.7, "available": True}},
    ],
    registry=builtin_registry(),
)

print(result.decision.status)
print(result.report.to_dict())
```

## Profile Shape

Profiles are folders:

```text
profiles/example/
  profile.yaml
  objective.md
  signals.md
  constraints.md
```

`profile.yaml` configures objectives, signals, constraints, decision policy,
stability policy, uncertainty behavior, and safe provider references such as
`candidate.value` or `state.is_current`.

## Current Scope

Implemented:

- dataclass models for waves, observations, evidence, candidates, decisions,
  belief snapshots, reports, feedback, and state
- folder profile loading with Markdown sidecars
- safe function registry with categories for signals, constraints, evidence,
  postprocessors, and feedback handlers
- evidence generation from signal evaluations or registered evidence builders
- belief snapshots with candidate support/opposition, uncertainty, conflicts,
  stale sources, reliability, and history
- weighted scoring with higher/lower/boolean/target normalization
- block/warn/human-decision/penalize constraints
- select, route, regulate-style action status, and section composition
- composition dependencies, compatibility rules, global constraints, conflict
  reporting, and composed payload plans
- hysteresis, cooldown, min-hold, debounce, hold-then-recheck, and switching cost
- stale-source behavior: ignore, penalize, block, or request more evidence
- JSON state/report output plus memory and JSON file state stores
- CLI for validate, decide, inspect, explain, replay, state init, and examples
- import-free Fala-shaped adapter returning artifacts, events, and gates

Scaffolded:

- Fala adapter returns Fala-shaped artifacts/events/gates, but does not call a
  real Fala runtime API.
- Profile YAML uses stdlib fallback parsing; if PyYAML is installed, Splot uses
  `yaml.safe_load`.
- Built-in domain functions are intentionally generic. Real domains should
  register their own providers.
