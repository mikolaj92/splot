"""Python binding smoke: must match Mojo fusion_step / fixture semantics."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REQ = ROOT / "examples" / "fixtures" / "player_camera_director.request.json"
FIXTURE_PROFILE = ROOT / "examples" / "fixtures" / "player_camera_director.profile.toml"


@pytest.fixture(autouse=True)
def _chdir_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("SPLOT_HOME", str(ROOT))


def test_fuse_fixture_selects_cam_a() -> None:
    import splot

    request = json.loads(FIXTURE_REQ.read_text(encoding="utf-8"))
    decision, state = splot.fuse(
        profile=request["profile"],
        candidates=request["candidates"],
        now=request.get("now"),
    )
    assert decision["status"] == "selected"
    assert decision["selected_candidate_id"] == "cam_a"
    assert "previous_decision" in state or "previous_decision" in json.dumps(state)


def test_fuse_json_matches_subprocess_shape() -> None:
    import splot

    envelope = splot.fuse_json(FIXTURE_REQ.read_text(encoding="utf-8"))
    assert "decision" in envelope and "state" in envelope and "events" in envelope
    assert envelope["decision"]["selected_candidate_id"] == "cam_a"


def test_load_profile_rejects_yaml() -> None:
    import splot

    fake = ROOT / "examples" / "fixtures" / "_tmp.yaml"
    try:
        fake.write_text("x: 1\n", encoding="utf-8")
        with pytest.raises(ValueError, match="YAML"):
            splot.load_profile(fake)
    finally:
        fake.unlink(missing_ok=True)


def test_load_profile_ok() -> None:
    import splot

    path = splot.load_profile(FIXTURE_PROFILE)
    assert Path(path).is_file()


def test_compose_one_matches_mojo_smoke() -> None:
    import splot

    decision, _ = splot.fuse(
        profile=ROOT / "examples/fixtures/compose_streams.profile.toml",
        candidates=[
            {"id": "rag", "payload": {"relevance": 0.9, "coverage": 0.8, "available": True}},
            {"id": "docs", "payload": {"relevance": 0.7, "coverage": 0.85, "available": True}},
            {"id": "image", "payload": {"relevance": 0.2, "coverage": 0.2, "available": True}},
            {"id": "dead", "payload": {"relevance": 0.99, "coverage": 0.99, "available": False}},
        ],
        now="2026-01-01T12:00:00Z",
    )
    assert decision["status"] == "composed"
    assert decision["selected_candidate_id"] == "rag"
    composed = decision["composed"]
    assert [part["id"] for part in composed["parts"]] == ["rag", "docs"]


def test_host_reader_matches_mojo_smoke() -> None:
    import splot

    decision, _ = splot.fuse(
        profile=ROOT / "examples/fixtures/host_focus.profile.toml",
        candidates=[
            {"id": "stream_a", "payload": {"player": 0.9, "ball": 0.9, "available": True}},
            {"id": "stream_b", "payload": {"player": 0.99, "ball": 0.1, "available": True}},
        ],
        readers={"signals": {"host.focus": "product:player,ball"}},
        now="2026-01-01T00:00:01Z",
    )
    assert decision["status"] == "selected"
    assert decision["selected_candidate_id"] == "stream_a"
    assert decision["confidence"] > 0.5


def test_toml_unterminated_string_fails_closed(tmp_path: Path) -> None:
    import splot

    profile = tmp_path / "broken.profile.toml"
    profile.write_text('mode = "select_one', encoding="utf-8")
    with pytest.raises(Exception, match=r"unterminated .*string"):
        splot.fuse(
            profile=profile,
            candidates=[{"id": "candidate", "payload": {"available": True}}],
        )
