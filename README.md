# Splot

**Version 0.4.1** — exclusive Mojo engine + optional thin Python binding (`fuse`).

**Splot is a Mojo library.** There is no YAML, no database, and no report store.
An optional Python package (`python/splot`) is a JSON bridge to the same Mojo
engine — not a second runtime.

## One job

> **Many high-entropy streams of communicates in → one lower-entropy commitment
> out.**

The name *splot* is Polish for an interweaving. Splot is a **domain-agnostic,
evaluator-agnostic fusion organ**: it does not manage sources, run models, or
decode media. It fuses already-produced signals into **one** committed result
the host can act on — with optional stickiness so the output does not thrash
every tick.

```text
  stream / candidate ₁   (signals from any evaluator)
  stream / candidate ₂
  …
  stream / candidate ₙ
              │
              ▼
     weight · normalize · constrain
              │
              ▼
     rank & commit one
              │
              ▼
     optional hysteresis (homeostat)
              │
              ▼
     decision { status, selected_id, confidence, reason }
```

Who produced a signal — **LLM, simple algorithm, sensor, human, or random** —
is irrelevant. Splot only sees the communicate shape (payload fields + profile
rules).

## What it is for

| Use | High-entropy in | Lower-entropy out |
| --- | --- | --- |
| Multi-camera / multi-sensor | 5 camera streams, each scored “player visible?” by *whatever* | one live stream id to switch to |
| Multi-modal tasking | RAG, images, book, docs, prompt, goal as parallel streams | one committed task / choice the host can execute |
| Option / route pick | several options with partial scores | one allowed choice |
| Any host fusion tick | candidates + precomputed signals | one id (and reason) per round |

Typical host: **Fala** (or any process that can run a Mojo program / JSON step).
Splot does **not** import Fala. The host owns scheduling, evaluators, journals,
and persistence. Splot only **fuses and commits**.

## What it is not

- **Not a management or orchestration product** (no source registry UI, no
  workflow engine, no queue, no web server)
- **Not an evaluator** — it does not call LLMs, run CV, or invent scores
- **Not domain-specific** — no video codecs, no RAG stack, no document parsers
- **Not a report / audit / HTML product**
- **Not a state database** (optional previous-decision JSON is enough for
  stability)
- **Not a second engine** — the optional Python package only calls Mojo

## Boundaries (hard)

| Outside Splot (host / effector) | Inside Splot |
| --- | --- |
| Producing signals (LLM, heuristic, random, …) | Reading signal fields from candidate payloads |
| Domain meaning of a field (`visibility`, `relevance`) | Weights, normalize, constraints, rank, hysteresis |
| Streaming media or tokens | One fusion **round** → one commitment |
| Persistence, journals, multi-process schedule | Optional previous decision in `state` |

**Evaluator-agnostic:** any function may fill payload numbers. Swapping random
for an LLM does not require a Splot code path change — only different numbers
in the same fields.

**Domain-agnostic:** cameras and multi-modal AI use the same contract:
candidates + profile → decision.

## Mojo-native engine

| | |
| --- | --- |
| Language | **Mojo** (`mojo/splot/`) — the product engine |
| Profiles | **TOML only** (`profile.toml`) |
| Proof | Mojo smokes (`mojo/smoke/`) |
| Python | optional thin package (`python/splot/`), a JSON bridge — not a second engine |

```text
mojo/splot/     engine (+ step_main for host entry)
python/splot/   optional host binding (fuse / fuse_json)
mojo/smoke/     gates
examples/       TOML profiles & fixtures
docs/           design notes (intent + shipped scope)
tools/          mojo_run.sh, splot_step.sh (Fala effector)
```

## Quick proof

Requires Pixi Mojo **1.0.0** (`pixi.toml` channel `conda.modular.com/max`). EmberJson is cloned + patched at first smoke (`tools/setup_ember_json.sh`), not vendored in git:

```bash
./tools/mojo_run.sh mojo/smoke/core_round.mojo
./tools/mojo_run.sh mojo/smoke/fala_stdio.mojo
# Complete product gate:
mise exec pixi -- pixi run full-smoke
uv run pytest
```

### One step as a subprocess (Fala-compatible)

```bash
# From Splot (or via Fala process host → this script):
export SPLOT_REQUEST_PATH=examples/fixtures/player_camera_director.request.json
./tools/splot_step.sh
# With FALA_EFFECTOR_OUTPUT_DIR set, writes output/result.json
```

Fala integration proof (sibling checkout):

