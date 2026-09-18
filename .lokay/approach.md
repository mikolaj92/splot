# Approach plan

<!-- lokay-approach source=deterministic repo=mikolaj92/splot issue=41 -->

Repository: `mikolaj92/splot`  
Issue: #41 — [code-audit] Observation, switching_cost, source_ids, stability_memory — martwy publiczny model

## Goal

Publiczny model 0.4.1 eksportuje pola i typ, których silnik **nigdy nie czyta** i których JSON-owy `fusion_step` **nigdy nie wypełnia**. Host widzi je w `state` / Mojo API i myśli, że homeostat albo fale z nich korzystają.

## Files likely touched

- `models.mojo`
- `__init__.mojo`

## Test plan

- `Observation` znika z produktu albo ma jednego callera i smoke
- `source_ids_json` / `switching_cost` albo wchodzą do JSON contract + pipeline, albo znikają z `Candidate`
- `stability_memory` albo jest czytane przez homeostat, albo nie wychodzi w `SplotState.to_json`
- `stability.policy = "switching_cost"` albo używa kosztu kandydata, albo fail-closed jako nieobsługiwane (dziś alias hysteresis)

## Non-goals

- Implementacja wave runtime / Observation pipeline. #40 (fixture waves).

## Notes

- Trust intentional issue; this plan is evidence for later review, not a human gate.
- Coding agent may refine details but should stay on the stated goal and non-goals.
- Collector boundary: if implementation introduces unbounded collection, ship only a bounded collector patch that starts durably in the background after merge. The coding agent and lokay must not populate data or wait for collection to finish.
