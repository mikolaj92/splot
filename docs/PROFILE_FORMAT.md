# Profile Format

A profile is a folder with `profile.yaml` plus optional Markdown sidecars. The
sidecars are loaded for documentation and review; the core decision path uses
the YAML.

If PyYAML is installed, Splot uses `yaml.safe_load`. Without PyYAML it falls
back to a small parser that supports mappings, lists, strings, numbers,
booleans, nulls, and inline scalar lists. The profile is configuration, not a
programming language.

Required fields:

- `version`
- `id`
- `mode`: `select_one`, `compose`, `route`, or `regulate`
- `objective.id`

Common sections:

- `waves`
- `observation_providers`
- `candidate_providers`
- `candidate.provider`
- `signals`
- `scoring`
- `constraints`
- `verifiers`
- `evidence` or `evidence_builders`
- `decision`
- `decision.renderer` or `decision_renderer.provider`
- `stability`
- `uncertainty`
- `feedback_handlers`
- `postprocess`
- `explain`
- `required_providers`
- `sidecars`

Providers are looked up in `FunctionRegistry`. YAML cannot import modules,
execute shell commands, loop, or define arbitrary conditionals.

Built-in provider names:

- `candidate.value`
- `candidate.flag`
- `candidate.available`
- `candidates.static`
- `candidates.from_observation_values`
- `observation.value`
- `observations.static`
- `state.is_current`
- `always.pass`
- `evidence.payload`
- `score.weighted`
- `decision.render_summary`
- `postprocess.identity`
- `postprocess.context_pack`
- `feedback.acceptance_reliability`

Signal options (all optional):

- `prefer`: `higher`, `lower`, `target` (with `target: VALUE`), or `boolean`
- `range: [low, high]`: rescales raw units into `0..1` before `prefer` is
  applied; a `target` is rescaled with the same transform
- `reduce`: `last`, `mean`, `median`, `min`, or `max` — with
  `observation.value`, fuses the newest value per wave instead of silently
  taking the last write; a spread above `tolerance` (default `0.1`) lowers the
  signal confidence proportionally and records which sources disagreed.
  Without `reduce` the provider keeps its original last-write behavior.

Belief options (`belief` section, all optional):

- `contested_threshold` (default `0.25`): a candidate whose support and
  opposition both exceed it is flagged as a `contested_candidate` conflict
- `smoothing` (default `0`, off): weight in `[0, 1)` given to the previous
  round's support/opposition (exponential smoothing across rounds)
- `stability_step` / `stability_cap` (defaults `0` / `0.2`): each extra round
  the same candidate stays on top reduces belief uncertainty by `step`, capped
  at `cap`; the reduction is recorded explicitly in the report, never silent

Wave options:

- `reliability`: `0..1`
- `max_age_seconds`: the wave counts as stale unless it has an observation
  newer than this

Scoring options:

- `use_source_reliability` (default `false`): weigh candidate scores by the
  minimum reliability of their sources

Important validation rules:

- wave reliability must be between `0` and `1`, `max_age_seconds` non-negative
- signal `prefer` must be `higher`, `lower`, `target`, or `boolean`
- signal weights must be non-negative and total positive
- signal `range` must be `[low, high]` with `low < high`
- signal `reduce` must be `last`, `mean`, `median`, `min`, or `max`, and
  `tolerance` non-negative
- `belief.smoothing` must be in `[0, 1)`; `belief.contested_threshold`,
  `belief.stability_step`, and `belief.stability_cap` must be non-negative
- constraints can reference only known signal IDs
- constraint operators and severities are allowlisted
- composition sections must have unique IDs
- composition compatibility rules must use `forbid_together` or `require_together`

Use profile diagnostics when editing a profile:

```bash
PYTHONPATH=src python -m splot.cli profile diagnose examples/profiles/player-camera-director
```

`diagnose` prints file and line information for validation failures when the
failing provider, policy, signal, or section can be located.

It also warns about declared Markdown sidecars that are missing, undeclared
sidecars when `sidecars` is present, missing required providers, and YAML
features outside Splot's fallback parser. See `docs/YAML_SUBSET.md` and
`docs/PROVIDERS.md`.
