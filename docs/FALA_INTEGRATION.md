# Fala Integration

Splot is standalone. The optional adapter in `splot.adapters.fala` accepts
a manifest-shaped dictionary:

```python
from splot.adapters.fala import arbitration_step

result = arbitration_step({
    "profile": "examples/profiles/player-camera-director",
    "observations": [],
    "candidates": [],
    "state": {},
    "output_report": "decision_report.json",
    "output_state": "state.json",
})
```

Suggested mapping for a real Fala host:

- Carrier -> Wave or candidate source
- Observation -> Observation
- Artifact -> evidence snapshot or decision report
- Event -> arbitration round and committed decision
- Projection -> arbitration state or history
- Gate -> human decision required
- RuntimeRef -> another wave or runtime source

The adapter returns:

- `decision`
- `state`
- `decision_report`
- `artifacts`: currently a decision report artifact descriptor
- `events`: currently `splot.round_completed`
- `gates`: human-decision descriptors when required

## Process Runtime Step

Splot also exposes a Fala process-runtime stdio entrypoint:

```bash
splot-fala-step
```

Use it from a Fala subprocess step. Put `profile` in process `config` or input
values. Put `observations`, `candidates`, `state`, `feedback`, and `now` in
input values or `initial` values. The step returns a Fala-compatible
`ProcessOutput` dictionary and writes:

- `splot_decision_report` artifact
- `splot_state` artifact
- `splot.decision_committed` event
- `splot.human_decision_required` event when human input is needed

The manifest-shaped adapter remains useful for non-Fala hosts that want the
same descriptors without running a Fala process step.
