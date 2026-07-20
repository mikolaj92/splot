"""Smoke: compose_one multi-stream commitment + evaluations envelope detail."""

from std.collections import List
from splot.adapters_fala import fusion_step
from splot.models import Candidate, SplotState
from splot.pipeline import run_round
from splot.profile import load_profile_toml


def _check(ok: Bool, msg: String) raises:
    if not ok:
        raise Error("splot compose envelope smoke: " + msg)


def main() raises:
    var profile = load_profile_toml("examples/fixtures/compose_streams.profile.toml")
    var candidates = List[Candidate]()
    candidates.append(
        Candidate("rag", "{\"relevance\":0.9,\"coverage\":0.8,\"available\":true}")
    )
    candidates.append(
        Candidate("docs", "{\"relevance\":0.7,\"coverage\":0.85,\"available\":true}")
    )
    candidates.append(
        Candidate("image", "{\"relevance\":0.2,\"coverage\":0.2,\"available\":true}")
    )
    candidates.append(
        Candidate("dead", "{\"relevance\":0.99,\"coverage\":0.99,\"available\":false}")
    )

    var result = run_round(profile, candidates, SplotState(), "2026-01-01T12:00:00Z")
    _check(result.decision.status == "composed", "status composed")
    _check(result.decision.selected_candidate_id == "rag", "primary is rag")
    _check(result.decision.composed_json.find("\"mode\":\"compose_one\"") >= 0, "compose mode")
    _check(result.decision.composed_json.find("\"id\":\"rag\"") >= 0, "rag part")
    _check(result.decision.composed_json.find("\"id\":\"docs\"") >= 0, "docs part")
    # image below min_score 0.3 after weights? relevance 0.2*0.6+0.2*0.4=0.2 < 0.3
    _check(result.decision.composed_json.find("\"id\":\"image\"") < 0, "weak image excluded")
    _check(result.decision.composed_json.find("\"id\":\"dead\"") < 0, "blocked dead excluded")
    _check(result.decision.composed_json.find("part_count") >= 0, "part_count present")

    # Envelope includes evaluations (host audit detail, not a report product).
    _check(result.report_json.find("\"evaluations\"") >= 0, "envelope has evaluations")
    _check(result.report_json.find("\"candidate_id\":\"rag\"") >= 0, "eval rag")
    _check(result.report_json.find("\"eligible\":false") >= 0, "dead ineligible in detail")
    _check(result.evaluations_json.find("\"score\"") >= 0, "evaluations_json scores")
    _check(result.report_json.find("decision_report") < 0, "no decision_report product")

    # Fala thin step remains decision+state without evaluations by default.
    var thin = fusion_step(
        "{"
        + "\"profile\":\"examples/fixtures/compose_streams.profile.toml\","
        + "\"candidates\":["
        + "{\"id\":\"rag\",\"payload\":{\"relevance\":0.9,\"coverage\":0.8,\"available\":true}},"
        + "{\"id\":\"docs\",\"payload\":{\"relevance\":0.7,\"coverage\":0.85,\"available\":true}}"
        + "],"
        + "\"now\":\"2026-01-01T12:00:00Z\""
        + "}"
    )
    _check(thin.find("\"status\":\"composed\"") >= 0, "fala composed")
    _check(thin.find("\"evaluations\"") < 0, "thin fala omits evaluations")
    _check(thin.find("\"events\"") >= 0, "events present")

    # Opt-in detail on Fala step.
    var rich = fusion_step(
        "{"
        + "\"profile\":\"examples/fixtures/compose_streams.profile.toml\","
        + "\"include_evaluations\":true,"
        + "\"candidates\":["
        + "{\"id\":\"rag\",\"payload\":{\"relevance\":0.9,\"coverage\":0.8,\"available\":true}}"
        + "]"
        + "}"
    )
    _check(rich.find("\"evaluations\"") >= 0, "detail includes evaluations")
    _check(rich.find("decision_report") < 0, "still no report product key")

    print("splot compose envelope smoke ok")
    # Dump sample envelope for verification capture
    print("ENVELOPE_BEGIN")
    print(result.report_json)
    print("ENVELOPE_END")
