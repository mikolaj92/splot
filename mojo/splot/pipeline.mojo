"""Evaluate candidates, decide, apply stability (select_one core)."""

from std.collections import List, Dict
from emberjson import Value
from splot.builtins import candidate_available, candidate_value, state_is_current
from splot.json_util import clamp01, nested, obj_float, obj_string, parse_json, quote
from splot.models import (
    Candidate,
    CandidateEvaluation,
    ConstraintResult,
    Decision,
    RoundResult,
    Signal,
    SplotState,
)
from splot.normalize import normalize_signal, to_float_json


def _new_id(prefix: String) -> String:
    # Deterministic-enough for smoke (no UUID in core): use content length + prefix.
    return prefix + "_mojo"


def build_signals(
    profile: Value,
    candidate: Candidate,
    state: SplotState,
) raises -> List[Signal]:
    var out = List[Signal]()
    if not profile.is_object() or "signals" not in profile.object():
        return out^
    var signals = profile.object()["signals"].copy()
    if not signals.is_array():
        return out^
    for item in signals.array():
        if not item.is_object():
            continue
        var cfg = item.copy()
        var sid = obj_string(cfg, "id")
        var provider = obj_string(cfg, "provider", "candidate.value")
        var prefer = obj_string(cfg, "prefer", "higher")
        var weight = obj_float(cfg, "weight", 1.0)
        var field = obj_string(cfg, "field", sid)
        var raw: Float64 = 0.0
        var value_json = "0"
        if provider == "candidate.value":
            raw = candidate_value(candidate, field)
            value_json = String(raw)
        elif provider == "state.is_current":
            raw = state_is_current(candidate, state)
            value_json = String(raw)
        else:
            # Unknown provider: zero signal
            raw = 0.0
            value_json = "0"
        var normalized = normalize_signal(raw, prefer)
        out.append(Signal(sid, value_json, normalized, weight, prefer, 1.0))
    return out^


def apply_constraints(
    profile: Value,
    candidate: Candidate,
    signals: List[Signal],
) raises -> List[ConstraintResult]:
    var out = List[ConstraintResult]()
    var by_id = Dict[String, Signal]()
    for s in signals:
        by_id[s.id] = s.copy()

    # Signal min/max from signal configs
    if profile.is_object() and "signals" in profile.object() and profile.object()["signals"].is_array():
        for item in profile.object()["signals"].array():
            if not item.is_object():
                continue
            var cfg = item.copy()
            var sid = obj_string(cfg, "id")
            if sid not in by_id:
                continue
            var signal = by_id[sid].copy()
            var severity = obj_string(cfg, "severity", "block")
            var penalty = obj_float(cfg, "penalty", 0.0)
            if severity != "penalize":
                penalty = 0.0
            if "min" in cfg.object():
                var mn = obj_float(cfg, "min", 0.0)
                if signal.normalized < mn:
                    out.append(
                        ConstraintResult(
                            sid + ".min",
                            severity,
                            False,
                            "signal " + sid + " below min",
                            penalty if severity == "penalize" else 0.0,
                        )
                    )
            if "max" in cfg.object():
                var mx = obj_float(cfg, "max", 1.0)
                if signal.normalized > mx:
                    out.append(
                        ConstraintResult(
                            sid + ".max",
                            severity,
                            False,
                            "signal " + sid + " above max",
                            penalty if severity == "penalize" else 0.0,
                        )
                    )

    if profile.is_object() and "constraints" in profile.object() and profile.object()["constraints"].is_array():
        for item in profile.object()["constraints"].array():
            if not item.is_object():
                continue
            var cfg = item.copy()
            var cid = obj_string(cfg, "id")
            var severity = obj_string(cfg, "severity", "block")
            var provider = obj_string(cfg, "provider", "")
            var passed = True
            var reason = obj_string(cfg, "reason", cid)
            var penalty = 0.0
            if provider == "candidate.available":
                passed = candidate_available(candidate)
                if not passed:
                    reason = obj_string(cfg, "reason", "source is not live")
            elif "signal" in cfg.object():
                var sig_id = obj_string(cfg, "signal")
                if sig_id in by_id:
                    var sig = by_id[sig_id].copy()
                    var use_norm = obj_string(cfg, "use", "") == "normalized"
                    var left = sig.normalized if use_norm else to_float_json(sig.value_json)
                    var right = obj_float(cfg, "value", obj_float(cfg, "threshold", 0.0))
                    var op = obj_string(cfg, "operator", "gte")
                    passed = _compare(left, op, right)
                    reason = sig_id + " " + op + " " + String(right)
            if not passed and severity == "penalize":
                penalty = obj_float(cfg, "penalty", 0.0)
            out.append(ConstraintResult(cid, severity, passed, reason, penalty))
    return out^


