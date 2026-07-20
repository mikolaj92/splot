# Profile Format (TOML only)

A profile is a folder with `profile.toml` plus optional Markdown sidecars
(`objective.md`, `signals.md`, …). Sidecars are documentation; the runtime
loads **only** `profile.toml`.

YAML is not supported.

## Shape

```toml
version = 1
id = "example"
mode = "select_one"

[objective]
id = "best"
description = "..."

[[signals]]
id = "visibility"
provider = "candidate.value"
field = "visibility"
weight = 0.5
prefer = "higher"
min = 0.6

[[constraints]]
id = "live"
provider = "candidate.available"
severity = "block"

[decision]
policy = "constrained_weighted_score"
tie_breaker = "keep_current"
close_margin = 0.05

[stability]
policy = "hysteresis"
min_improvement = 0.15

[uncertainty]
when_close = "keep_previous"
when_constraints_block_all = "fallback"
```

## Providers (native builtins)

- `candidate.value` — payload field
- `candidate.available` — live flag
- `state.is_current` — previous selection bonus

No free-form user code. Extend builtins in `mojo/splot/builtins.mojo`.
