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

This file is still import-free. A real Fala host should translate those
descriptors into actual artifacts, events, projections, and gates.
