# Splot

**Splot is a fully Mojo library.** There is no Python runtime, no YAML, no
database, and no report store.

It answers one problem:

> Given several partial, noisy, possibly conflicting **signals** about a set of
> **candidates**, pick **one** decision — with a short reason and optional
> stickiness so the choice does not thrash every tick.

Think of it as a small **arbitration / fusion organ**: many communicates in,
one committed selection out.

```text
candidates + signals (from payloads)
        │
        ▼
   weight & normalize
        │
        ▼
   constraints (block / warn / penalize)
        │
        ▼
   rank & choose one
        │
        ▼
   optional hysteresis (keep previous if the gain is tiny)
        │
        ▼
   decision { status, selected_id, confidence, reason }
```

## What it is for

| Use | Example |
| --- | --- |
| Multi-camera / multi-sensor pick | several sources → one “best live view” |
| Route or option selection | several options → one allowed choice |
| Any host that needs fusion | feed candidates each tick, get one id back |

Typical host: **Fala** (or any process that can run a Mojo program / JSON step).
Splot does **not** import Fala. Fala (or you) owns scheduling, journals, and
persistence. Splot only **computes the decision**.

## What it is not

- Not a workflow engine, queue, or web server  
- Not a report / audit / HTML product  
- Not a state database (optional previous-decision JSON is enough for stability)  
- Not a Python package  

## Fully Mojo

| | |
| --- | --- |
| Language | **Mojo only** (`mojo/splot/`) |
| Profiles | **TOML only** (`profile.toml`) |
| Proof | Mojo smokes (`mojo/smoke/`) |
| Python | **none** in the product tree |

```text
mojo/splot/     engine
mojo/smoke/     gates
examples/       TOML profiles & fixtures
docs/           short design notes
vendor/         EmberJson
tools/          mojo_run.sh
```

## Quick proof

Requires a Mojo toolchain (Pixi or a sibling Fala Pixi env via `tools/mojo_run.sh`):

```bash
./tools/mojo_run.sh mojo/smoke/core_round.mojo
./tools/mojo_run.sh mojo/smoke/fala_stdio.mojo
```

Both should print `… smoke ok`.

## Contract

### Input

1. **Profile** — TOML file (weights, constraints, decision & stability policy).  
2. **Candidates** — each has `id` + JSON `payload` (signal fields live here).  
3. **State** (optional) — previous decision, for hysteresis / stickiness.  
4. **now** (optional) — timestamp string for the host clock.

### Output

```json
{
  "decision": {
    "id": "decision_mojo",
    "status": "selected",
    "objective_id": "best_player_view",
    "selected_candidate_id": "cam_a",
    "confidence": 0.87,
    "uncertainty": 0.13,
    "policy_reason": "constrained_weighted_score_selected_highest_score",
    "explanation": "selected cam_a with score 0.870"
  },
  "state": {
    "previous_decision": { "…": "…" }
  }
}
```

Statuses you will see in normal use: `selected`, `fallback`,
`needs_human_decision`, and similar uncertainty outcomes from the profile.

## Profile (TOML only)

```toml
version = 1
id = "player_camera_director"
mode = "select_one"

[objective]
id = "best_player_view"

[[signals]]
id = "visibility"
provider = "candidate.value"
field = "visibility"
weight = 0.35
prefer = "higher"
min = 0.60

[[constraints]]
id = "source_must_be_live"
provider = "candidate.available"
severity = "block"

[decision]
policy = "constrained_weighted_score"
tie_breaker = "keep_current"
close_margin = 0.05

[stability]
policy = "hysteresis"
min_improvement = 0.15
```

See [`docs/PROFILE_FORMAT.md`](docs/PROFILE_FORMAT.md) and
`examples/profiles/` / `examples/fixtures/`.

### Built-in providers

| Name | Role |
| --- | --- |
| `candidate.value` | Read a numeric field from the candidate payload |
| `candidate.available` | Live / dead gate (block if false) |
| `state.is_current` | Bonus if this candidate was selected last time |

No free-form user code. Extend builtins in `mojo/splot/builtins.mojo` if needed.

## Use from Mojo

```mojo
from std.collections import List
from splot.profile import load_profile_toml
from splot.models import Candidate, SplotState
from splot.pipeline import run_round

var profile = load_profile_toml("examples/fixtures/player_camera_director.profile.toml")
var candidates = List[Candidate]()
candidates.append(Candidate("a", "{\"visibility\":0.9,\"available\":true}"))
candidates.append(Candidate("b", "{\"visibility\":0.5,\"available\":true}"))
var result = run_round(profile, candidates, SplotState())
# result.decision.status, result.decision.selected_candidate_id
```

## Use with Fala (optional)

Splot stays import-free toward Fala. A Fala effector can pass JSON and get a
decision back (`mojo/splot/adapters_fala.mojo` — `arbitration_step` /
`run_stdio_line`). Mapping notes: [`docs/FALA_INTEGRATION.md`](docs/FALA_INTEGRATION.md).

Fala owns journals and process host. Splot only fuses signals into one choice.

## Theory (optional reading)

The name *splot* is Polish for an interweaving: many communicates in, one
decision out. That matches Mazur’s correlator / homeostat picture of reducing
uncertainty. Background: [`docs/CONCEPTUAL_MODEL.md`](docs/CONCEPTUAL_MODEL.md).

## License

MIT — see [`LICENSE`](LICENSE).
