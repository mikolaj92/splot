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
- `feedback.acceptance_reliability`

Important validation rules:

- wave reliability must be between `0` and `1`
- signal `prefer` must be `higher`, `lower`, `target`, or `boolean`
- signal weights must be non-negative and total positive
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
