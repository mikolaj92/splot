from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .audit import audit_report, compare_replay, compare_reports
from .context_pack import build_context_pack
from .html_report import render_html_report
from .models import SplotState
from .profile import ProfileError, diagnose_profile, load_profile, validate_profile
from .redaction import redact_value
from .registry import builtin_registry
from .runtime import run_round
from .sensitivity import explain_weights, format_weight_explanation
from .schemas import SchemaValidationError, validate_decision_report_data
from .state import load_state_file, write_state_file


EXAMPLE_ROOT = Path(__file__).resolve().parents[2] / "examples"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="splot")
    subcommands = parser.add_subparsers(dest="command", required=True)

    profile_parser = subcommands.add_parser("profile")
    profile_subcommands = profile_parser.add_subparsers(dest="profile_command", required=True)
    validate_parser = profile_subcommands.add_parser("validate")
    validate_parser.add_argument("path")
    diagnose_parser = profile_subcommands.add_parser("diagnose")
    diagnose_parser.add_argument("path")

    decide_parser = subcommands.add_parser("decide")
    decide_parser.add_argument("--profile", required=True)
    decide_parser.add_argument("--input", required=True)
    decide_parser.add_argument("--state")
    decide_parser.add_argument("--out")

    inspect_parser = subcommands.add_parser("inspect-decision")
    inspect_parser.add_argument("report")

    explain_parser = subcommands.add_parser("explain")
    explain_parser.add_argument("report")

    replay_parser = subcommands.add_parser("replay-round")
    replay_parser.add_argument("--profile", required=True)
    replay_parser.add_argument("--report", required=True)
    replay_parser.add_argument("--out")
    replay_parser.add_argument("--compare", action="store_true")

    audit_parser = subcommands.add_parser("audit-report")
    audit_parser.add_argument("report")

    compare_parser = subcommands.add_parser("compare-reports")
    compare_parser.add_argument("old")
    compare_parser.add_argument("new")

    html_parser = subcommands.add_parser("export-html")
    html_parser.add_argument("report")
    html_parser.add_argument("--out", required=True)
    html_parser.add_argument("--redact", action="store_true")
    html_parser.add_argument("--field", action="append", default=[])

    weights_parser = subcommands.add_parser("explain-weights")
    weights_parser.add_argument("report")

    sensitivity_parser = subcommands.add_parser("sensitivity")
    sensitivity_parser.add_argument("--profile", required=True)
    sensitivity_parser.add_argument("--input", required=True)

    redact_parser = subcommands.add_parser("redact-report")
    redact_parser.add_argument("report")
    redact_parser.add_argument("--out", required=True)
    redact_parser.add_argument("--field", action="append", default=[])

    pack_parser = subcommands.add_parser("context-pack")
    pack_parser.add_argument("report")
    pack_parser.add_argument("--out")
    pack_parser.add_argument("--max-bytes", type=int, default=8000)
    pack_parser.add_argument("--top-evidence", type=int, default=5)
    pack_parser.add_argument("--field", action="append", default=[])

    report_parser = subcommands.add_parser("report")
    report_subcommands = report_parser.add_subparsers(dest="report_command", required=True)
    report_validate = report_subcommands.add_parser("validate")
    report_validate.add_argument("report")

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
        if args.command == "inspect-decision":
            return _inspect(args)
        if args.command == "explain":
            return _explain(args)
        if args.command == "replay-round":
            return _replay(args)
        if args.command == "audit-report":
            return _audit(args)
        if args.command == "compare-reports":
            return _compare_reports(args)
        if args.command == "export-html":
            return _export_html(args)
        if args.command == "explain-weights":
            return _explain_weights(args)
        if args.command == "sensitivity":
            return _sensitivity(args)
        if args.command == "redact-report":
            return _redact_report(args)
        if args.command == "context-pack":
            return _context_pack(args)
        if args.command == "report":
            return _report(args)
        if args.command == "state":
            return _state(args)
        if args.command == "examples":
            return _example(args)
    except (ProfileError, SchemaValidationError, KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def _profile(args: argparse.Namespace) -> int:
    if args.profile_command == "diagnose":
        diagnostics = diagnose_profile(args.path, registry=builtin_registry())
        if not diagnostics:
            print(f"valid profile: {load_profile(args.path).id}")
            return 0
        for diagnostic in diagnostics:
            print(diagnostic.format(), file=sys.stderr)
        return 1 if any(item.severity == "error" for item in diagnostics) else 0
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


def _inspect(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    _print_summary(report["decision"])
    if report.get("human_decisions"):
        print("human_decisions:")
        for item in report["human_decisions"]:
            print(f"- {item}")
    return 0


def _explain(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    _print_summary(report["decision"])
    for reason in report.get("policy_reasons") or []:
        print(f"policy: {reason}")
    stability = report.get("stability") or {}
    if stability:
        print(f"stability: {stability.get('decision')} ({stability.get('policy')})")
    for ev in report.get("evaluations") or []:
        if ev.get("rejected_reasons"):
            print(f"rejected {ev.get('candidate_id')}: {', '.join(ev.get('rejected_reasons') or [])}")
    uncertainty = report.get("uncertainty") or {}
    if uncertainty.get("conflicts"):
        print(f"conflicts: {len(uncertainty['conflicts'])}")
    return 0


def _replay(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    result = run_round(
        profile=args.profile,
        observations=report.get("observations") or [],
        candidates=report.get("candidates") or [],
        previous_state=report.get("previous_state") or {},
        registry=builtin_registry(),
        now=report.get("created_at"),
    )
    output = result.report.to_dict()
    if args.out:
        Path(args.out).write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    _print_summary(result.decision.to_dict())
    if args.compare:
        findings = compare_replay(report, output)
        for finding in findings:
            print(finding.format(), file=sys.stderr)
        return 1 if any(finding.severity == "error" for finding in findings) else 0
    return 0


def _audit(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    findings = audit_report(report)
    if not findings:
        print("report ok")
        return 0
    for finding in findings:
        stream = sys.stderr if finding.severity == "error" else sys.stdout
        print(finding.format(), file=stream)
    return 1 if any(finding.severity == "error" for finding in findings) else 0


def _compare_reports(args: argparse.Namespace) -> int:
    old = json.loads(Path(args.old).read_text(encoding="utf-8"))
    new = json.loads(Path(args.new).read_text(encoding="utf-8"))
    findings = compare_reports(old, new)
    if not findings:
        print("reports match on decision metadata")
        return 0
    for finding in findings:
        print(finding.format())
    return 0


def _export_html(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    html = render_html_report(report, redact=args.redact, fields=args.field)
    Path(args.out).write_text(html, encoding="utf-8")
    print(f"wrote html report: {args.out}")
    return 0


def _explain_weights(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    print(format_weight_explanation(explain_weights(report)))
    return 0


def _sensitivity(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = run_round(
        profile=args.profile,
        observations=payload.get("observations") or [],
        candidates=payload.get("candidates") or [],
        previous_state=payload.get("state") or {},
        registry=builtin_registry(),
        now=payload.get("now"),
        feedback=payload.get("feedback"),
    )
    print(format_weight_explanation(explain_weights(result.report.to_dict())))
    return 0


def _context_pack(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    pack = build_context_pack(
        report,
        max_bytes=args.max_bytes,
        top_evidence=args.top_evidence,
        fields=args.field,
    )
    text = json.dumps(pack, indent=2, sort_keys=True, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote context pack: {args.out}")
    else:
        print(text)
    return 0


def _redact_report(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    redacted = redact_value(report, args.field)
    Path(args.out).write_text(json.dumps(redacted, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote redacted report: {args.out}")
    return 0


def _report(args: argparse.Namespace) -> int:
    if args.report_command == "validate":
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        validate_decision_report_data(report)
        print("valid report")
        return 0
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
