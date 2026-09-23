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


def test_mojo_env_prefers_detected_pixi_sdk_over_inherited_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from splot import _build

    repo_root = tmp_path / "splot"
    pixi_root = repo_root / ".pixi" / "envs" / "default"
    mojo_bin = pixi_root / "bin" / "mojo"
    mojo_bin.parent.mkdir(parents=True)
    mojo_bin.touch()
    import_path = pixi_root / "lib" / "mojo"
    import_path.mkdir(parents=True)

    monkeypatch.setattr(_build, "repo_root", lambda: repo_root)
    monkeypatch.setenv("CONDA_PREFIX", "/opt/modular")
    monkeypatch.setenv("MODULAR_HOME", "/opt/modular")

    env = _build._mojo_env()

    assert env["CONDA_PREFIX"] == str(pixi_root)
    assert env["MODULAR_HOME"] == str(pixi_root / "share" / "max")
    assert env["MODULAR_MOJO_MAX_DRIVER_PATH"] == str(mojo_bin)
    assert env["MODULAR_MOJO_MAX_IMPORT_PATH"] == str(import_path)


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
    assert "evaluations" not in envelope


def test_fuse_include_evaluations_returns_evaluations() -> None:
    import splot

    request = json.loads(FIXTURE_REQ.read_text(encoding="utf-8"))
    decision, state, evaluations = splot.fuse(
        profile=request["profile"],
        candidates=request["candidates"],
        now=request.get("now"),
        include_evaluations=True,
    )
    assert decision["status"] == "selected"
    assert decision["selected_candidate_id"] == "cam_a"
    assert "evaluations" not in decision
    assert isinstance(state, dict)
    assert {row["candidate_id"] for row in evaluations} == {
        "cam_a",
        "cam_b",
        "cam_offline",
    }
    cam_a = next(row for row in evaluations if row["candidate_id"] == "cam_a")
    assert cam_a["eligible"] is True
    assert "score" in cam_a


def test_readme_python_binding_example() -> None:
    """Keep the documented fuse/fuse_json comparison executable."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Thin Python binding (optional)", 1)[1]
    example = section.split("```python\n", 1)[1].split("```", 1)[0]
    namespace = {}

    exec(compile(example, "README.md", "exec"), namespace)

    assert namespace["decision"]["selected_candidate_id"] == "cam_a"
    assert namespace["evaluations"]


def test_fuse_json_include_evaluations_attaches_detail() -> None:
    import splot

    request = json.loads(FIXTURE_REQ.read_text(encoding="utf-8"))
    request["include_evaluations"] = True
    envelope = splot.fuse_json(request)
    evaluations = envelope["evaluations"]
    assert {row["candidate_id"] for row in evaluations} == {
        "cam_a",
        "cam_b",
        "cam_offline",
    }
    assert envelope["decision"]["selected_candidate_id"] == "cam_a"


def test_fuse_empty_candidates_is_no_candidate() -> None:
    import splot

    decision, state = splot.fuse(profile=FIXTURE_PROFILE, candidates=[])
    assert decision["status"] == "no_candidate"
    assert not decision.get("selected_candidate_id")
    assert isinstance(state, dict)


def test_fuse_json_empty_candidates_is_no_candidate() -> None:
    import splot

    envelope = splot.fuse_json(
        {
            "profile": "examples/fixtures/player_camera_director.profile.toml",
            "candidates": [],
            "now": "2026-01-01T12:00:00Z",
        }
    )
    assert envelope["decision"]["status"] == "no_candidate"
    assert not envelope["decision"].get("selected_candidate_id")
    assert "state" in envelope


def test_fuse_empty_candidates_include_evaluations() -> None:
    import splot

    decision, state, evaluations = splot.fuse(
        profile=FIXTURE_PROFILE,
        candidates=[],
        include_evaluations=True,
    )
    assert decision["status"] == "no_candidate"
    assert isinstance(state, dict)
    assert evaluations == []


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


def _stability_candidate(
    cid: str,
    *,
    visibility: float,
    face_angle: float,
    sharpness: float,
    available: bool,
) -> dict[str, object]:
    return {
        "id": cid,
        "payload": {
            "visibility": visibility,
            "face_angle": face_angle,
            "sharpness": sharpness,
            "occlusion": 0.0,
            "available": available,
        },
    }


def test_stability_eligibility_matches_mojo_smoke() -> None:
    """Blocked or absent previous cannot win via hysteresis / when_close.

    Same cases as ``mojo/smoke/stability_eligibility.mojo`` (in ``full-smoke``),
    through the thin Python binding — not a second engine.
    """
    import splot

    _, state = splot.fuse(
        profile=FIXTURE_PROFILE,
        candidates=[
            _stability_candidate(
                "previous",
                visibility=1.0,
                face_angle=1.0,
                sharpness=1.0,
                available=True,
            )
        ],
    )

    replacement = _stability_candidate(
        "replacement",
        visibility=0.7,
        face_angle=0.5,
        sharpness=0.5,
        available=True,
    )
    blocked_previous = _stability_candidate(
        "previous",
        visibility=1.0,
        face_angle=1.0,
        sharpness=1.0,
        available=False,
    )
    for next_candidates in ([blocked_previous, replacement], [replacement]):
        decision, _ = splot.fuse(
            profile=FIXTURE_PROFILE,
            candidates=next_candidates,
            state=state,
        )
        assert decision["selected_candidate_id"] == "replacement"

    close_replacement = _stability_candidate(
        "replacement",
        visibility=0.72,
        face_angle=0.5,
        sharpness=0.5,
        available=True,
    )
    rival = _stability_candidate(
        "rival",
        visibility=0.70,
        face_angle=0.5,
        sharpness=0.5,
        available=True,
    )
    for next_candidates in (
        [blocked_previous, close_replacement, rival],
        [close_replacement, rival],
    ):
        decision, _ = splot.fuse(
            profile=FIXTURE_PROFILE,
            candidates=next_candidates,
            state=state,
        )
        assert decision["selected_candidate_id"] == "replacement"


def test_toml_unterminated_string_fails_closed(tmp_path: Path) -> None:
    import splot

    profile = tmp_path / "broken.profile.toml"
    profile.write_text('mode = "select_one', encoding="utf-8")
    with pytest.raises(Exception, match=r"unterminated .*string"):
        splot.fuse(
            profile=profile,
            candidates=[{"id": "candidate", "payload": {"available": True}}],
        )
