import unittest

from splot import run_round


CANDIDATES = [{"id": "a"}]


def _profile(**signal_extra):
    return {
        "version": 1,
        "id": "fusion",
        "mode": "select_one",
        "objective": {"id": "objective"},
        "signals": [
            {
                "id": "quality",
                "provider": "observation.value",
                "field": "quality",
                "weight": 1,
                **signal_extra,
            }
        ],
        "decision": {"policy": "constrained_weighted_score"},
    }


def _observations(*pairs):
    return [
        {"id": f"obs_{index}", "wave_id": wave_id, "values": {"quality": value}}
        for index, (wave_id, value) in enumerate(pairs)
    ]


def _signal(result):
    return result.report.evaluations[0]["signals"][0]


class SignalFusionTests(unittest.TestCase):
    def test_last_wins_without_reduce(self):
        result = run_round(
            _profile(),
            observations=_observations(("wave_a", 0.9), ("wave_b", 0.2), ("wave_a", 0.4)),
            candidates=CANDIDATES,
            now="2026-06-28T12:00:00+00:00",
        )

        signal = _signal(result)
        self.assertEqual(signal["value"], 0.4)
        self.assertEqual(signal["confidence"], 1.0)
        self.assertIsNone(signal["reason"])
        self.assertEqual(signal["sources"], [])

    def test_reduce_mean_fuses_and_flags_disagreement(self):
        result = run_round(
            _profile(reduce="mean"),
            observations=_observations(("wave_a", 0.9), ("wave_b", 0.2)),
            candidates=CANDIDATES,
            now="2026-06-28T12:00:00+00:00",
        )

        signal = _signal(result)
        self.assertEqual(signal["value"], 0.55)
        self.assertAlmostEqual(signal["confidence"], 0.1 / 0.7, places=5)
        self.assertEqual(signal["reason"], "sources disagree: wave_a=0.9, wave_b=0.2")
        self.assertEqual(
            signal["sources"],
            [
                {"observation_id": "obs_0", "wave_id": "wave_a"},
                {"observation_id": "obs_1", "wave_id": "wave_b"},
            ],
        )

    def test_reduce_uses_newest_value_per_wave(self):
        result = run_round(
            _profile(reduce="mean"),
            observations=_observations(("wave_a", 0.1), ("wave_a", 0.9), ("wave_b", 0.9)),
            candidates=CANDIDATES,
            now="2026-06-28T12:00:00+00:00",
        )

        signal = _signal(result)
        self.assertEqual(signal["value"], 0.9)
        self.assertEqual(signal["confidence"], 1.0)
        self.assertIsNone(signal["reason"])

    def test_agreement_within_tolerance_keeps_confidence(self):
        result = run_round(
            _profile(reduce="mean"),
            observations=_observations(("wave_a", 0.5), ("wave_b", 0.55)),
            candidates=CANDIDATES,
            now="2026-06-28T12:00:00+00:00",
        )

        signal = _signal(result)
        self.assertEqual(signal["value"], 0.525)
        self.assertEqual(signal["confidence"], 1.0)
        self.assertIsNone(signal["reason"])

    def test_reduce_modes(self):
        observations = _observations(("wave_a", 0.2), ("wave_b", 0.9), ("wave_c", 0.5))
        expected = {"min": 0.2, "max": 0.9, "median": 0.5, "last": 0.5}
        for mode, value in expected.items():
            with self.subTest(reduce=mode):
                result = run_round(
                    _profile(reduce=mode, tolerance=1.0),
                    observations=observations,
                    candidates=CANDIDATES,
                    now="2026-06-28T12:00:00+00:00",
                )
                self.assertEqual(_signal(result)["value"], value)

    def test_observation_confidence_bounds_fused_confidence(self):
        observations = _observations(("wave_a", 0.5), ("wave_b", 0.5))
        observations[0]["confidence"] = 0.6
        result = run_round(
            _profile(reduce="mean"),
            observations=observations,
            candidates=CANDIDATES,
            now="2026-06-28T12:00:00+00:00",
        )

        self.assertEqual(_signal(result)["confidence"], 0.6)

    def test_fused_attribution_reaches_evidence(self):
        result = run_round(
            _profile(reduce="mean"),
            observations=_observations(("wave_a", 0.9), ("wave_b", 0.2)),
            candidates=CANDIDATES,
            now="2026-06-28T12:00:00+00:00",
        )

        entries = [
            item
            for item in result.report.evidence
            if item.get("metadata", {}).get("signal_id") == "quality"
        ]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertIsNone(entry["observation_id"])
        self.assertEqual(
            entry["metadata"]["sources"],
            [
                {"observation_id": "obs_0", "wave_id": "wave_a"},
                {"observation_id": "obs_1", "wave_id": "wave_b"},
            ],
        )
        self.assertTrue(entry["reasons"][0].startswith("sources disagree"))

    def test_single_source_attribution_sets_observation_id(self):
        result = run_round(
            _profile(reduce="last"),
            observations=_observations(("wave_a", 0.9)),
            candidates=CANDIDATES,
            now="2026-06-28T12:00:00+00:00",
        )

        entries = [
            item
            for item in result.report.evidence
            if item.get("metadata", {}).get("signal_id") == "quality"
        ]
        self.assertEqual(entries[0]["observation_id"], "obs_0")


if __name__ == "__main__":
    unittest.main()
