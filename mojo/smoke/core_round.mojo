"""Core arbitration smoke: camera-style candidates + fixture profile."""

from std.collections import List
from splot.models import Candidate, SplotState
from splot.pipeline import run_round
from splot.profile import load_profile_toml


def _check(ok: Bool, msg: String) raises:
    if not ok:
        raise Error("splot core round smoke: " + msg)


def main() raises:
    var profile_path = "examples/fixtures/player_camera_director.profile.toml"
    var profile = load_profile_toml(profile_path)
    var candidates = List[Candidate]()
    candidates.append(
        Candidate(
            "cam_a",
            "{\"visibility\":0.95,\"face_angle\":0.8,\"sharpness\":0.7,\"occlusion\":0.1,\"available\":true}",
        )
    )
    candidates.append(
        Candidate(
            "cam_b",
            "{\"visibility\":0.70,\"face_angle\":0.5,\"sharpness\":0.6,\"occlusion\":0.3,\"available\":true}",
        )
    )
    candidates.append(
        Candidate(
            "cam_offline",
            "{\"visibility\":0.99,\"face_angle\":0.9,\"sharpness\":0.9,\"occlusion\":0.0,\"available\":false}",
        )
    )
    var result = run_round(profile, candidates, SplotState(), "2026-01-01T00:00:00Z")
    _check(result.decision.status == "selected", "status selected")
    _check(result.decision.selected_candidate_id == "cam_a", "best live camera wins")
    _check(result.report_json.find("\"status\":\"selected\"") >= 0, "result envelope")
    _check(result.state.previous_decision_json.find("cam_a") >= 0, "state updated")

    # Offline-only blocked → fallback
    var blocked = List[Candidate]()
    blocked.append(
        Candidate("only_offline", "{\"visibility\":0.99,\"available\":false}")
    )
    var fb = run_round(profile, blocked, SplotState(), "2026-01-01T00:00:01Z")
    _check(fb.decision.status == "fallback" or fb.decision.selected_candidate_id == "", "blocked all fallback")

    print("splot core round smoke ok")
