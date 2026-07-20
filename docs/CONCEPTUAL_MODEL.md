# Conceptual Model

Splot is a **generic fusion organ**: many high-entropy streams of communicates
in, one lower-entropy commitment out. It is **domain-agnostic** and
**evaluator-agnostic**. The core never imports domain libraries and never runs
an evaluation function.

## Design intent (what Splot is for)

```text
  stream₁  stream₂  …  streamₙ     high entropy, noise, conflict, partial views
       \      |      /
        \     |     /
         ─────┼─────
              ▼
            SPLOT                 fuse · constrain · stabilize · commit
              ▼
         one stream / one communicate     lower entropy
```

### Examples (same mechanism)

1. **Live video director**  
   Five camera streams. Something outside Splot (LLM, detector, heuristic, or
   even random) scores each frame or tick — e.g. “player visible?”, “ball in
   frame?”. Splot fuses those signals and commits **one** stream id so the host
   can switch the output feed without thrashing.

2. **Multi-modal tasking**  
   Parallel streams: RAG hits, images, a book chapter, docs, a user prompt, a
   goal. Outside Splot, any evaluators attach signals (relevance, coverage,
   conflict, freshness, …). Splot commits **one** lower-entropy outcome the host
   can act on (e.g. which option to take, or — in a future compose mode — the
   structure of a single task communicate).

The camera metaphor is only an example. The technical concept is **stateful
reduction of uncertainty across communicates**, not camera control and not
AI-stack management.

### Hard boundaries

| Splot does | Splot does not |
| --- | --- |
| Fuse host-supplied signals under a profile | Manage sources, queues, or workflows |
| Commit one result per round (with stability) | Call LLMs, CV, RAG, or “the evaluator” |
| Stay ignorant of what a field *means* | Decode video, parse PDFs, embed text |
| Optional stickiness so output does not oscillate | Own persistence, audit HTML, or ops UI |

**Evaluator-agnostic:** the function that produced a signal may be an LLM, a
three-line algorithm, a human click, or `random()`. Splot does not branch on
evaluator type. It only sees communicates (payload fields + optional reliability
metadata the host chooses to supply).

**Domain-agnostic:** a camera id, a document chunk, a model draft, a route, or a
queue item are all representable as candidates (or waves) with payloads. The
core has no domain types.

Splot is **not** an explicit management or arbitration *product*. “Arbitration”
in older wording only meant “pick/commit under rules” — not admin, not
orchestration.

## Theoretical foundation (Mazur)

Splot is framed in the tradition of Marian Mazur (Polish school of cybernetics):
qualitative information theory (*Jakościowa teoria informacji*, 1970) and
autonomous systems (*Cybernetyczna teoria układów samodzielnych*, 1966).

Runtime intent: accept many communicates and emit **one** decision signal with
**reduced** entropy, while remaining honest about residual uncertainty and why
the commitment was made.

Precision: Mazur’s qualitative theory describes information as transformations
between communicates, not as Shannon probabilities. Splot borrows the entropy
shorthand from the wider cybernetic tradition and Mazur’s vocabulary for the
rest (correlator, homeostat, feedback).

| Idea | Role in Splot |
| --- | --- |
| **Waves / communicates** | Carriers of partial information from streams (host-owned media; Splot sees signals) |
| **Correlator (korelator)** | Fuse signals across candidates; optional richer belief is design target |
| **Distortion** | Reliability, stale, confidence — first-class *when the host supplies them* |
| **Homeostat** | Stability rules (hysteresis, close margin, keep previous) so the output does not re-inject entropy by thrashing |
| **Feedback** | Committed decision acts via host effectors; new observations enter the next round |
| **Self-protection** | Constraints (block / warn / penalize / escalate) — profile policy, not a management console |

## Concepts

- **Stream / wave** — a source or carrier of partial information (camera feed,
  RAG channel, doc stream, prompt, …). Media stays with the host.
- **Communicate / observation** — a concrete reading at a moment (metrics in a
  payload, not the raw video/token bytes).
- **Candidate** — something Splot may commit to (select, and later optionally
  compose into / defer / reject).
- **Signal** — a scalar (or flag) Splot reads from the candidate payload under
  the profile. **Origin of the number is out of scope.**
- **Profile** — declarative fusion policy: objective, weights, constraints,
  decision and stability rules. No domain code, no evaluator code.
- **Constraint** — block / warn / penalize / ask human — protection of the
  commitment, not “source management.”
- **Policy** — how eligible candidates are ranked and chosen.
- **Stability** — homeostat: hysteresis and related rules against thrashing.
- **Decision / commitment** — the single lower-entropy result for this round.
- **State** — minimal memory (e.g. previous decision) so stability can work.
- **Feedback** — host applies the decision; later rounds see new signals.

Optional richer notions (**evidence**, **belief**, full **trace/report**,
**verifiers** as registered checks) belong to the design target for deeper
uncertainty accounting. They are **not** required to understand or use the
0.3.x fusion loop.

## Shipped vs design target

Documentation used to describe a rich belief / DecisionReport surface in the
present tense while the Mojo product was intentionally slim. This section is
the honest split.

### Shipped in 0.3.x+ (Mojo product)

- TOML profile + candidates with JSON payloads
- Builtin **payload readers**: `candidate.value`, `candidate.available`,
  `state.is_current` (how to *read* fields — not how to *score* the world)
- **Host-registered readers** (`ReaderRegistry` / optional `readers` in
  `fusion_step` JSON): named recipes over host-supplied fields; unknown names
  fail closed; still not evaluators
- Weighted normalize → constraints → rank
- Modes: **`select_one`** (one id) and **`compose_one`** (multi-stream
  `decision.composed` parts + primary id)
- Hysteresis / close-margin style stability for `select_one`
- Envelope: `decision` + `state` + **`evaluations`** detail from `run_round`
  (Fala step remains thin unless `include_evaluations` / `detail`)
- No report store, HTML suite, Python product, or YAML
- Optional Fala JSON / subprocess step — host still owns evaluators

### Design target (not yet product surface)

- Richer wave / reliability / stale / conflict accounting when hosts supply it
- Belief snapshot and long-lived replay/audit store (still not a report
  *product* or management UI)
- Multi-wave timing models beyond “one host batch per round” if needed by hosts

Code follows the shipped contract. Intent documents the organ we are building
toward so agents and humans do not confuse fusion with management or with
evaluation.

## Pipeline (logical)

```text
host evaluators (any)     →  candidate payloads (signals)
profile (TOML)            →  weights, constraints, stability
                ╲         ╱
                 ╲       ╱
                  SPLOT round
                      │
                      ▼
              one commitment + next state
```

1. Host runs whatever evaluations it wants (or none, or random).
2. Host builds candidates + payloads.
3. Splot runs one fusion round under the profile.
4. Host acts on `selected_candidate_id` (switch stream, start task, …).
5. Host feeds previous decision back as state on the next tick if stickiness
   matters.

## Reading this repo

| Document | Role |
| --- | --- |
| [README](../README.md) | Product entry, contract, proof |
| [PROFILE_FORMAT](PROFILE_FORMAT.md) | TOML surface |
| [FALA_INTEGRATION](FALA_INTEGRATION.md) | Optional host mapping |
| [MOJO_PORT](MOJO_PORT.md) | What is in / out of the Mojo product |
| `examples/profiles/` | Illustrative fusion policies (not domain engines) |
