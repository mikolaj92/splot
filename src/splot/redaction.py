from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_SENSITIVE_KEYS = {"api_key", "authorization", "password", "secret", "token"}
REDACTED = "[REDACTED]"


def redact_value(value: Any, fields: list[str] | None = None) -> Any:
    copied = deepcopy(value)
    _redact_default_keys(copied)
    for field in fields or []:
        _redact_path(copied, field.split("."))
    return copied


def _redact_default_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in list(value.items()):
            if key.lower() in DEFAULT_SENSITIVE_KEYS:
                value[key] = REDACTED
            else:
                _redact_default_keys(item)
    elif isinstance(value, list):
        for item in value:
            _redact_default_keys(item)


def _redact_path(value: Any, parts: list[str]) -> None:
    if not parts:
        return
    part = parts[0]
    rest = parts[1:]
    if isinstance(value, list):
        if part == "*":
            for item in value:
                _redact_path(item, rest)
            return
        if part.isdigit() and int(part) < len(value):
            _redact_path(value[int(part)], rest)
        return
    if not isinstance(value, dict) or part not in value:
        return
    if rest:
        _redact_path(value[part], rest)
    else:
        value[part] = REDACTED
