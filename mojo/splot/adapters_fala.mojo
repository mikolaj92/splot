"""Import-free Fala boundary: JSON in, fusion descriptors out (stdio step).

Host owns evaluators (LLM, heuristic, random, …) and fills candidate payloads.
Splot only fuses those signals under a TOML profile into one commitment.

Default JSON stays thin (decision + state + events + gates). Set
`include_evaluations` / `detail` true to attach per-candidate fusion detail.
"""

from std.collections import List
from emberjson import Value, to_string
from splot.json_util import obj_bool, obj_string, parse_json, quote
from splot.models import Candidate, RoundResult, SplotState
from splot.pipeline import run_round
from splot.profile import load_profile_toml
from splot.registry import ReaderRegistry


def _candidates_from_input(root: Value) raises -> List[Candidate]:
    var out = List[Candidate]()
    if root.is_object() and "candidates" in root.object() and root.object()["candidates"].is_array():
        for item in root.object()["candidates"].array():
            if not item.is_object():
                continue
            var id = obj_string(item, "id")
            var payload = "{}"
            if "payload" in item.object():
                payload = to_string(item.object()["payload"].copy())
            out.append(Candidate(id, payload))
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
        if root.is_object() and "profile_object" in root.object():
            return root.object()["profile_object"].copy()
        raise Error("splot: profile or profile_path required")
    if path.find(".yaml") >= 0 or path.find(".yml") >= 0:
        raise Error("splot: YAML profiles are not supported; use profile.toml")
    return load_profile_toml(path)


def _registry_from_input(root: Value) raises -> ReaderRegistry:
    """Optional host-declared readers in request JSON (recipes only).

    Shape:
      "readers": {
        "signals": {"host.focus": "product:player,ball"},
        "gates": {"host.ready": "bool:ready"}
      }
    """
    var reg = ReaderRegistry.with_builtins()
    if not root.is_object() or "readers" not in root.object():
        return reg^
    var readers = root.object()["readers"].copy()
    if not readers.is_object():
        return reg^
    if "signals" in readers.object() and readers.object()["signals"].is_object():
        for entry in readers.object()["signals"].object().items():
            var recipe = String("")
            var v = entry.value.copy()
            if v.is_string():
                recipe = v.string()
            else:
                recipe = to_string(v)
            reg.register_signal_reader(entry.key, recipe)
    if "gates" in readers.object() and readers.object()["gates"].is_object():
        for entry in readers.object()["gates"].object().items():
            var grecipe = String("")
            var gv = entry.value.copy()
            if gv.is_string():
                grecipe = gv.string()
            else:
                grecipe = to_string(gv)
            reg.register_gate_reader(entry.key, grecipe)
    return reg^


def fusion_step(input_json: String) raises -> String:
    """One fusion round from host JSON; returns Fala-friendly descriptors.

    Expects candidates (or carriers) with **precomputed** payload signals.
    Does not run evaluators. Emits decision + state + light events/gates —
    not a report product or storage. Optional evaluations when detail is on.
    """
    var root = parse_json(input_json)
    var profile = _load_profile(root)
    var candidates = _candidates_from_input(root)
    var state = _state_from_input(root)
    var now = obj_string(root, "now", "2026-01-01T00:00:00Z")
    var include_detail = obj_bool(root, "include_evaluations", False) or obj_bool(
        root, "detail", False
    )
    var reg = _registry_from_input(root)
    var result = run_round(
        profile, candidates, state, now, reg, include_evaluations=include_detail
    )
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
    var out = (
        "{\"decision\":"
        + result.decision.to_json()
        + ",\"state\":"
        + result.state.to_json()
        + ",\"events\":"
        + events
        + ",\"gates\":"
        + gates
    )
    if include_detail:
        out += ",\"evaluations\":" + result.evaluations_json
    out += "}"
    return out


def arbitration_step(input_json: String) raises -> String:
    """Historical alias for `fusion_step` (Fala / older hosts). Prefer fusion_step."""
    return fusion_step(input_json)


def run_stdio_line(line: String) raises -> String:
    """One-line process step used by Fala subprocess effectors."""
    var root = parse_json(line)
    if root.is_object() and "input" in root.object():
        var inp = root.object()["input"].copy()
        if inp.is_object() and "values" in inp.object():
            var values = inp.object()["values"].copy()
            if root.is_object() and "config" in root.object() and root.object()["config"].is_object():
                return fusion_step(to_string(values))
            return fusion_step(to_string(values))
    return fusion_step(line)
