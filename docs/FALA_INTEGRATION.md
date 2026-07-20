# Fala integration (optional)

Splot does **not** depend on Fala. Fala can call Splot as a **subprocess / JSON
fusion step**.

Fala (or any host) owns:

- scheduling and process lifecycle  
- **evaluators** (LLM, heuristics, sensors, random, …) that fill candidate payloads  
- journals / persistence if desired  

Splot only fuses those payloads under a TOML profile into **one commitment**.

## Mapping

| Fala | Splot |
| --- | --- |
| Process / effector | one fusion step / stdio line (`fusion_step`; `arbitration_step` is a historical alias) |
| Candidate payloads | `candidates[]` or `carriers[]` — signals **already evaluated** |
| Decision | `decision.status` + `selected_candidate_id` |
| Homeostat (optional) | `needs_human_decision` + `gates` |
| Evaluators / media / RAG | **not in Splot** |

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

`visibility` (and any other signal) is host-supplied. Splot does not care how it
was produced.

## Output (JSON)

```json
{
  "decision": { "status": "selected", "selected_candidate_id": "a", "confidence": 0.8 },
  "state": { "previous_decision": { "…": "…" } },
  "events": [{ "type": "splot.decision_committed", "…" : "…" }],
  "gates": []
}
```

Optional:

```json
{
  "include_evaluations": true,
  "readers": {
    "signals": { "host.focus": "product:player,ball" },
    "gates": { "host.ready": "bool:ready" }
  }
}
```

- Default step JSON is **thin**: `decision` + `state` + `events` + `gates`
  (backward compatible).  
- `include_evaluations` / `detail` attaches per-candidate fusion detail.  
- `readers` registers host payload recipes for this step only.  

No report files, no state store, no evaluator config — Fala persists and
evaluates if it wants.
