from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .models import SplotState
from .profile import ProfileError, load_profile, validate_profile
from .registry import builtin_registry
from .runtime import run_round
from .state import load_state_file, write_state_file


EXAMPLE_ROOT = Path(__file__).resolve().parents[2] / "examples"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="splot")
    subcommands = parser.add_subparsers(dest="command", required=True)

    profile_parser = subcommands.add_parser("profile")
    profile_subcommands = profile_parser.add_subparsers(dest="profile_command", required=True)
    validate_parser = profile_subcommands.add_parser("validate")
    validate_parser.add_argument("path")

    decide_parser = subcommands.add_parser("decide")
    decide_parser.add_argument("--profile", required=True)
    decide_parser.add_argument("--input", required=True)
    decide_parser.add_argument("--state")
    decide_parser.add_argument("--out")

    state_parser = subcommands.add_parser("state")
    state_subcommands = state_parser.add_subparsers(dest="state_command", required=True)
    state_init = state_subcommands.add_parser("init")
    state_init.add_argument("--out", required=True)

    examples_parser = subcommands.add_parser("examples")
    examples_subcommands = examples_parser.add_subparsers(dest="examples_command", required=True)
    run_example = examples_subcommands.add_parser("run")
    run_example.add_argument("name", choices=["camera", "contract-compose", "route", "uncertainty"])
    run_example.add_argument("--out")

    args = parser.parse_args(argv)
    try:
        if args.command == "profile":
            return _profile(args)
        if args.command == "decide":
            return _decide(args)
        if args.command == "state":
            return _state(args)
        if args.command == "examples":
            return _example(args)
    except (ProfileError, KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def _profile(args: argparse.Namespace) -> int:
    profile = load_profile(args.path)
    validate_profile(profile, registry=builtin_registry())
    print(f"valid profile: {profile.id} ({profile.mode})")
    return 0


def _decide(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    input_state = payload.get("state")
    file_state = load_state_file(args.state) if args.state else SplotState()
    state = input_state or file_state.to_dict()
    result = run_round(
        profile=args.profile,
        observations=payload.get("observations") or [],
        candidates=payload.get("candidates") or [],
        previous_state=state,
        registry=builtin_registry(),
        now=payload.get("now"),
        feedback=payload.get("feedback"),
    )
    report = result.report.to_dict()
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.state:
        write_state_file(args.state, result.state)
    _print_summary(result.decision.to_dict())
    return 0


def _state(args: argparse.Namespace) -> int:
    write_state_file(args.out, SplotState())
    print(f"wrote state: {args.out}")
    return 0


def _example(args: argparse.Namespace) -> int:
    mapping = {
        "camera": ("player-camera-director", "camera_round_1.json"),
        "contract-compose": ("contract-composer", "contract_sections.json"),
        "route": ("route-selector", "route_item.json"),
        "uncertainty": ("multi-wave-uncertainty", "uncertainty_round.json"),
    }
    profile_name, input_name = mapping[args.name]
    fake_args = argparse.Namespace(
        profile=str(EXAMPLE_ROOT / "profiles" / profile_name),
        input=str(EXAMPLE_ROOT / "inputs" / input_name),
        state=None,
        out=args.out,
    )
    return _decide(fake_args)


def _print_summary(decision: dict[str, Any]) -> None:
    selected = decision.get("selected_candidate_id") or ",".join(decision.get("selected_candidate_ids") or [])
    suffix = f" selected={selected}" if selected else ""
    print(f"{decision.get('status')} confidence={decision.get('confidence'):.3f}{suffix}")
    if decision.get("policy_reason"):
        print(decision["policy_reason"])


if __name__ == "__main__":
    raise SystemExit(main())
