# Policies

## Decision Policies

- `weighted_score`: choose the highest score.
- `constrained_weighted_score`: choose the highest eligible score.
- `keep_current_when_close`: keep previous when scores are close.
- `require_human_when_ambiguous`: ask a human when top candidates are close.
- `fallback_when_no_candidate`: fallback if nothing is eligible.
- `section_by_section_composition`: choose candidates per composition slot.
- `route_by_best_match`: route to the best candidate path.

## Stability Policies

- `none`: accept the proposed decision.
- `hysteresis`: switch only when the score margin reaches `min_improvement`.
- `cooldown`: block switches until `cooldown_ms` passes.
- `minimum_decision_duration`: use `min_hold_ms` to hold a decision.
- `debounce`: require the same proposal for `rounds`.
- `hold_then_recheck`: keep a pending proposal until `hold_ms` passes.
- `switching_cost`: subtract candidate/profile switching cost from margin.
- `prefer_current_when_close`: a hysteresis-style current-candidate preference.

Policies are deliberately small. Domain-specific scoring and validation should
be registered functions, not YAML logic.

