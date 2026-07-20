# Splot

**Exclusive Mojo** library: many signals / candidates → **one** decision.

```
candidates + TOML profile → score + constrain → (optional) stabilize → decision
```

Not a report platform. Not a database. Not Fala.  
Fala is optional **host** (subprocess / JSON); Splot does not import Fala.

## Product tree

```text
mojo/splot/       # only engine
mojo/smoke/       # proof
examples/         # TOML profiles + fixtures
docs/             # conceptual notes
vendor/EmberJson  # JSON
```

## Proof

```bash
./tools/mojo_run.sh mojo/smoke/core_round.mojo
./tools/mojo_run.sh mojo/smoke/fala_stdio.mojo
```

## Contract

**In:** `profile.toml` + candidates (`id` + payload JSON) + optional previous state  
**Out:**

```json
{
  "decision": {
    "status": "selected",
    "selected_candidate_id": "…",
    "confidence": 0.87,
    "reason": "…"
  },
  "state": { "previous_decision": { … } }
}
```

## Builtins

- `candidate.value` — field from payload  
- `candidate.available` — live flag  
- `state.is_current` — stickiness bonus  

Profiles: **TOML only** (`profile.toml`). No YAML. No Python.
