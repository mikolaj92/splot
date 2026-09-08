# Approach plan

<!-- lokay-approach source=deterministic repo=mikolaj92/splot issue=21 -->

Repository: `mikolaj92/splot`  
Issue: #21 — README/pixi 0.3.2 i „Not a Python package”, produkt jest 0.4.0 z python/splot

## Goal

README: Version 0.3.2, „There is no Python runtime”, „Not a Python package”.
`pixi.toml` version 0.3.2.

## Files likely touched

- `pixi.toml`
- `pyproject.toml`
- `1.0.0`
- `examples/fixtures/player_camera_director.profile.toml`

## Test plan

- Run the smallest useful tests for files touched

## Non-goals

- (none stated)

## Notes

- Trust intentional issue; this plan is evidence for later review, not a human gate.
- Coding agent may refine details but should stay on the stated goal and non-goals.
- Collector boundary: if implementation introduces unbounded collection, ship only a bounded collector patch that starts durably in the background after merge. The coding agent and mill must not populate data or wait for collection to finish.
