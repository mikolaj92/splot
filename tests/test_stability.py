import unittest

from splot import run_round


def profile(stability):
    return {
        "version": 1,
        "id": "stable",
        "mode": "select_one",
        "objective": {"id": "objective"},
        "signals": [{"id": "score", "provider": "candidate.value", "field": "score", "weight": 1}],
        "decision": {"policy": "constrained_weighted_score"},
        "stability": stability,
    }


def state():
    return {
        "session_id": "stable_session",
        "objective_id": "objective",
        "last_decision_at": "2026-06-28T12:00:00+00:00",
        "last_switch_at": "2026-06-28T12:00:00+00:00",
        "previous_decision": {
            "id": "previous",
            "status": "selected",
            "objective_id": "objective",
            "selected_candidate_id": "current",
            "confidence": 0.8,
        },
    }


class StabilityTests(unittest.TestCase):
    def test_hysteresis_keeps_previous_when_margin_too_small(self):
        result = run_round(
            profile({"policy": "hysteresis", "min_improvement": 0.15}),
            candidates=[
                {"id": "current", "payload": {"score": 0.8}},
                {"id": "new", "payload": {"score": 0.9}},
            ],
            previous_state=state(),
            now="2026-06-28T12:00:03+00:00",
        )

        self.assertEqual(result.decision.status, "kept_previous")
        self.assertEqual(result.decision.selected_candidate_id, "current")

    def test_hysteresis_switches_when_margin_enough(self):
        result = run_round(
            profile({"policy": "hysteresis", "min_improvement": 0.15}),
            candidates=[
                {"id": "current", "payload": {"score": 0.6}},
                {"id": "new", "payload": {"score": 0.9}},
            ],
            previous_state=state(),
            now="2026-06-28T12:00:03+00:00",
        )

        self.assertEqual(result.decision.status, "selected")
        self.assertEqual(result.decision.selected_candidate_id, "new")

    def test_cooldown_prevents_switch(self):
        result = run_round(
            profile({"policy": "cooldown", "cooldown_ms": 5000}),
            candidates=[
                {"id": "current", "payload": {"score": 0.6}},
                {"id": "new", "payload": {"score": 1.0}},
            ],
            previous_state=state(),
            now="2026-06-28T12:00:01+00:00",
        )

        self.assertEqual(result.decision.status, "kept_previous")
        self.assertEqual(result.report.stability["decision"], "keep_previous_cooldown")

    def test_debounce_requires_repeated_proposal(self):
        first = run_round(
            profile({"policy": "debounce", "rounds": 2}),
            candidates=[
                {"id": "current", "payload": {"score": 0.2}},
                {"id": "new", "payload": {"score": 1.0}},
            ],
            previous_state=state(),
            now="2026-06-28T12:00:03+00:00",
        )
        second = run_round(
            profile({"policy": "debounce", "rounds": 2}),
            candidates=[
                {"id": "current", "payload": {"score": 0.2}},
                {"id": "new", "payload": {"score": 1.0}},
            ],
            previous_state=first.state,
            now="2026-06-28T12:00:04+00:00",
        )

        self.assertEqual(first.decision.status, "kept_previous")
        self.assertEqual(second.decision.selected_candidate_id, "new")

    def test_hold_then_recheck_pending_behavior(self):
        first = run_round(
            profile({"policy": "hold_then_recheck", "hold_ms": 1000}),
            candidates=[
                {"id": "current", "payload": {"score": 0.2}},
                {"id": "new", "payload": {"score": 1.0}},
            ],
            previous_state=state(),
            now="2026-06-28T12:00:03+00:00",
        )
        second = run_round(
            profile({"policy": "hold_then_recheck", "hold_ms": 1000}),
            candidates=[
                {"id": "current", "payload": {"score": 0.2}},
                {"id": "new", "payload": {"score": 1.0}},
            ],
            previous_state=first.state,
            now="2026-06-28T12:00:05+00:00",
        )

        self.assertEqual(first.decision.status, "kept_previous")
        self.assertEqual(second.decision.selected_candidate_id, "new")

    def test_switching_cost_reduces_margin(self):
        result = run_round(
            profile({"policy": "switching_cost", "min_improvement": 0.05}),
            candidates=[
                {"id": "current", "payload": {"score": 0.7}},
                {"id": "new", "payload": {"score": 0.8}, "switching_cost": 0.08},
            ],
            previous_state=state(),
            now="2026-06-28T12:00:03+00:00",
        )

        self.assertEqual(result.decision.status, "kept_previous")


if __name__ == "__main__":
    unittest.main()
