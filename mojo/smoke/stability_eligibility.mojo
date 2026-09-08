"""An unavailable or absent previous candidate cannot win via hysteresis."""
from std.collections import List
from splot.models import Candidate, SplotState
from splot.pipeline import run_round
from splot.profile import load_profile_toml


def main() raises:
    var profile = load_profile_toml("examples/fixtures/player_camera_director.profile.toml")
    var first = List[Candidate]()
    first.append(Candidate("previous", "{\"visibility\":1.0,\"face_angle\":1.0,\"sharpness\":1.0,\"occlusion\":0.0,\"available\":true}"))
    var initial = run_round(profile, first, SplotState())
    for missing in range(2):
        var next_candidates = List[Candidate]()
        if missing == 0:
            next_candidates.append(Candidate("previous", "{\"visibility\":1.0,\"face_angle\":1.0,\"sharpness\":1.0,\"occlusion\":0.0,\"available\":false}"))
        next_candidates.append(Candidate("replacement", "{\"visibility\":0.7,\"face_angle\":0.5,\"sharpness\":0.5,\"occlusion\":0.0,\"available\":true}"))
        var result = run_round(profile, next_candidates, initial.state)
        if result.decision.selected_candidate_id != "replacement":
            raise Error("hysteresis retained an unavailable or absent candidate")
    print("splot stability eligibility smoke ok")