def _compare(left: Float64, op: String, right: Float64) -> Bool:
    if op == "gte" or op == ">=":
        return left >= right
    if op == "gt" or op == ">":
        return left > right
    if op == "lte" or op == "<=":
        return left <= right
    if op == "lt" or op == "<":
        return left < right
    if op == "eq" or op == "==":
        return left == right
    if op == "neq" or op == "!=":
        return left != right
    return False


def evaluate_candidate(
    profile: Value,
    candidate: Candidate,
    state: SplotState,
) raises -> CandidateEvaluation:
    var signals = build_signals(profile, candidate, state)
    var constraints = apply_constraints(profile, candidate, signals)
    var total_weight: Float64 = 0.0
    var raw: Float64 = 0.0
    for s in signals:
        total_weight += s.weight
        raw += s.contribution
    if total_weight > 0.0:
        raw = raw / total_weight
    else:
        raw = 0.0
    var penalty: Float64 = 0.0
    var eval = CandidateEvaluation(candidate.id)
    eval.signals = signals^
    eval.constraints = constraints.copy()
    for c in constraints:
        if c.passed:
            continue
        if c.severity == "block":
            eval.rejected_reasons.append(c.reason)
        elif c.severity == "warn" or c.severity == "penalize":
            eval.warnings.append(c.reason)
            if c.severity == "penalize":
                penalty += c.penalty
        elif c.severity == "human_decision":
            eval.human_decisions.append(c.reason)
    eval.eligible = len(eval.rejected_reasons) == 0
    eval.raw_score = raw
    eval.score = clamp01(raw - penalty)
    return eval^


def evaluate_all(
    profile: Value,
    candidates: List[Candidate],
    state: SplotState,
) raises -> List[CandidateEvaluation]:
    var out = List[CandidateEvaluation]()
    for c in candidates:
        out.append(evaluate_candidate(profile, c, state))
    return out^


def decide_from_evaluations(
    profile: Value,
    evaluations: List[CandidateEvaluation],
    state: SplotState,
) raises -> Decision:
    var objective = nested(profile, "objective")
    var objective_id = obj_string(objective, "id", obj_string(profile, "id", "objective"))
    var decision_cfg = nested(profile, "decision")
    var policy = obj_string(decision_cfg, "policy", "constrained_weighted_score")
    var close_margin = obj_float(decision_cfg, "close_margin", 0.05)
    var prev = parse_json(state.previous_decision_json)
    var previous_id = obj_string(prev, "selected_candidate_id", "")

    var eligible = List[CandidateEvaluation]()
    for e in evaluations:
        if policy == "weighted_score":
            eligible.append(e.copy())
        elif e.eligible:
            eligible.append(e.copy())

    if len(evaluations) == 0:
        return Decision(
            _new_id("decision"),
            "no_candidate",
            objective_id,
            "",
            0.0,
            1.0,
            "when_no_candidate",
            "no candidates",
        )
    if len(eligible) == 0:
        var behavior = obj_string(nested(profile, "uncertainty"), "when_constraints_block_all", "fallback")
        if behavior == "keep_previous" and previous_id != "":
            return Decision(
                _new_id("decision"),
                "selected",
                objective_id,
                previous_id,
                obj_float(prev, "confidence", 0.0),
                1.0 - obj_float(prev, "confidence", 0.0),
                "keep_previous",
                "all candidates blocked",
            )
        return Decision(
            _new_id("decision"),
            "fallback",
            objective_id,
            "",
            0.0,
            1.0,
            "when_constraints_block_all",
            "all candidates blocked",
        )

    # rank by score
    var ranked = eligible.copy()
    # simple bubble sort
    var n = len(ranked)
    for i in range(n):
        for j in range(0, n - i - 1):
            if ranked[j].score < ranked[j + 1].score:
                var tmp = ranked[j].copy()
                ranked[j] = ranked[j + 1].copy()
                ranked[j + 1] = tmp^

    var best = ranked[0].copy()
    var margin: Float64 = 1.0
    if len(ranked) > 1:
        margin = best.score - ranked[1].score

    if len(best.human_decisions) > 0:
        return Decision(
            _new_id("decision"),
            "needs_human_decision",
            objective_id,
            best.candidate_id,
            best.score,
            1.0 - best.score,
            "candidate_requires_human_decision",
            "best candidate requires human input",
        )

    var tie = obj_string(decision_cfg, "tie_breaker", "")
    if tie == "keep_current" and previous_id != "" and best.candidate_id != previous_id:
        var prev_score: Float64 = 0.0
        for e in evaluations:
            if e.candidate_id == previous_id and e.eligible:
                prev_score = e.score
                if best.score - prev_score <= close_margin:
                    return Decision(
                        _new_id("decision"),
                        "selected",
                        objective_id,
                        previous_id,
                        prev_score,
                        1.0 - prev_score,
                        "tie_breaker_keep_current",
                        "kept previous within close margin",
                    )

    var when_close = obj_string(nested(profile, "uncertainty"), "when_close", "select_best_anyway")
    if when_close == "keep_previous" and previous_id != "" and margin <= close_margin and len(ranked) > 1:
        var prev_score2: Float64 = 0.0
        for e in evaluations:
            if e.candidate_id == previous_id:
                prev_score2 = e.score
        return Decision(
            _new_id("decision"),
            "selected",
            objective_id,
            previous_id,
            prev_score2,
            1.0 - prev_score2,
            "close_scores_keep_previous",
            "top candidates are close",
        )

    return Decision(
        _new_id("decision"),
        "selected",
        objective_id,
        best.candidate_id,
        best.score,
        clamp01(1.0 - best.score),
        policy + "_selected_highest_score",
        "selected " + best.candidate_id + " with score " + String(best.score),
    )


