from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ProfileError(ValueError):
    pass


@dataclass
class SplotProfile:
    raw: dict[str, Any]
    path: Path | None = None
    sidecars: dict[str, str] | None = None

    @property
    def id(self) -> str:
        return str(self.raw.get("id", ""))

    @property
    def mode(self) -> str:
        return str(self.raw.get("mode", "select_one"))

    @property
    def objective_id(self) -> str:
        objective = self.raw.get("objective") or {}
        return str(objective.get("id", self.id))


def load_profile(path_or_data: str | Path | dict[str, Any] | SplotProfile) -> SplotProfile:
    if isinstance(path_or_data, SplotProfile):
        return path_or_data
    if isinstance(path_or_data, dict):
        profile = SplotProfile(raw=path_or_data)
        validate_profile(profile)
        return profile

    path = Path(path_or_data)
    profile_file = path / "profile.yaml" if path.is_dir() else path
    if not profile_file.exists():
        raise ProfileError(f"profile file does not exist: {profile_file}")

    raw = load_simple_yaml(profile_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProfileError("profile.yaml must contain a mapping")

    sidecars: dict[str, str] = {}
    if profile_file.parent.exists():
        for file in sorted(profile_file.parent.glob("*.md")):
            sidecars[file.name] = file.read_text(encoding="utf-8")

    profile = SplotProfile(raw=raw, path=profile_file.parent, sidecars=sidecars)
    validate_profile(profile)
    return profile


def validate_profile(profile: SplotProfile, registry: Any | None = None) -> None:
    data = profile.raw
    for field in ("version", "id", "mode", "objective"):
        if field not in data:
            raise ProfileError(f"profile missing required field: {field}")
    if profile.mode not in {"select_one", "compose", "route", "regulate"}:
        raise ProfileError(f"unsupported mode: {profile.mode}")
    if not isinstance(data.get("objective"), dict) or "id" not in data["objective"]:
        raise ProfileError("objective.id is required")

    signals = data.get("signals") or []
    if not isinstance(signals, list):
        raise ProfileError("signals must be a list")
    signal_ids: set[str] = set()
    total_weight = 0.0
    for signal in signals:
        if not isinstance(signal, dict) or not signal.get("id"):
            raise ProfileError("each signal needs an id")
        if signal["id"] in signal_ids:
            raise ProfileError(f"duplicate signal id: {signal['id']}")
        signal_ids.add(signal["id"])
        weight = _as_number(signal.get("weight", 1.0), f"signal {signal['id']} weight")
        if weight < 0:
            raise ProfileError(f"signal {signal['id']} weight must be non-negative")
        total_weight += weight
        if signal.get("provider") and registry is not None and not registry.has(signal["provider"]):
            raise ProfileError(f"unregistered signal provider: {signal['provider']}")
    if profile.mode in {"select_one", "route", "regulate", "compose"} and signals and total_weight <= 0:
        raise ProfileError("at least one signal weight must be positive")

    for constraint in data.get("constraints") or []:
        if not isinstance(constraint, dict) or not constraint.get("id"):
            raise ProfileError("each constraint needs an id")
        signal_ref = constraint.get("signal")
        if signal_ref and signal_ref not in signal_ids:
            raise ProfileError(f"constraint references unknown signal: {signal_ref}")
        provider = constraint.get("provider")
        if provider and registry is not None and not registry.has(provider):
            raise ProfileError(f"unregistered constraint provider: {provider}")
        if constraint.get("severity") not in {None, "block", "warn", "human_decision", "penalize"}:
            raise ProfileError(f"invalid constraint severity: {constraint.get('severity')}")

    for verifier in data.get("verifiers") or []:
        provider = verifier.get("provider") if isinstance(verifier, dict) else None
        if provider and registry is not None and not registry.has(provider):
            raise ProfileError(f"unregistered verifier: {provider}")

    decision = data.get("decision") or {}
    policy = decision.get("policy", "constrained_weighted_score")
    known_policies = {
        "weighted_score",
        "constrained_weighted_score",
        "keep_current_when_close",
        "require_human_when_ambiguous",
        "fallback_when_no_candidate",
        "section_by_section_composition",
        "route_by_best_match",
    }
    if policy not in known_policies:
        raise ProfileError(f"unsupported decision policy: {policy}")

    stability = data.get("stability") or {}
    stability_policy = stability.get("policy", "none")
    known_stability = {
        "none",
        "hysteresis",
        "debounce",
        "cooldown",
        "hold_then_recheck",
        "minimum_decision_duration",
        "switching_cost",
        "prefer_current_when_close",
    }
    if stability_policy not in known_stability:
        raise ProfileError(f"unsupported stability policy: {stability_policy}")
    for field in (
        "min_improvement",
        "min_hold_ms",
        "cooldown_ms",
        "hold_ms",
        "duration_ms",
        "switching_cost",
    ):
        if field in stability and _as_number(stability[field], f"stability.{field}") < 0:
            raise ProfileError(f"stability.{field} must be non-negative")
    if "rounds" in stability and int(stability["rounds"]) < 1:
        raise ProfileError("stability.rounds must be >= 1")

    if profile.mode == "compose":
        composition = data.get("composition") or {}
        sections = composition.get("sections") or []
        if not sections:
            raise ProfileError("compose mode requires composition.sections")

    for postprocessor in data.get("postprocess") or []:
        provider = postprocessor.get("provider") if isinstance(postprocessor, dict) else None
        if provider and registry is not None and not registry.has(provider):
            raise ProfileError(f"unregistered postprocessor: {provider}")


def _as_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ProfileError(f"{label} must be a number")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ProfileError(f"{label} must be a number") from exc


def load_simple_yaml(text: str) -> Any:
    """Small YAML subset parser for Splot profiles.

    It intentionally supports only mappings, lists, scalars, and inline scalar
    lists. Use PyYAML in an application if you need full YAML.
    """

    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        clean = _strip_comment(raw_line).rstrip()
        if not clean.strip():
            continue
        indent = len(clean) - len(clean.lstrip(" "))
        if indent % 2:
            raise ProfileError("YAML indentation must use multiples of two spaces")
        lines.append((indent, clean.lstrip(" ")))
    if not lines:
        return {}
    value, index = _parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ProfileError("could not parse full YAML document")
    return value


def _parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return None, index
    current_indent, content = lines[index]
    if current_indent != indent:
        raise ProfileError("unexpected indentation")
    if content.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_map(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ProfileError("unexpected nested mapping")
        if content.startswith("- "):
            break
        key, sep, raw_value = content.partition(":")
        if not sep:
            raise ProfileError(f"expected key: value, got: {content}")
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value:
            result[key] = _parse_scalar(raw_value)
            index += 1
            continue
        index += 1
        if index < len(lines) and lines[index][0] > indent:
            result[key], index = _parse_block(lines, index, lines[index][0])
        else:
            result[key] = None
    return result, index


def _parse_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or not content.startswith("- "):
            break
        item = content[2:].strip()
        if not item:
            index += 1
            if index < len(lines) and lines[index][0] > indent:
                value, index = _parse_block(lines, index, lines[index][0])
            else:
                value = None
            result.append(value)
            continue
        if _looks_like_key_value(item):
            key, _, raw_value = item.partition(":")
            value: dict[str, Any] = {key.strip(): _parse_scalar(raw_value.strip())}
            index += 1
            if index < len(lines) and lines[index][0] > indent:
                nested, index = _parse_block(lines, index, lines[index][0])
                if isinstance(nested, dict):
                    value.update(nested)
                else:
                    raise ProfileError("list item mapping cannot be followed by a list")
            result.append(value)
            continue
        result.append(_parse_scalar(item))
        index += 1
    return result, index


def _looks_like_key_value(text: str) -> bool:
    if ":" not in text:
        return False
    before, after = text.partition(":")[::2]
    return bool(before.strip()) and (not after or after.startswith(" "))


def _parse_scalar(value: str) -> Any:
    if value == "":
        return None
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inside = value[1:-1].strip()
        if not inside:
            return []
        return [_parse_scalar(item.strip()) for item in inside.split(",")]
    try:
        if any(char in value for char in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return value


def _strip_comment(line: str) -> str:
    quote: str | None = None
    for index, char in enumerate(line):
        if char in {"'", '"'}:
            quote = None if quote == char else char
        if char == "#" and quote is None:
            return line[:index]
    return line

