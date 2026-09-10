# Approach plan

<!-- lokay-approach source=deterministic repo=mikolaj92/splot issue=38 -->

Repository: `mikolaj92/splot`  
Issue: #38 — when_close=keep_previous przywraca ghost id; hysteresis z #37 tego nie widzi

## Goal

`decide_select_one` przy `uncertainty.when_close = "keep_previous"` zwraca poprzedniego kandydata **bez sprawdzenia, czy nadal jest na liście i eligible**. `apply_stability` z #37 (`5db2bd9`) tego nie łapie: gdy `proposed == previous_id`, hysteresis wychodzi na linii 500 i nigdy nie patrzy na `previous_eligible`.

## Files likely touched

- `examples/profiles/player-camera-director/profile.toml`
- `e.eligible`
- `0.0`
- `tools/test_product.sh`
- `stability_eligibility.mojo`

## Test plan

- `when_close = "keep_previous"` zostawia previous tylko gdy jest **obecny i eligible** w tej rundzie
- Absent albo blocked previous → commit replacement (albo `fallback` / `no_candidate`), nie ghost id
- Native smoke: close scores + previous unavailable **oraz** previous absent; oba wybierają replacement
- Smoke wchodzi do `pixi run full-smoke` / `./tools/test_product.sh` (dziś `stability_eligibility.mojo` nie jest w gate)

## Non-goals

- Nowe mode. Zmiana `min_improvement`. Komentarz na zamkniętym #37.

## Notes

- Trust intentional issue; this plan is evidence for later review, not a human gate.
- Coding agent may refine details but should stay on the stated goal and non-goals.
- Collector boundary: if implementation introduces unbounded collection, ship only a bounded collector patch that starts durably in the background after merge. The coding agent and lokay must not populate data or wait for collection to finish.
