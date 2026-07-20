# Changelog

Splot follows semantic versioning:

- **patch** — bug fixes and documentation-only changes  
- **minor** — backward-compatible engine or profile surface additions  
- **major** — breaking changes to the public decision / profile contract  

## 0.3.0

**Exclusive Mojo product.** First release of Splot as a fully Mojo arbitration
library (no Python runtime, no YAML).

### Product

- Mojo engine under `mojo/splot/`: signals → weighted score → constraints →
  single decision → optional hysteresis.
- Profiles are **TOML only** (`profile.toml` / fixtures).
- Builtins: `candidate.value`, `candidate.available`, `state.is_current`.
- Optional Fala JSON / stdio boundary (`adapters_fala.mojo`) without report or
  storage products.
- Proof: `core_round` and `fala_stdio` smokes.

### Removed from product

- Python package (`src/`, tests, CLI, registry of free-form callables).
- YAML profiles and YAML subset.
- Decision-report suite, schemas, HTML, audit/compare tooling as product surface.
- State file stores as product surface (optional previous-decision JSON only).

### Contract (stable for hosts)

**In:** TOML profile + candidates (+ optional previous state).  
**Out:** `decision` (`status`, `selected_candidate_id`, `confidence`, …) +
`state` for stickiness.

### Notes

- Not full feature parity with historical Python 0.2.x (compose/route modes,
  rich evidence/belief, operator CLI). Scope is the generic fusion organ.
- Integration with Fala is optional; Splot does not import Fala.

## 0.2.0

Historical Python-era release (see git history before the Mojo exclusive cut).
Summary of 0.2.x work included entropy/fusion refinements, context pack, Fala
adapter alignment, CI/schemas, and cybernetic documentation. Superseded for
runtime purposes by **0.3.0 Mojo**.
