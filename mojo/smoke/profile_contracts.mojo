"""Smoke: every illustrative profile is executable and invalid contracts fail closed."""

from std.collections import List
from splot.models import Candidate, SplotState
from splot.pipeline import run_round
from splot.profile import load_profile_text, load_profile_toml


def _check(ok: Bool, msg: String) raises:
    if not ok:
        raise Error("splot profile contract smoke: " + msg)


def _candidates() -> List[Candidate]:
    var candidates = List[Candidate]()
    candidates.append(Candidate("a", "{\"route_fit\":0.9,\"route_cost\":0.2,\"goal_fit\":0.9,\"completeness\":0.9,\"legal_risk\":0.1,\"style_consistency\":0.8,\"support\":0.9,\"source_freshness\":0.9,\"visibility\":0.9,\"face_angle\":0.8,\"sharpness\":0.8,\"occlusion\":0.1,\"available\":true}"))
    candidates.append(Candidate("b", "{\"route_fit\":0.5,\"route_cost\":0.8,\"goal_fit\":0.6,\"completeness\":0.6,\"legal_risk\":0.5,\"style_consistency\":0.6,\"support\":0.5,\"source_freshness\":0.8,\"visibility\":0.7,\"face_angle\":0.6,\"sharpness\":0.6,\"occlusion\":0.3,\"available\":true}"))
    return candidates^


def main() raises:
    var paths = List[String]()
    paths.append("examples/profiles/route-selector/profile.toml")
    paths.append("examples/profiles/contract-composer/profile.toml")
    paths.append("examples/profiles/multi-wave-uncertainty/profile.toml")
    paths.append("examples/profiles/player-camera-director/profile.toml")
    for path in paths:
        var result = run_round(load_profile_toml(path), _candidates(), SplotState())
        _check(result.decision.status == "selected" or result.decision.status == "composed", path)

    try:
        _ = run_round(load_profile_text("mode = \"route\"\n[decision]\npolicy = \"constrained_weighted_score\""), _candidates(), SplotState())
        raise Error("bad mode was accepted")
    except err:
        _check(String(err).find("unsupported decision mode") >= 0, "bad mode error")

    try:
        _ = run_round(load_profile_text("mode = \"select_one\"\n[decision]\npolicy = \"route_by_best_match\""), _candidates(), SplotState())
        raise Error("bad policy was accepted")
    except err:
        _check(String(err).find("unsupported decision policy") >= 0, "bad policy error")

    print("splot profile contract smoke ok")
