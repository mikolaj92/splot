# Conceptual Model

Splot is domain-agnostic. A camera, document, model output, sensor, queue item,
or human note can all be represented as sources, observations, evidence, and
candidates. The core never imports domain libraries.

## Concepts

- Wave: a source or carrier of partial information.
- Projection: what a wave preserves, loses, or distorts.
- Observation: a concrete reading, fragment, event, or metric.
- Evidence: interpreted support for or against a candidate.
- Belief: current state, uncertainty, history, and reliability.
- Candidate: something Splot may choose, route, compose, defer, or reject.
- Constraint: a profile rule that blocks, warns, asks a human, or penalizes.
- Verifier: a stronger registered check.
- Policy: the arbitration behavior.
- Stability: rules that prevent thrashing and premature switching.
- Decision: committed result.
- Feedback: information returned after execution.
- Trace: the machine-readable decision report.

The camera/director metaphor is only one example. The technical concept is
stateful information arbitration.

Every round now emits:

- candidate evaluations with signals, scores, constraints, and verifier results
- evidence, either from registered builders or signal-derived defaults
- belief snapshot with conflicts, stale sources, reliability, and history
- decision report suitable for replay, debugging, and audit
