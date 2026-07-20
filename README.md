# Splot

Splot is a **standalone information arbitration runtime** (Mojo exclusive).

It takes many partial observations / candidates, scores them with declared
signals, applies constraints and stability, and emits an explainable decision
report.

```
waves / observations -> evidence/signals -> candidates
-> score + constrain -> stabilize -> decision -> report / state
```

It is **not** Fala. Fala owns flow/journal/process host; Splot owns the
arbitration step. Integration is optional JSON / subprocess — Splot does not
import Fala.

## Product tree

```text
mojo/splot/          # engine
mojo/smoke/          # proof
examples/profiles/   # TOML profiles (data)
examples/fixtures/   # JSON profiles for native load
schemas/             # shared JSON Schema
docs/MOJO_PORT.md    # migration notes
```

## Proof

```bash
# requires Mojo (pixi) — or Fala's pixi env as fallback via tools/mojo_run.sh
./tools/mojo_run.sh mojo/smoke/core_round.mojo
./tools/mojo_run.sh mojo/smoke/fala_stdio.mojo
```

With pixi in this repo:

```bash
mise exec -- pixi install   # when pixi available
mise exec -- pixi run full-smoke
```

## Programmatic (Mojo)

```mojo
from splot.pipeline import run_round
from splot.models import Candidate, SplotState
from splot.profile import load_profile_toml
from std.pathlib import Path

var profile = parse_json(Path("examples/fixtures/player_camera_director.profile.toml").read_text())
var cands = List[Candidate]()
cands.append(Candidate("a", "{\"visibility\":0.9,\"available\":true}"))
var result = run_round(profile, cands, SplotState())
print(result.decision.status, result.decision.selected_candidate_id)
```

## Fala boundary

```bash
# JSON step (Fala subprocess can invoke the same entry)
# arbitration_step / run_stdio_line in mojo/splot/adapters_fala.mojo
```

See [`docs/FALA_INTEGRATION.md`](docs/FALA_INTEGRATION.md) and
[`docs/MOJO_PORT.md`](docs/MOJO_PORT.md).

## Builtins (land)

Profile providers implemented natively:

- `candidate.value` (field from payload)
- `candidate.available`
- `state.is_current`

No free-form user code registry (Python callables are gone).

## Theoretical note

Splot follows Mazur’s correlator / homeostat framing (entropy-reducing decision
from many communicates). See `docs/CONCEPTUAL_MODEL.md`.
