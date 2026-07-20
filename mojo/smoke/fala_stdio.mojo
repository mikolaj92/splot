"""Fala adapter boundary smoke (JSON step)."""

from splot.adapters_fala import arbitration_step


def _check(ok: Bool, msg: String) raises:
    if not ok:
        raise Error("splot fala stdio smoke: " + msg)


def main() raises:
    var payload = (
        "{"
        + "\"profile\":\"examples/fixtures/player_camera_director.profile.toml\","
        + "\"candidates\":["
        + "{\"id\":\"a\",\"payload\":{\"visibility\":0.9,\"face_angle\":0.8,\"sharpness\":0.7,\"occlusion\":0.1,\"available\":true}},"
        + "{\"id\":\"b\",\"payload\":{\"visibility\":0.5,\"face_angle\":0.4,\"sharpness\":0.4,\"occlusion\":0.5,\"available\":true}}"
        + "],"
        + "\"now\":\"2026-01-01T12:00:00Z\""
        + "}"
    )
    var out = arbitration_step(payload)
    _check(out.find("\"status\":\"selected\"") >= 0, "decision selected")
    _check(out.find("splot.decision_committed") >= 0, "event emitted")
    _check(out.find("splot.decision_report") >= 0, "artifact descriptor")
    _check(out.find("\"selected_candidate_id\":\"a\"") >= 0, "winner a")
    print("splot fala stdio smoke ok")
