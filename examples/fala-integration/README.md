# Fala-shaped Splot integration

Fala owns the information-flow runtime (Carrier, Observation, Artifact,
Event, Process, Run, Gate, Projection, SQLite, filesystem artifacts). Splot only
arbitrates. This example hosts Splot as a Fala step **without** making Fala a
runtime dependency of Splot: no server, Redis, Postgres, Kafka, or scheduler.

## Files

- `stdin.json` — a Fala-shaped step input: `config.profile` plus `input.needs`
  with **carriers** and **observations**.
- `fala-package.yaml` — a Fala carrier package that runs `splot-fala-step`
  as a `subprocess` capability and adds a `manual_gate` step for human review.

The integration is built against **Fala 0.1.0** as its baseline. Fala is an
optional extra (`pip install 'splot-runtime[fala]'`), never a hard dependency — the step
below runs identically whether or not Fala is installed.

## Run standalone (no Fala installed)

```bash
splot-fala-step < examples/fala-integration/stdin.json
```

Splot maps the input and returns a Fala step output
(`{values, observations, artifacts, metadata}`):

- **Carrier → candidate source**: each carrier becomes a Splot candidate.
- **Observation → observation**: each Fala observation (`carrier_id`, `kind`,
  `values`) becomes a Splot observation.
- **Artifact ← `decision_report` / `state`**: written to a durable artifact root
  (`PROCESS_RUNTIME_ARTIFACT_DIR`, else `.flow-runs/...`) and referenced with a
  `sha256` in `artifacts`. The ephemeral `FALA_STEP_OUTPUT_DIR` is not used, so the
  `file://` URIs stay valid after the step returns.
- **Event**: `values.events` carries a `splot.decision_committed` descriptor.
- **Gate**: `values.gates` carries a `splot.human_decision` descriptor and
  `values.human_decision_required` when the decision needs a human. These are
  advisory Splot signals; Fala has no conditional gates, so the package's separate
  `manual_gate` step always opens a review gate for an operator to resolve.

## Under a real Fala host

With Fala 0.1.0+ installed (`pip install 'splot-runtime[fala]'`), Fala writes the step
manifest to `FALA_STEP_MANIFEST`, runs `splot-fala-step`,
reads `FALA_STEP_OUTPUT_DIR/result.json`, and persists the whole step-output blob
as the process output. It does not, from a subprocess step, commit the returned
observations, artifacts, or events as first-class domain rows — a domain pack or a
dedicated step (e.g. `manual_gate`) does that. Steps never touch SQLite directly.
