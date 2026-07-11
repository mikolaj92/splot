from __future__ import annotations

import html
import json
from typing import Any

from .redaction import redact_value


def render_html_report(report: dict[str, Any], *, redact: bool = False, fields: list[str] | None = None) -> str:
    data = redact_value(report, fields) if redact else report
    decision = data.get("decision") or {}
    uncertainty = data.get("uncertainty") or {}
    rows = "\n".join(_evaluation_row(item) for item in data.get("evaluations") or [])
    human = "".join(f"<li>{_e(item)}</li>" for item in data.get("human_decisions") or [])
    warnings = "".join(f"<li>{_e(item)}</li>" for item in data.get("warnings") or [])
    rejected = "".join(
        f"<li>{_e(item.get('candidate_id'))}: {_e(', '.join(item.get('reasons') or []))}</li>"
        for item in decision.get("rejected_candidates") or []
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Splot decision report {_e(data.get('round_id'))}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ddd; padding: .4rem; text-align: left; vertical-align: top; }}
    th {{ background: #f5f5f5; }}
    code, pre {{ background: #f7f7f7; padding: .15rem .25rem; }}
    pre {{ overflow: auto; padding: 1rem; }}
    .status {{ font-weight: 700; }}
  </style>
</head>
<body>
  <h1>Splot Decision Report</h1>
  <section>
    <h2>Summary</h2>
    <p><span class="status">{_e(decision.get('status'))}</span> confidence={_e(decision.get('confidence'))}</p>
    <p>uncertainty={_e(uncertainty.get('value'))} dominant={_e(uncertainty.get('dominant_component'))}</p>
    <p>profile={_e(data.get('profile_id'))} round={_e(data.get('round_id'))}</p>
    <p>created_at={_e(data.get('created_at'))}</p>
  </section>
  <section><h2>Previous Decision</h2><pre>{_json(data.get('previous_decision'))}</pre></section>
  <section><h2>Final Decision</h2><pre>{_json(decision)}</pre></section>
  <section><h2>Candidate Scores</h2><table>
    <thead><tr><th>Candidate</th><th>Eligible</th><th>Score</th><th>Signals</th><th>Constraints</th><th>Rejected</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></section>
  <section><h2>Stability</h2><pre>{_json(data.get('stability'))}</pre></section>
  <section><h2>Uncertainty / Conflicts</h2><pre>{_json(data.get('uncertainty'))}</pre></section>
  <section><h2>Human Decisions</h2><ul>{human}</ul></section>
  <section><h2>Warnings</h2><ul>{warnings}</ul></section>
  <section><h2>Rejected Candidates</h2><ul>{rejected}</ul></section>
  <section><h2>State Updates</h2><pre>{_json(data.get('state_updates'))}</pre></section>
</body>
</html>
"""


def _evaluation_row(item: dict[str, Any]) -> str:
    signals = "<br>".join(
        f"{_e(signal.get('id'))}: {_e(signal.get('contribution'))} ({_e(signal.get('normalized'))})"
        for signal in item.get("signals") or []
    )
    constraints = "<br>".join(
        f"{_e(constraint.get('id'))}: {_e(constraint.get('severity'))} passed={_e(constraint.get('passed'))}"
        for constraint in item.get("constraints") or []
    )
    rejected = "<br>".join(_e(reason) for reason in item.get("rejected_reasons") or [])
    return (
        "<tr>"
        f"<td>{_e(item.get('candidate_id'))}</td>"
        f"<td>{_e(item.get('eligible'))}</td>"
        f"<td>{_e(item.get('score'))}</td>"
        f"<td>{signals}</td>"
        f"<td>{constraints}</td>"
        f"<td>{rejected}</td>"
        "</tr>"
    )


def _json(value: Any) -> str:
    return html.escape(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value))
