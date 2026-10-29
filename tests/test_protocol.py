"""Deterministic eyes-open/closed protocol tests; never touch a headset."""

import math
import unittest

from memstack.protocol import Cue, EyesExperiment


class EyesExperimentTests(unittest.TestCase):
    def test_default_schedule_and_boundaries(self):
        p = EyesExperiment()
        self.assertEqual(p.total_seconds, 60.0)
        self.assertEqual(p.condition(100.0), "NOT_STARTED")
        initial = p.start(100.0)
        self.assertEqual(initial, [Cue(100.0, "OPEN", "Open your eyes")])
        self.assertEqual(p.condition(100.0), "OPEN")
        self.assertEqual(p.condition(109.999), "OPEN")
        self.assertEqual(p.condition(110.0), "CLOSED")
        self.assertEqual(p.advance(110.0), [Cue(110.0, "CLOSED", "Close your eyes")])
        self.assertEqual(p.advance(110.0), [])
        self.assertEqual(p.condition(120.0), "OPEN")
        self.assertEqual(p.condition(160.0), "DONE")
        self.assertEqual(p.end_epoch_s, 160.0)

    def test_catch_up_returns_all_unobserved_scheduled_cues_once(self):
        p = EyesExperiment(open_seconds=2, closed_seconds=3, cycles=2)
        p.start(100.0)
        cues = p.advance(120.0)
        self.assertEqual(
            [(cue.scheduled_epoch_s, cue.condition, cue.instruction) for cue in cues],
            [(102.0, "CLOSED", "Close your eyes"),
             (105.0, "OPEN", "Open your eyes"),
             (107.0, "CLOSED", "Close your eyes"),
             (110.0, "DONE", "Experiment complete")],
        )
        self.assertEqual(p.advance(121.0), [])
        self.assertEqual(len(p.events), 5)
        self.assertIsInstance(p.events, tuple)

    def test_condition_is_deterministic_without_advance(self):
        p = EyesExperiment(open_seconds=1, closed_seconds=1, cycles=2)
        p.start(0.0)
        self.assertEqual([p.condition(t) for t in (0, .999, 1, 1.999, 2, 3, 4, 20)],
                         ["OPEN", "OPEN", "CLOSED", "CLOSED", "OPEN", "CLOSED", "DONE", "DONE"])
        self.assertEqual(len(p.events), 1)

    def test_fractional_schedule_matches_cue_times_at_realistic_unix_epoch(self):
        p = EyesExperiment(open_seconds=1.1, closed_seconds=1.7, cycles=3)
        first = p.start(1_793_000_000.123456)
        all_cues = first + p.advance(1_793_000_100.0)
        for cue in all_cues:
            with self.subTest(cue=cue):
                self.assertEqual(p.condition(cue.scheduled_epoch_s), cue.condition)

    def test_invalid_params_and_times_are_rejected(self):
        cases = [
            {"open_seconds": 0}, {"closed_seconds": -1},
            {"open_seconds": .001},
            {"open_seconds": math.inf}, {"closed_seconds": math.nan},
            {"cycles": 0}, {"cycles": 11}, {"cycles": True},
            {"open_seconds": 61}, {"closed_seconds": 61},
            {"open_seconds": 60, "closed_seconds": 60, "cycles": 6},
        ]
        for params in cases:
            with self.subTest(params=params), self.assertRaises(ValueError):
                EyesExperiment(**params)
        p = EyesExperiment()
        for bad in (float("nan"), float("inf"), -1, "tomorrow", True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                p.start(bad)
        p.start(12.0)
        for bad in (float("nan"), -1, "later", True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                p.advance(bad)

    def test_never_restart_or_reverse_observation_time(self):
        p = EyesExperiment(open_seconds=1, closed_seconds=1, cycles=1)
        self.assertEqual(p.advance(9.0), [])
        p.start(10.0)
        with self.assertRaises(RuntimeError):
            p.start(11.0)
        p.advance(11.0)
        with self.assertRaises(ValueError):
            p.advance(10.0)
        self.assertEqual(p.condition(9.0), "NOT_STARTED")


if __name__ == "__main__":
    unittest.main()
