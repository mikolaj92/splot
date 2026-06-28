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

This file is a scaffold, not a real Fala event/gate implementation.
