# YAML Subset

Splot uses `yaml.safe_load` when PyYAML is installed. Without PyYAML it falls
back to a small stdlib parser for portable profiles.

The fallback parser supports:

- mappings
- lists
- scalar strings, numbers, booleans, and nulls
- quoted strings
- inline scalar lists such as `[a, b, c]`
- comments outside quotes

The fallback parser does not support:

- tabs for indentation
- anchors and aliases
- merge keys
- inline mappings
- advanced YAML tags

Use `splot profile diagnose PROFILE` to surface constructs that would surprise
the fallback parser.
