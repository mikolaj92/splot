# Exclusive Mojo — minimal product

**Release: 0.3.x**

Splot is a **Mojo-only fusion step**: several host-supplied signal streams
(candidates) → one commitment (`select_one` or `compose_one`). No Python
product, no report suite, no storage product, no embedded evaluators.

## In tree

- `mojo/splot/` — engine (`registry`, pipeline, Fala adapter)  
- TOML profiles only (fusion policy, not domain/evaluator code)  
- Host-registered **payload reader recipes** (not free-form plugins)  
- Fala JSON boundary (`adapters_fala.mojo`) without artifact files  
- Smokes: `core_round`, `fala_stdio`, `host_readers`, `compose_envelope`  

## Out of product

- Decision report platform / schema suite  
- State file stores  
- HTML / audit / CLI operator suite  
- YAML / Python runtime  
- LLM / CV / RAG / “evaluator plugins” as Splot features  
- Source or stream **management** APIs  

## Proof

```bash
./tools/mojo_run.sh mojo/smoke/core_round.mojo
./tools/mojo_run.sh mojo/smoke/fala_stdio.mojo
```

Intent and shipped-vs-target: [`CONCEPTUAL_MODEL.md`](CONCEPTUAL_MODEL.md).
