import unittest

from splot import SplotState, Candidate, Decision, DecisionReport, Observation, Wave


class ModelTests(unittest.TestCase):
    def test_models_are_json_serializable(self):
        wave = Wave(id="wave_1", reliability=0.8)
        observation = Observation(id="obs_1", wave_id="wave_1", values={"x": 1})
        candidate = Candidate(id="candidate_1", payload={"score": 0.7})
        decision = Decision(
            id="decision_1",
            status="selected",
            objective_id="objective",
            selected_candidate_id="candidate_1",
            selected_candidate_ids=["candidate_1"],
        )
        state = SplotState(previous_decision=decision.to_dict())
        report = DecisionReport(
            round_id="round_1",
            profile_id="profile",
            mode="select_one",
            objective_id="objective",
            created_at="2026-06-28T12:00:00+00:00",
            previous_decision=None,
            observations=[observation.to_dict()],
            candidates=[candidate.to_dict()],
            evidence=[],
            belief={"id": "belief_1"},
            evaluations=[],
            stability={},
            decision=decision.to_dict(),
            uncertainty={},
            policy_reasons=[],
            previous_state=SplotState().to_dict(),
            updated_state=state.to_dict(),
        )

        self.assertEqual(wave.to_dict()["id"], "wave_1")
        self.assertEqual(report.to_dict()["decision"]["status"], "selected")
        self.assertEqual(SplotState.from_dict(state.to_dict()).previous_decision["id"], "decision_1")


if __name__ == "__main__":
    unittest.main()
