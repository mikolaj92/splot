# Exclusive Mojo — minimal product

**Release: 0.3.0**

Splot is a **Mojo-only** arbitration step: compose several signals into one
decision. No Python product, no report suite, no storage product.

## In tree

- `mojo/splot/` — engine  
- TOML profiles only  
- Fala JSON boundary (`adapters_fala.mojo`) without artifact files  

## Out of product

- Decision report platform / schema suite  
- State file stores  
- HTML / audit / CLI operator suite  
- YAML / Python runtime  

## Proof

```bash
./tools/mojo_run.sh mojo/smoke/core_round.mojo
./tools/mojo_run.sh mojo/smoke/fala_stdio.mojo
```
