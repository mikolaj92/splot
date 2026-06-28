# Providers

Splot keeps domain work outside the core. Engineers register Python functions,
and profiles reference those functions by safe names.

```python
from splot import FunctionContext, FunctionRegistry

registry = FunctionRegistry()

def my_signal(context: FunctionContext) -> float:
    return context.candidate.payload.get("score", 0)

registry.register("example.score", my_signal, category="signal_provider")
```

Profiles can then use:

```yaml
signals:
  - id: score
    provider: example.score
    weight: 1
```

Supported categories are descriptive only in the MVP: signal providers,
constraint predicates, verifiers, evidence builders, observation providers,
candidate providers, scorers, postprocessors, decision renderers, and feedback
handlers.

Profiles may also declare:

```yaml
required_providers:
  - example.score
```

`splot profile diagnose PROFILE` reports missing required providers when a
registry is supplied by the application or CLI.