def apply_stability(
    profile: Value,
    evaluations: List[CandidateEvaluation],
    state: SplotState,
    decision: Decision,
) raises -> Decision:
    var stab = nested(profile, "stability")
    var policy = obj_string(stab, "policy", "none")
    if policy == "none" or decision.status != "selected":
        return decision.copy()
    var prev = parse_json(state.previous_decision_json)
    var previous_id = obj_string(prev, "selected_candidate_id", "")
    var proposed = decision.selected_candidate_id
    if previous_id == "" or proposed == previous_id:
        return decision.copy()
    var min_improvement = obj_float(stab, "min_improvement", 0.0)
    var proposed_score: Float64 = decision.confidence
    var previous_score: Float64 = obj_float(prev, "confidence", 0.0)
    for e in evaluations:
        if e.candidate_id == proposed:
            proposed_score = e.score
        if e.candidate_id == previous_id:
            previous_score = e.score
    var margin = proposed_score - previous_score
    if policy == "hysteresis" or policy == "prefer_current_when_close" or policy == "switching_cost":
        if margin < min_improvement:
            return Decision(
                decision.id,
                "selected",
                decision.objective_id,
                previous_id,
                previous_score,
                1.0 - previous_score,
                "keep_previous_hysteresis",
                "score margin below min_improvement",
            )
    return decision.copy()


def run_round(
    profile: Value,
    candidates: List[Candidate],
    state: SplotState,
    now: String = "2026-01-01T00:00:00Z",
) raises -> RoundResult:
    var evaluations = evaluate_all(profile, candidates, state)
    var decision = decide_from_evaluations(profile, evaluations, state)
    decision = apply_stability(profile, evaluations, state, decision)

    # Update state
    var next_state = state.copy()
    next_state.previous_decision_json = decision.to_json()
    next_state.last_decision_at = now
    if decision.selected_candidate_id != obj_string(parse_json(state.previous_decision_json), "selected_candidate_id", ""):
        next_state.last_switch_at = now

    var ranks = "["
    var first = True
    # sort copy for report
    var ranked = evaluations.copy()
    var n = len(ranked)
    for i in range(n):
        for j in range(0, n - i - 1):
            if ranked[j].score < ranked[j + 1].score:
                var tmp = ranked[j].copy()
                ranked[j] = ranked[j + 1].copy()
                ranked[j + 1] = tmp^
    for e in ranked:
        if not first:
            ranks += ","
        ranks += (
            "{\"candidate_id\":"
            + quote(e.candidate_id)
            + ",\"score\":"
            + String(e.score)
            + ",\"eligible\":"
            + ("true" if e.eligible else "false")
            + "}"
        )
        first = False
    ranks += "]"

    var report = (
        "{\"schema\":\"splot.decision_report\",\"decision\":"
        + decision.to_json()
        + ",\"state\":"
        + next_state.to_json()
        + ",\"evaluations\":"
        + ranks
        + ",\"now\":"
        + quote(now)
        + "}"
    )
    return RoundResult(decision^, next_state^, report)
