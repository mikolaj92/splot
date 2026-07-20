"""Smoke: host-registered payload readers change commitment (shipped registry path)."""

from std.collections import List
from splot.models import Candidate, SplotState
from splot.pipeline import run_round
from splot.profile import load_profile_toml
from splot.registry import ReaderRegistry


def _check(ok: Bool, msg: String) raises:
    if not ok:
        raise Error("splot host readers smoke: " + msg)


def main() raises:
    var profile = load_profile_toml("examples/fixtures/host_focus.profile.toml")
    # Payloads only make sense under product(player,ball); single fields alone
    # would rank differently.
    var candidates = List[Candidate]()
    candidates.append(
        Candidate("stream_a", "{\"player\":0.9,\"ball\":0.9,\"available\":true}")
    )
    candidates.append(
        Candidate("stream_b", "{\"player\":0.99,\"ball\":0.1,\"available\":true}")
    )

    # Without registration: host.focus → 0 for both → first by stable order / score tie.
    var bare = run_round(profile, candidates, SplotState(), "2026-01-01T00:00:00Z")
    _check(bare.decision.status == "selected", "bare selected")
    # Both scores ~0; winner is whichever ranks first at equal score (stream_a).
    var bare_winner = bare.decision.selected_candidate_id

    # With host recipe: product player*ball → A=0.81, B=0.099 → A wins for focus.
    var reg = ReaderRegistry.with_builtins()
    reg.register_signal_reader("host.focus", "product:player,ball")
    var fused = run_round(
        profile, candidates, SplotState(), "2026-01-01T00:00:01Z", reg
    )
    _check(fused.decision.status == "selected", "registered selected")
    _check(
        fused.decision.selected_candidate_id == "stream_a",
        "product reader selects stream_a (0.81 > 0.099)",
    )
    _check(fused.decision.confidence > 0.5, "confidence reflects product score")

    # Wrong/missing registration must not produce the product-based winner
    # when payloads are inverted for a value reader on a single misleading field.
    var reg_wrong = ReaderRegistry.with_builtins()
    reg_wrong.register_signal_reader("host.focus", "value:player")
    var wrong = run_round(
        profile, candidates, SplotState(), "2026-01-01T00:00:02Z", reg_wrong
    )
    _check(
        wrong.decision.selected_candidate_id == "stream_b",
        "value:player alone prefers stream_b (0.99)",
    )
    _check(
        wrong.decision.selected_candidate_id != fused.decision.selected_candidate_id
        or wrong.decision.confidence != fused.decision.confidence,
        "wrong recipe differs from product commitment",
    )

    # Builtins still work on camera fixture path.
    var cam_profile = load_profile_toml(
        "examples/fixtures/player_camera_director.profile.toml"
    )
    var cams = List[Candidate]()
    cams.append(
        Candidate(
            "cam_a",
            "{\"visibility\":0.95,\"face_angle\":0.8,\"sharpness\":0.7,\"occlusion\":0.1,\"available\":true}",
        )
    )
    cams.append(
        Candidate(
            "cam_b",
            "{\"visibility\":0.70,\"face_angle\":0.5,\"sharpness\":0.6,\"occlusion\":0.3,\"available\":true}",
        )
    )
    var cam = run_round(cam_profile, cams, SplotState())
    _check(cam.decision.selected_candidate_id == "cam_a", "builtins still pick cam_a")

    _check(bare_winner == "stream_a" or bare_winner == "stream_b", "bare had a winner")
    print("splot host readers smoke ok")
