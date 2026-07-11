# Conceptual Model

Splot is domain-agnostic. A camera, document, model output, sensor, queue item,
or human note can all be represented as sources, observations, evidence, and
candidates. The core never imports domain libraries.

## Theoretical Foundation: Mazur's Cybernetics

Splot is designed as a cybernetic mechanism in the tradition of Marian Mazur,
founder of the Polish school of cybernetics. Two of his works anchor the
design: the qualitative theory of information (*Jakościowa teoria informacji*,
1970) and the theory of autonomous systems (*Cybernetyczna teoria układów
samodzielnych*, 1966). The runtime's single job: accept many communicates and
emit one decision signal with minimized entropy, while recording the
uncertainty that remains and why the decision was committed. (One precision:
Mazur's qualitative theory deliberately describes information without
Shannon's probabilities — as transformations between communicates. Splot
borrows the entropy shorthand from the wider cybernetic tradition, and Mazur's
vocabulary for everything else.)

This is why the runtime is constructed the way it is:

- **Waves** carry communicates. Distortion (loss, noise, bias) is first-class:
  Splot tracks it via wave `reliability`, per-signal `confidence`, `stale_sources`,
  disagreement on `reduce`, source reliability feedback, and explicit conflicts
  in belief. Splot core does not define a `Projection` type — that is a
  carrier-layer concern (Fala).
- **Evidence and belief** are the correlator (korelator) of an autonomous
  system: incoming communicates are registered, correlated against each other
  and against history, and condensed into a belief state with explicit
  uncertainty, conflicts, and reliability.
- **Reliability and stale sources** exist because Mazur's information theory
  treats distortion as first-class: communicates can transinform (faithfully),
  pseudo-inform, or disinform. A mechanism that arbitrates signals must track
  how much each source can be trusted, not only what it says. Redaction is
  separate: it protects the audit trace (DecisionReport) from leaking sensitive
  values when the trace is exported or fed to other systems.
- **Constraints, verifiers, and human-decision escalation** implement control
  in the system's own interest: an autonomous system (układ samodzielny) does
  not merely react — it protects itself. Blocking, warning, penalizing, and
  escalating to a human are that protection.
- **Stability rules** (hysteresis, cooldown, min-hold, debounce, switching
  cost) are the homeostat: they keep the mechanism in functional equilibrium
  and prevent the output signal from oscillating faster than the world it
  controls, which would re-inject entropy downstream.
- **Decision and feedback** close the loop through the effectors: the
  committed decision acts, and feedback (sprzężenie zwrotne) returns as new
  observations for the next round.
- **The trace** (`DecisionReport`) makes the uncertainty accounting auditable.
  A mechanism that only outputs a decision asserts its entropy reduction; a
  mechanism that outputs a replayable report shows its work — every input,
  score, constraint, and the remaining uncertainty can be inspected and
  replayed.

The framing changes nothing about how the code executes. It exists so that a
human or an agent reading this codebase understands the intent behind each
stage rather than treating the pipeline as arbitrary structure.

## Concepts

- Wave: a source or carrier of partial information.
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
