# Profile format (TOML only)

```toml
version = 1
id = "example"
mode = "select_one"

[objective]
id = "best"

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

Markdown sidecars in profile folders are optional documentation only.
