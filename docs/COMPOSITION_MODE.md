# Composition Mode

Composition mode chooses candidates per required slot or section. A candidate
declares its slot in `payload.section` or `payload.slot`.

The result is a composition plan:

```json
{
  "selected_by_section": {
    "intro": "intro_a"
  },
  "missing_required": []
}
```

Missing required slots and human-decision constraints make the decision status
`needs_human_decision`. The core does not merge prose, analyze contracts, or
normalize style; those actions belong in registered postprocessors.

