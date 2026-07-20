# Mojo exclusive — status

**Done (2026-07):** product engine is Mojo under `mojo/splot/`. Python `src/`
and `tests/` removed.

## Proof

```bash
./tools/mojo_run.sh mojo/smoke/core_round.mojo
./tools/mojo_run.sh mojo/smoke/fala_stdio.mojo
```

## Scope shipped

| Piece | Status |
| --- | --- |
| Models + `run_round` | done |
| Signals (`candidate.value`, `state.is_current`) | done |
| Constraints (`candidate.available`, signal ops, min) | done |
| Scoring (weighted) | done |
| Decision (constrained weighted + tie/keep_previous) | done |
| Stability hysteresis | done |
| JSON profile fixtures | done |
| Fala JSON adapter | done |
| Full YAML profile loader + all Python providers | not yet (extend builtins) |
| HTML CLI / full report audit suite | not yet |

## Fala

Use latest Mojo Fala as **host** only (`subprocess` → Splot stdio). Do not
merge Splot into Fala core.
