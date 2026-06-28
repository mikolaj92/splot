# Fala-shaped Splot Integration

This example shows how Fala could host Splot without making Fala a runtime
dependency of the core package.

Run the stdin/stdout fallback:

```bash
splot-fala-step < examples/fala-integration/stdin.json
```

A Fala host would treat the emitted decision report as an artifact, emit a
`splot.decision_committed` event when the decision is committed, and open a
manual gate when the decision status is `needs_human_decision`.