```bash
# From Fala:
mise exec -- pixi run splot-integration
```

Both should print `… smoke ok`.

## Contract (0.4.x shipped)

### Input

1. **Profile** — TOML (weights, constraints, decision & stability policy).
2. **Candidates** — each has `id` + JSON `payload` (signal fields live here;
   **already evaluated** by the host).
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

Statuses in normal use: `selected`, `composed`, `fallback`,
`needs_human_decision`, and similar uncertainty outcomes from the profile.

**Shipped modes**

| Mode | Commitment |
| --- | --- |
| `select_one` (default) | one candidate id |
| `compose_one` | one multi-stream composition (`decision.composed` parts + primary id) |

Any other `mode` or decision `policy` fails closed. Shipped policies are
`constrained_weighted_score` and `weighted_score`.

`run_round` returns a host-facing envelope with `decision`, `state`, and
**`evaluations`** (per-candidate scores/signals/constraints). The Fala/subprocess
step stays **thin** (decision + state + events + gates) unless the request sets
`include_evaluations` / `detail` to true. See
[`docs/CONCEPTUAL_MODEL.md`](docs/CONCEPTUAL_MODEL.md).

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

Signal **values** are host-supplied. Profile `provider` names only describe how
Splot **reads** the payload (not how scores were computed).

See [`docs/PROFILE_FORMAT.md`](docs/PROFILE_FORMAT.md) and
`examples/profiles/` / `examples/fixtures/`.

### Payload readers (not evaluators)

Builtins (always available):

| Name | Role |
| --- | --- |
| `candidate.value` | Read a numeric field from the candidate payload |
| `candidate.available` | Live / dead gate (block if false) |
| `state.is_current` | Bonus if this candidate was selected last time |

**Host-registered readers** map additional `provider` names without forking
core. Recipes only combine already-supplied payload fields (e.g.
`product:player,ball`). No free-form user code, no LLM/CV plugins.

```mojo
from splot.registry import ReaderRegistry
var reg = ReaderRegistry.with_builtins()
reg.register_signal_reader("host.focus", "product:player,ball")
var result = run_round(profile, candidates, SplotState(), registry=reg)
```

On `fusion_step` JSON, optional:

```json
"readers": { "signals": { "host.focus": "product:player,ball" } }
```

**Producing** field values stays with the host evaluator of choice.

## Use from Mojo

```mojo
from std.collections import List
from splot.profile import load_profile_toml
from splot.models import Candidate, SplotState
from splot.pipeline import run_round

var profile = load_profile_toml("examples/fixtures/player_camera_director.profile.toml")
# Host already ran any evaluators; payloads carry the signals.
var candidates = List[Candidate]()
candidates.append(Candidate("a", "{\"visibility\":0.9,\"available\":true}"))
candidates.append(Candidate("b", "{\"visibility\":0.5,\"available\":true}"))
var result = run_round(profile, candidates, SplotState())
# result.decision.status, result.decision.selected_candidate_id
# result.report_json / result.evaluations_json — host audit detail
```

## Thin Python binding (optional)

Mojo remains the product engine. An optional in-process host API ships as a
real Python package (`python/splot`):

```bash
export SPLOT_HOME=/path/to/Splot   # if not developing from the checkout
# Mojo toolchain on PATH (pixi / Modular)
uv pip install -e .
python -c "import splot; print(splot.fuse(profile='examples/fixtures/player_camera_director.profile.toml', candidates=[...]))"
```

```python
import splot

decision, state = splot.fuse(
    profile="examples/fixtures/player_camera_director.profile.toml",
    candidates=[{"id": "cam_a", "payload": {"visibility": 0.9, "available": True}}],
)
# same JSON contract as tools/splot_step.sh
```

`tools/splot_step.sh` stays the official Fala subprocess contract. No dual engine.

## Use with Fala (optional)

Splot stays import-free toward Fala. A Fala effector can pass JSON and get a
decision back (`mojo/splot/adapters_fala.mojo` — `fusion_step` / stdio line;
`arbitration_step` remains as a historical alias). Mapping notes:
[`docs/FALA_INTEGRATION.md`](docs/FALA_INTEGRATION.md).

Fala owns journals, process host, and **evaluators**. Splot only fuses signals
into one commitment.

## Theory

Background and the split between **design intent** and **0.4.x shipped scope**:
[`docs/CONCEPTUAL_MODEL.md`](docs/CONCEPTUAL_MODEL.md).

## License

MIT — see [`LICENSE`](LICENSE).
