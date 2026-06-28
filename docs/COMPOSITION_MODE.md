# Composition Mode

Composition mode chooses candidates per required slot or section. A candidate
declares its slot in `payload.section` or `payload.slot`.

The result is a composition plan:

```json
{
  "selected_by_section": {
    "intro": "intro_a"
  },
  "selected_candidate_by_slot": {
    "intro": "intro_a"
  },
  "missing_required": [],
  "missing_required_slots": [],
  "blocked_candidates_by_slot": {},
  "human_decisions_by_slot": {},
  "global_conflicts": [],
  "compatibility_explanations": [],
  "composed_payload_schema_version": 1,
  "composed_payload": {
    "intro": {}
  },
  "conflicts": []
}
```

Missing required slots and human-decision constraints make the decision status
`needs_human_decision`. The core does not merge prose, analyze contracts, or
normalize style; those actions belong in registered postprocessors.

Generic composition features:

- candidate slot: `payload.section` or `payload.slot`
- candidate dependencies: `Candidate.dependencies`
- compatibility rules: `forbid_together` and `require_together`
- global constraints with `block`, `warn`, or `human_decision` severity
- selected payload plan in `decision.action.plan.composed_payload`
- explicit audit fields for selected candidates, missing slots, blocked
  candidates, human decisions, and compatibility explanations

Block-level composition conflicts produce `conflict`. Missing required slots
and human-decision conflicts produce `needs_human_decision`.
