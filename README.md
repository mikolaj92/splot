# Splot

Splot is a small, standalone information arbitration runtime built as a
cybernetic mechanism: it takes many partial, noisy, possibly conflicting
signals and emits one decision signal with minimized entropy. Observations and
candidate projections are scored with registered functions, filtered through
constraints and stability rules, and committed as an explainable decision
report that records the remaining uncertainty, the conflicts encountered, and
why the winning decision was chosen.

It is not a video director, legal merger, workflow engine, queue, streaming
system, rules-language clone, or LLM agent framework. Domain work lives in
registered Python functions; profiles only reference safe function names.

## Core Archetype

```
waves / observations -> evidence -> belief/state -> candidates
-> arbitration -> stabilization -> decision -> feedback / trace
```

## Theoretical Foundation

Splot's research basis is the Polish school of cybernetics of Marian Mazur —
the qualitative theory of information (*Jakościowa teoria informacji*, 1970)
and the theory of autonomous systems (*Cybernetyczna teoria układów
samodzielnych*, 1966). The name is the Polish word *splot*, an interweaving:
many communicates in, one committed decision out, with the remaining
uncertainty accounted for in the trace.

Each pipeline stage plays a role from Mazur's model of a self-controlling
system:

| Splot stage                          | Cybernetic role                                        |
| ------------------------------------ | ------------------------------------------------------ |
| waves / observations                 | receptors: communicates from distorting carriers       |
| evidence -> belief/state             | correlator: registering and correlating signals        |
| candidates -> arbitration            | correlator: deriving the reaction                      |
| constraints, verifiers, human-decision escalation | control in the system's own interest      |
| stabilization (hysteresis, cooldown) | homeostat: functional equilibrium, no thrashing        |
| decision -> feedback                 | effectors and feedback coupling                        |
| trace (`DecisionReport`)             | the uncertainty accounting, made auditable             |

This framing does not change how the code runs; it explains why the runtime is
constructed the way it is. See `docs/CONCEPTUAL_MODEL.md` for the full mapping.

The current package lives at `src/splot`. Fala owns the information-flow runtime (Carrier, Observation, Artifact, Event, Process, Run, Gate, Projection, SQLite, filesystem artifacts); Splot owns arbitration; Takt supplies n-layer hierarchical regulation (CascadeRegulator) over Fala conduction, optionally using Splot for entropy-reducing fusion. See `docs/FALA_INTEGRATION.md` for the full archetype mapping (Fala + Splot + Takt) with citations to Mazur (*Jakościowa teoria informacji* 1970, *Cybernetyczna teoria układów samodzielnych* 1966) and Kossecki (wielopoziomowe układy samodzielne). Fala integration is optional and is only a thin, import-free adapter in `splot.adapters.fala`.

## Quick Run

```bash
PYTHONPATH=src python -m splot.cli profile validate examples/profiles/player-camera-director
PYTHONPATH=src python -m splot.cli examples run camera --out decision_report.json
PYTHONPATH=src python -m splot.cli explain decision_report.json
PYTHONPATH=src python -m splot.cli explain-weights decision_report.json
PYTHONPATH=src python -m splot.cli audit-report decision_report.json
PYTHONPATH=src python -m splot.cli report validate decision_report.json
PYTHONPATH=src python -m splot.cli export-html decision_report.json --out report.html --redact
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
  observation providers, candidate providers, scorers, decision renderers,
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
- report schema/version/digest metadata for replay and audit
- CLI for validate, decide, inspect, explain, report validate, HTML export,
  report redaction, weight explanation, replay, state init, and examples
- report audit, report comparison, and replay comparison helpers
- import-free Fala adapter (Carrier/Observation/Artifact/Event/Gate mapping)
  plus `splot-fala-step` process-runtime entrypoint

Boundaries:

- `splot-fala-step` returns a Fala step output
  (`{values, observations, artifacts, metadata}`) and uses `fala.sdk` helpers
  when available. It does not own Fala scheduling, persistence, or operator UI.
- Profile YAML uses stdlib fallback parsing; if PyYAML is installed, Splot uses
  `yaml.safe_load`.
- Built-in domain functions are intentionally generic. Real domains should
  register their own providers.
- Static HTML reports are local debug artifacts; Splot does not ship a web
  server, broker, database, or scheduler.
