"""Import-free Fala boundary: JSON in, descriptors out (stdio step)."""

from std.collections import List
from std.pathlib import Path
from emberjson import Value, to_string
from splot.json_util import obj_string, parse_json, quote
from splot.models import Candidate, RoundResult, SplotState
from splot.pipeline import run_round
from splot.profile import load_profile_toml


def _candidates_from_input(root: Value) raises -> List[Candidate]:
    var out = List[Candidate]()
    # candidates array
    if root.is_object() and "candidates" in root.object() and root.object()["candidates"].is_array():
        for item in root.object()["candidates"].array():
            if not item.is_object():
                continue
            var id = obj_string(item, "id")
            var payload = "{}"
            if "payload" in item.object():
                payload = to_string(item.object()["payload"].copy())
            out.append(Candidate(id, payload))
    # Fala carriers -> candidates
    if root.is_object() and "carriers" in root.object() and root.object()["carriers"].is_array():
        for item in root.object()["carriers"].array():
            if not item.is_object():
                continue
            var id = obj_string(item, "id", obj_string(item, "carrier_id", "carrier"))
            var payload = "{}"
            if "payload" in item.object():
                payload = to_string(item.object()["payload"].copy())
            out.append(Candidate(id, payload))
    return out^


def _state_from_input(root: Value) raises -> SplotState:
    if not root.is_object() or "state" not in root.object():
        return SplotState()
    var st = root.object()["state"].copy()
    if not st.is_object():
        return SplotState()
    var prev = "{}"
    if "previous_decision" in st.object():
        prev = to_string(st.object()["previous_decision"].copy())
    return SplotState(
        prev,
        obj_string(st, "last_decision_at", ""),
        obj_string(st, "last_switch_at", ""),
        "{}",
    )


def _load_profile(root: Value) raises -> Value:
    var path = obj_string(root, "profile", "")
    if path == "":
        path = obj_string(root, "profile_path", "")
    if path == "":
        # inline profile object (JSON Value tree)
        if root.is_object() and "profile_object" in root.object():
            return root.object()["profile_object"].copy()
        raise Error("splot: profile or profile_path required")
    # Profiles are TOML only (.toml). Reject .yaml/.yml explicitly.
    if path.find(".yaml") >= 0 or path.find(".yml") >= 0:
        raise Error("splot: YAML profiles are not supported; use profile.toml")
    return load_profile_toml(path)


def arbitration_step(input_json: String) raises -> String:
    """Manifest-shaped arbitration; returns Fala-friendly JSON descriptors."""
    var root = parse_json(input_json)
    var profile = _load_profile(root)
    var candidates = _candidates_from_input(root)
    var state = _state_from_input(root)
    var now = obj_string(root, "now", "2026-01-01T00:00:00Z")
    var result = run_round(profile, candidates, state, now)
    var needs_human = result.decision.status == "needs_human_decision"
    var gates = "[]"
    if needs_human:
        gates = "[{\"id\":\"splot.human_decision\",\"kind\":\"manual_decision\"}]"
    var events = (
        "[{\"type\":\"splot.decision_committed\",\"decision_id\":"
        + quote(result.decision.id)
        + ",\"selected_candidate_id\":"
        + (
            quote(result.decision.selected_candidate_id)
            if result.decision.selected_candidate_id != ""
            else "null"
        )
        + ",\"status\":"
        + quote(result.decision.status)
        + "}]"
    )
    return (
        "{\"decision\":"
        + result.decision.to_json()
        + ",\"state\":"
        + result.state.to_json()
        + ",\"decision_report\":"
        + result.report_json
        + ",\"artifacts\":[{\"kind\":\"splot.decision_report\",\"path\":\"decision_report.json\"}"
        + ",{\"kind\":\"splot.state\",\"path\":\"state.json\"}]"
        + ",\"events\":"
        + events
        + ",\"gates\":"
        + gates
        + "}"
    )


def run_stdio_line(line: String) raises -> String:
    """One-line process step used by Fala subprocess effectors."""
    # Merge config/input.values like Python step (simplified: treat whole object as step input)
    var root = parse_json(line)
    if root.is_object() and "input" in root.object():
        var inp = root.object()["input"].copy()
        if inp.is_object() and "values" in inp.object():
            # shallow merge: prefer values fields, keep top-level profile if present
            var values = inp.object()["values"].copy()
            if root.is_object() and "config" in root.object() and root.object()["config"].is_object():
                # use values as primary
                return arbitration_step(to_string(values))
            return arbitration_step(to_string(values))
    return arbitration_step(line)
