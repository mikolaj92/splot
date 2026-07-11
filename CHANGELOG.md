# Changelog

Splot follows simple semantic versioning while the API stabilizes:

- patch: bug fixes and documentation-only changes
- minor: backward-compatible profile, CLI, or report additions
- major: breaking changes to public models, CLI, or report schema

## 0.2.0

- Entropy-minimization pass across the arbitration pipeline (in the cybernetic
  tradition Splot builds on; still counting and spread only, no probability
  math): feedback reliability updates keyed by `selected_source_ids`; evidence
  confidence and source reliability feed belief uncertainty; opt-in
  `scoring.use_source_reliability`; wave `max_age_seconds` staleness and
  `silent_sources` reporting; named uncertainty components with a
  `dominant_component`; contested-candidate conflicts and deduplicated
  cross-round conflict persistence; `range: [low, high]` signal normalization.
- Multi-source fusion in `observation.value`: opt-in `reduce`
  (`last`/`mean`/`median`/`min`/`max`) fuses the newest value per wave,
  disagreement above `tolerance` lowers signal confidence and names the
  disagreeing sources, and per-source attribution reaches the evidence.
- Belief accumulation across rounds: per-candidate `rounds_seen`, opt-in
  `belief.smoothing` of support/opposition, and a winner-streak uncertainty
  reduction that is always recorded explicitly in the report.
- LLM-ready context pack: `splot context-pack`, `build_context_pack`, and the
  `postprocess.context_pack` postprocessor emit one condensed deterministic
  signal with an explicit `omitted` registry and always-on redaction.
- Documented the theoretical foundation: Splot is presented as a cybernetic
  mechanism after Marian Mazur (qualitative theory of information, theory of
  autonomous systems) — many signals in, one minimized-entropy decision signal
  out — across the README, conceptual model, Fala integration note, package
  docstring, and package metadata. No runtime behavior changed.
- Added CI, license metadata, report/state/profile schemas, version and digest
  metadata, static HTML report export, report redaction, report comparison, and
  weight explanation helpers.
- Hardened profile diagnostics, composition audit fields, Fala-shaped example,
  and documentation around providers, reports, YAML subset, security, and
  releases.
- Aligned the Fala adapter with the archetypal Fala runtime: Carrier ->
  candidate source and Observation -> observation input mapping, first-class
  `observations` output, `splot.decision_committed` event, `splot.human_decision`
  gate, dotted `splot.decision_report` / `splot.state` artifact kinds, a Fala
  `{values, observations, artifacts, metadata}` step output using `fala.sdk` when
  present, a manifest-step `splot-fala-step` entrypoint, an updated
  carrier-package example, and a Fala/Splot boundary architecture note.
- Declared Fala 0.1.0 as the integration baseline, installed explicitly from
  the GitHub tag when the SDK-backed path is needed; Splot's published package
  metadata stays PyPI-safe with `dependencies = []`, no direct URL
  `Requires-Dist`, and the import-free fallback when Fala is absent.
- Raised the minimum Python to 3.12 to match the Fala runtime (was 3.11).
- Publish as the `splot-runtime` distribution (the PyPI name `splot` is an
  unrelated PySAL package); the import package and console scripts stay
  `splot` / `splot-fala-step`.

## 0.1.0

- Initial standalone Splot runtime.
- Folder-based profiles with safe provider references.
- Weighted scoring, constraints, decision policies, stability, composition,
  evidence, belief, state, reports, CLI, examples, and optional Fala-shaped
  integration.
