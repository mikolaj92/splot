# Profile Format

A profile is a folder with `profile.yaml` plus optional Markdown sidecars. The
sidecars are loaded for documentation and review; the core decision path uses
the YAML.

Supported YAML is intentionally small: mappings, lists, strings, numbers,
booleans, nulls, and inline scalar lists. The profile is configuration, not a
programming language.

Required fields:

- `version`
- `id`
- `mode`: `select_one`, `compose`, `route`, or `regulate`
- `objective.id`

Common sections:

- `waves`
- `signals`
- `constraints`
- `verifiers`
- `decision`
- `stability`
- `uncertainty`
- `explain`

Providers are looked up in `FunctionRegistry`. YAML cannot import modules,
execute shell commands, loop, or define arbitrary conditionals.

