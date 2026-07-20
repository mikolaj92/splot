# Profile format (TOML only)

A profile is a **declarative fusion policy**. It does not define evaluators,
models, or domain logic. Signal **values** arrive in candidate payloads from
the host; the profile only says how Splot **reads, weights, constrains, and
commits**.

```toml
version = 1
id = "example"
mode = "select_one"   # or "compose_one"

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

# Only for mode = "compose_one"
[compose]
min_score = 0.3
max_parts = 3
```

## Field notes

| Piece | Meaning |
| --- | --- |
| `mode` | `select_one` (default) or `compose_one` (multi-stream composition). |
| `[[signals]]` | Named inputs to the fusion score. `provider` is a **payload reader**, not an evaluator. |
| `provider = "candidate.value"` | Read `field` from the candidate JSON payload (host already set the number). |
| Host providers | Any other name must be registered on `ReaderRegistry` (or `readers` in fusion JSON) with a **recipe** that only maps payload fields. |
| `weight` / `prefer` / `min` | How Splot normalizes and gates that signal. |
| `[[constraints]]` | Block / warn / penalize / escalate — commitment protection. |
| `[decision]` | Rank/commit policy and close-margin behavior. |
| `[stability]` | Homeostat for `select_one` (e.g. hysteresis). |
| `[compose]` | Thresholds for `compose_one` (`min_score`, `max_parts`). |
| `[uncertainty]` | What to do when all blocked or scores are too close (`select_one`). |

### Builtin readers (not evaluators)

| Name | Role |
| --- | --- |
| `candidate.value` | Numeric field from payload |
| `candidate.available` | Boolean live/available gate |
| `state.is_current` | Prefer the previously committed candidate |

### Host-registered recipes (examples)

| Recipe | Meaning |
| --- | --- |
| `value:field` | Read named numeric field |
| `product:a,b` | Product of two fields |
| `sum:a,b` / `min:a,b` / `max:a,b` | Combine two fields |
| `invert:field` | `1 - clamp01(field)` |
| `bool:field` | true/1 → 1.0 |
| Gate: `bool:ready`, `gte:score,0.5`, `available` | Constraint providers |

Whether a field was filled by an LLM, a detector, or `random()` is outside the
profile language.

Markdown sidecars in profile folders are optional documentation only.
