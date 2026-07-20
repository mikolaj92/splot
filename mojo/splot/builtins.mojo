"""Builtin profile providers (no free-form user code)."""

from emberjson import Value
from splot.json_util import obj_string, parse_json, quote
from splot.models import Candidate, SplotState
from splot.normalize import to_float_json


def payload_field(candidate: Candidate, field: String, default_json: String = "0") raises -> String:
    var payload = parse_json(candidate.payload_json)
    if field == "":
        return default_json
    if payload.is_object() and field in payload.object():
        var item = payload.object()[field].copy()
        if item.is_string():
            return item.string()
        if item.is_bool():
            return "true" if item.bool() else "false"
        if item.is_int():
            return String(item.int())
        if item.is_float():
            return String(item.float())
        if item.is_null():
            return default_json
        return default_json
    var meta = parse_json(candidate.metadata_json)
    if meta.is_object() and field in meta.object():
        var m = meta.object()[field].copy()
        if m.is_string():
            return m.string()
        if m.is_bool():
            return "true" if m.bool() else "false"
        if m.is_int():
            return String(m.int())
        if m.is_float():
            return String(m.float())
    return default_json


def candidate_value(candidate: Candidate, field: String) raises -> Float64:
    return to_float_json(payload_field(candidate, field, "0"))


def candidate_available(candidate: Candidate) raises -> Bool:
    var raw = payload_field(candidate, "available", "true")
    return raw == "true" or raw == "1"


def state_is_current(candidate: Candidate, state: SplotState) raises -> Float64:
    if state.previous_decision_json == "" or state.previous_decision_json == "{}":
        return 0.0
    var prev = parse_json(state.previous_decision_json)
    var prev_id = obj_string(prev, "selected_candidate_id", "")
    if prev_id != "" and prev_id == candidate.id:
        return 1.0
    return 0.0
