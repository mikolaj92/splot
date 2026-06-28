from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import SplotValidationError


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


class SchemaValidationError(SplotValidationError):
    pass


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate_with_schema(value: dict[str, Any], schema_name: str) -> None:
    schema = load_schema(schema_name)
    _validate(value, schema, path="$")


def validate_profile_data(value: dict[str, Any]) -> None:
    validate_with_schema(value, "profile.schema.json")


def validate_decision_report_data(value: dict[str, Any]) -> None:
    validate_with_schema(value, "decision_report.schema.json")


def validate_state_data(value: dict[str, Any]) -> None:
    validate_with_schema(value, "state.schema.json")


def _validate(value: Any, schema: dict[str, Any], path: str) -> None:
    if "type" in schema:
        _validate_type(value, schema["type"], path)
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path} must be one of {schema['enum']!r}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise SchemaValidationError(f"{path}.{key} is required")
        properties = schema.get("properties") or {}
        for key, item in value.items():
            if key in properties:
                _validate(item, properties[key], f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _validate(item, schema["items"], f"{path}[{index}]")


def _validate_type(value: Any, expected: str | list[str], path: str) -> None:
    expected_types = expected if isinstance(expected, list) else [expected]
    if any(_matches_type(value, item) for item in expected_types):
        return
    raise SchemaValidationError(f"{path} must be {expected}")


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True
