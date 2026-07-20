# Fala integration (optional)

Splot does **not** depend on Fala. Fala can call Splot as a **subprocess / JSON step**.

## Mapping

| Fala | Splot |
| --- | --- |
| Process / effector | one `arbitration_step` / stdio line |
| Candidate payloads | `candidates[]` or `carriers[]` |
| Decision | `decision.status` + `selected_candidate_id` |
| Homeostat (optional) | `needs_human_decision` + `gates` |

## Input (JSON)

```json
{
  "profile": "examples/fixtures/player_camera_director.profile.toml",
  "candidates": [
    {"id": "a", "payload": {"visibility": 0.9, "available": true}},
    {"id": "b", "payload": {"visibility": 0.5, "available": true}}
  ],
  "now": "2026-01-01T12:00:00Z"
}
```

## Output (JSON)

```json
{
  "decision": { "status": "selected", "selected_candidate_id": "a", "confidence": 0.8 },
  "state": { "previous_decision": { … } },
  "events": [{ "type": "splot.decision_committed", … }],
  "gates": []
}
```

No report files, no state store — Fala persists if it wants.
