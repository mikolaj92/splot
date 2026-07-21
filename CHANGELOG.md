# Changelog

Splot follows semantic versioning:

- **patch** — bug fixes and documentation-only changes  
- **minor** — backward-compatible engine or profile surface additions  
- **major** — breaking changes to the public decision / profile contract  

## 0.4.0

**Thin optional Python binding** over the exclusive Mojo engine.

### Added

- `python/splot/`: `fuse`, `fuse_json`, `load_profile` — JSON-compatible happy path
- `_native.mojo` + JIT compile helper (`_build.py`) against `mojo/splot`
- Python smoke tests under `python/tests/`

### Unchanged

- Mojo engine and `tools/splot_step.sh` / Fala subprocess contract
- No dual engine: Python does not reimplement fusion

## 0.3.2

**Generic fusion organ.** Host-registered payload readers, `compose_one`, and
richer round evaluations — still evaluator- and domain-agnostic.

### Documentation

- Reframed product language around a **generic fusion organ**: many high-entropy
  streams in → one lower-entropy commitment out.
- Hard boundaries: **domain-agnostic**, **evaluator-agnostic** (LLM, heuristic,
  random, human — host-owned); Splot is not a management/orchestration product
  and does not run evaluators.
- Conceptual model / README: **host-registered readers**, **`compose_one`**, and
  **evaluations envelope detail** documented as shipped.

### Added

- **Host-registered payload readers** (`ReaderRegistry`): register named recipes
  (`product:a,b`, `value:field`, gates, …) used by profile `provider` strings
  without forking builtins. Unknown names fail closed (zero / non-pass).
  Optional JSON `readers` block on `fusion_step` requests.
- **`mode = "compose_one"`**: multi-stream commitment with `decision.composed`
  parts (primary id + weighted parts). Still evaluator/domain-agnostic.
- **Round envelope detail**: `run_round` includes `evaluations` (per-candidate
  scores, signals, constraints). Fala/step JSON stays thin by default; set
  `include_evaluations` / `detail` to attach the same detail.
- Smokes: `mojo/smoke/host_readers.mojo`, `mojo/smoke/compose_envelope.mojo`.
- Fixtures: `examples/fixtures/host_focus.profile.toml`,
  `compose_streams.profile.toml`.

### Changed

- Code/comments use **fusion** language: primary host entry is `fusion_step`;
  `arbitration_step` kept as a compatibility alias for Fala / older callers.
- Builtin helpers documented as **payload readers**, not evaluators.
- `Decision.to_json` includes additive `composed` (JSON `null` when unused).

## 0.3.1

**Fala host step.** Patch release so Fala (or any process host) can run one
fusion step as a subprocess effector.

### Added

- `mojo/splot/step_main.mojo` — CLI entry: request JSON path / Fala effector
  boundary (`FALA_EFFECTOR_*`) / `SPLOT_REQUEST_PATH` → writes
  `output/result.json` or prints the decision envelope.
- `tools/splot_step.sh` — host-friendly wrapper; sets `PATH` /
  `CONDA_PREFIX` / `MODULAR_HOME` from local or sibling Fala Pixi env so Mojo
  finds `std` under a sanitized process-host environment.
- `examples/fixtures/player_camera_director.request.json` — fixture used by the
  Fala integration smoke.

### Contract

Unchanged from 0.3.0 (decision + state). Hosts may pass Mojo toolchain env
explicitly when the parent process sanitizes the environment.

## 0.3.0

**Exclusive Mojo product.** First release of Splot as a fully Mojo fusion
library (no Python runtime, no YAML).

### Product

- Mojo engine under `mojo/splot/`: host-supplied signals → weighted score →
  constraints → single `select_one` commitment → optional hysteresis.
- Profiles are **TOML only** (`profile.toml` / fixtures) — fusion policy only.
- Builtin **payload readers**: `candidate.value`, `candidate.available`,
  `state.is_current` (not evaluators).
- Optional Fala JSON / stdio boundary (`adapters_fala.mojo`) without report or
  storage products.
- Proof: `core_round` and `fala_stdio` smokes.

### Removed from product

- Python package (`src/`, tests, CLI, registry of free-form callables).
- YAML profiles and YAML subset.
- Decision-report suite, schemas, HTML, audit/compare tooling as product surface.
- State file stores as product surface (optional previous-decision JSON only).

### Contract (stable for hosts)

**In:** TOML profile + candidates with precomputed payloads (+ optional previous
state).  
**Out:** `decision` (`status`, `selected_candidate_id`, `confidence`, …) +
`state` for stickiness.

### Notes

- Not full feature parity with historical Python 0.2.x (compose/route modes,
  rich evidence/belief, operator CLI). Scope is the generic fusion organ;
  evaluators and domain stay with the host.
- Integration with Fala is optional; Splot does not import Fala.

## 0.2.0

Historical Python-era release (see git history before the Mojo exclusive cut).
Summary of 0.2.x work included entropy/fusion refinements, context pack, Fala
adapter alignment, CI/schemas, and cybernetic documentation. Superseded for
runtime purposes by **0.3.0 Mojo**.
