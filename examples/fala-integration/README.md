# Fala integration example

JSON stdin shape for a Fala subprocess effector calling Splot as a **fusion
step**. The host (Fala) runs any evaluators and fills candidate payloads; Splot
only commits one result under the profile.

- `stdin.json` — sample step input (signals already in payloads)
- `fala-package.toml` — Fala package stub (subprocess effector; step id may still
  say `arbitrate` for historical host wiring)

Run (with Mojo Splot smoke equivalent):

```bash
./tools/mojo_run.sh mojo/smoke/fala_stdio.mojo
```
