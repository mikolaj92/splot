# Fala Integration

## Architecture note: two layers, one archetype

Fala and Splot are complementary layers over the same information-flow
archetype. Neither absorbs the other. Together they form one cybernetic
mechanism in the tradition of Marian Mazur's cybernetics: Fala is the flow
substrate — it carries, persists, schedules, and replays communicates between
the system and its environment — while Splot is the correlator-and-homeostat
organ that condenses many signals into one decision signal with minimized
entropy. See `docs/CONCEPTUAL_MODEL.md` for the full theoretical mapping.

- **Fala is the information-flow runtime.** It owns Carrier, Observation,
  Artifact, Event, Process, Run, Gate, and Projection, backed by an embedded
  SQLite runtime and a filesystem artifact store. Fala schedules work, persists
  state, appends events, waits on gates, and rebuilds projections. Domain
  meaning lives in Fala *domain packs*, not in the core.
- **Splot is the arbitration layer.** It owns Wave, Evidence, Belief, Candidate,
  scoring, constraints, policies, stability, the `DecisionReport`, and feedback
  traces. Splot is standalone, embeddable, and never imports Fala at module
  load. It adds no queue, scheduler, database, or web server.

Splot's archetypal process is a pure function of information:

```
waves / observations -> evidence -> belief/state -> candidates
-> arbitration -> stabilization -> decision -> feedback / trace
```

A Fala host supplies the left-hand inputs as carriers/observations and persists
the "decide" step's output blob. Splot is that step; Fala is everything around
it. Turning the step output into first-class Events, Gates, or Projections is the
host's or a domain pack's job — a subprocess step cannot open a gate or emit
domain events on its own.

## Archetype mapping

| Fala runtime object     | Splot arbitration meaning                  |
| ----------------------- | ------------------------------------------ |
| Carrier                 | Wave / candidate source                    |
| Observation             | Observation                                |
| Artifact                | `decision_report` / `state` output         |
| Event                   | `splot.decision_committed`                 |
| Gate                    | human decision requirement                 |
| Projection              | decision history / current arbitration state |
| RuntimeRef              | another wave / runtime source              |

Fala owns persistence, scheduling, and replay of these objects. Splot only
produces and consumes their arbitration meaning.

## Import-free adapter

`splot.adapters.fala` maps between the two layers without importing Fala. When
Fala is installed its `fala.sdk` helpers (`output`, `run_manifest_step`) are
used; otherwise identical fallbacks run, so Splot stays standalone.

The integration targets **Fala 0.1.0** as its baseline. Fala SDK support is
optional, not a hard dependency (`dependencies = []`). Public package indexes
reject direct Git URL dependencies in published `Requires-Dist` metadata, so
install Fala explicitly from GitHub when the SDK-backed path is needed:

```bash
pip install splot-runtime
pip install 'fala @ git+https://github.com/mikolaj92/Fala.git@0.1.0'
```

Splot itself ships as the **`splot-runtime`** distribution (the PyPI name `splot`
is an unrelated PySAL package); the import package and console scripts stay
`splot` / `splot-fala-step`. The Fala runtime distribution name is **`fala`**,
resolved from the `https://github.com/mikolaj92/Fala.git` `0.1.0` tag; its
import name is `import fala`.

```python
from splot.adapters.fala import arbitration_step

result = arbitration_step({
    "profile": "examples/profiles/player-camera-director",
    "carriers": [
        {"id": "camera_1", "carrier_type": "splot.wave",
         "payload": {"visibility": 0.9, "available": True}},
    ],
    "observations": [
        {"carrier_id": "camera_1", "kind": "reading", "values": {"lux": 42}},
    ],
    "state": {},
    "output_report": "decision_report.json",
    "output_state": "state.json",
})
```

`arbitration_step` accepts Splot `candidates` or Fala `carriers`, plus Splot- or
Fala-shaped `observations`, and returns host-agnostic descriptors:

- `decision`
- `state`
- `decision_report`
- `observations` — passed-through readings plus a `splot.decision` observation
- `artifacts` — a `splot.decision_report` descriptor
- `events` — `splot.decision_committed`
- `gates` — `splot.human_decision` descriptors when human input is required

## Process runtime step

`splot-fala-step` runs Splot as a Fala process step.

```bash
splot-fala-step < examples/fala-integration/stdin.json
```

- With Fala 0.1.0+ installed from GitHub alongside Splot, it runs as a manifest
  step: Fala writes the manifest to `FALA_STEP_MANIFEST`, Splot writes
  `FALA_STEP_OUTPUT_DIR/result.json`, and Fala commits the result. Steps never
  mutate SQLite directly.
- Standalone, it reads a JSON context from stdin and prints the step output to
  stdout.

It returns a Fala step output (`{values, observations, artifacts, metadata}`) and
writes `splot.decision_report` and `splot.state` artifact files. It also carries a
`splot.decision_committed` event and any `splot.human_decision` descriptor inside
`values` as advisory data. Fala's step-output contract (`fala.sdk.output`) has no
events/gates channel and does not ingest the returned observations or artifacts as
domain rows; it persists the whole output blob as opaque process output. Opening an
actual human gate is a separate `manual_gate` step (see the example package) or a
domain-pack wrapper that returns `waiting=True`.

See `examples/fala-integration/` for a runnable Fala-shaped input and a Fala
carrier-package descriptor. The example is import-free: it does not require Fala
to be installed.

## Boundary

- Splot never schedules, persists, or replays flows; Fala does. Splot only maps
  arbitration inputs and outputs.
- Splot-specific arbitration rules stay in Splot (or in a Fala domain pack that
  wraps it). Fala core never learns about waves, evidence, belief, or policies.
- The `splot-fala-step` output uses Fala SDK helpers when available and does not
  own Fala scheduling, persistence, or operator UI.
