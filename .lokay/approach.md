# Approach plan

<!-- lokay-approach source=deterministic repo=mikolaj92/splot issue=40 -->

Repository: `mikolaj92/splot`  
Issue: #40 — Fixture kamery obiecuje waves/min_hold/request_more_evidence; silnik tego nie czyta

## Goal

Shipped fixture `examples/fixtures/player_camera_director.profile.toml` nadal obiecuje klucze, których silnik **nie czyta**. #29 przepisało `examples/profiles/*` (`4de19fd`). Tego fixture nikt nie ruszył — a to on idzie przez `step-fixture`, `core_round`, pytest `fuse` i FunBall.

## Files likely touched

- `examples/fixtures/player_camera_director.profile.toml`
- `stab.policy`

## Test plan

- Fixture kamery ma wyłącznie klucze, które pipeline/parser honoruje jako semantykę (`select_one`, builtin readers, `hysteresis`+`min_improvement`, `when_close` / `when_constraints_block_all` shipped)
- Albo `min_hold_ms` / `cooldown_ms` działają względem `last_switch_at`, albo znikają z fixture
- `[[waves]]` i `request_more_evidence` znikają albo stają się błędem fail-closed (nie cisza)
- Smoke/pytest ładuje ten fixture i nie zależy od martwych kluczy

## Non-goals

- Implementacja evidence homeostatu / wave runtime. To osobny produkt, nie cichy dodatek w fixture.

## Notes

- Trust intentional issue; this plan is evidence for later review, not a human gate.
- Coding agent may refine details but should stay on the stated goal and non-goals.
- Collector boundary: if implementation introduces unbounded collection, ship only a bounded collector patch that starts durably in the background after merge. The coding agent and lokay must not populate data or wait for collection to finish.
