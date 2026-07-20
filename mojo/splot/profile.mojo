"""Load Splot fusion profiles from TOML only (policy, not evaluators)."""

from std.pathlib import Path
from emberjson import Value
from splot.toml import parse_toml_value


def load_profile_toml(path: String) raises -> Value:
    """Read a profile.toml (or any TOML profile file) into a Value tree."""
    var text = Path(path).read_text()
    return parse_toml_value(text, path)


def load_profile_text(text: String, path: String = "<memory>") raises -> Value:
    return parse_toml_value(text, path)
