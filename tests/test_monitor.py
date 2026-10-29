"""Headless tests for MemStack Monitor's display and bounded-memory helpers."""

import importlib
import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from memstack.waveform import RawEEGFrame


class MonitorUnitTests(unittest.TestCase):
    def test_module_import_does_not_create_a_window_or_connect(self):
        monitor = importlib.import_module("memstack.monitor")
        self.assertTrue(callable(monitor.main))

    def test_signal_window_drops_old_samples(self):
        from memstack.monitor import SignalWindow

        view = SignalWindow(max_samples=4)
        view.add(tuple(RawEEGFrame(i, i / 256, (float(i),) * 4) for i in range(7)))
        self.assertEqual(len(view.frames), 4)
        self.assertEqual([f.sample_index for f in view.frames], [3, 4, 5, 6])

    def test_quality_flags_cannot_claim_clean_brainwaves(self):
        from memstack.monitor import signal_flags

        self.assertEqual(signal_flags(()), ("NO_DATA",) * 4)
        ordinary = tuple(RawEEGFrame(i, i / 256, (float(i % 9),) * 4) for i in range(64))
        self.assertEqual(signal_flags(ordinary), ("UNASSESSED",) * 4)
        artifact = list(ordinary)
        artifact[9] = RawEEGFrame(9, 9 / 256, (1000., 2., 2., 2.))
        self.assertEqual(signal_flags(artifact)[0], "POSSIBLE_ARTIFACT")
        self.assertEqual(signal_flags(artifact)[1], "UNASSESSED")

    def test_flatline_suspected_not_proven_contact_failure(self):
        from memstack.monitor import signal_flags

        flat = tuple(RawEEGFrame(i, i / 256, (1., 2., float(i % 11), 4.)) for i in range(64))
        flags = signal_flags(flat)
        self.assertEqual(flags[0], "POSSIBLE_FLATLINE")
        self.assertEqual(flags[1], "POSSIBLE_FLATLINE")
        self.assertEqual(flags[2], "UNASSESSED")

    def test_trace_points_remain_inside_viewport(self):
        from memstack.monitor import trace_points

        vals = [-1000., -50., 0., 75., 1000.]
        pts = trace_points(vals, width=200, height=50, scale_uv=200)
        self.assertEqual(len(pts), 5)
        self.assertEqual(pts[0][0], 0.)
        self.assertEqual(pts[-1][0], 200.)
        self.assertTrue(all(0. <= x <= 200. and 0. <= y <= 50. for x, y in pts))

    def test_stop_capture_zeros_ephemeral_raw_window_and_cancels_old_audio(self):
        from memstack.monitor import MonitorApp, SignalWindow

        class DummyLabel:
            def __init__(self):
                self.value = None

            def set(self, value):
                self.value = value

            def configure(self, **_):
                pass

        view = SignalWindow()
        view.add((RawEEGFrame(0, 0., (12., 13., 14., 15.)),))
        speaker = SimpleNamespace(discard_count=0)

        def discard():
            speaker.discard_count += 1

        speaker.discard = discard
        ui = SimpleNamespace(
            worker=None, speaker=speaker, view=view, last_samples_mono=1.,
            accept_samples=True, experiment=object(), experiment_completed=False,
            experiment_button=DummyLabel(), audio_test_button=DummyLabel(),
            condition=DummyLabel(),
        )
        MonitorApp.stop_capture(ui)
        self.assertEqual(len(view.frames), 0)
        self.assertFalse(ui.accept_samples)
        self.assertIsNone(ui.experiment)
        self.assertEqual(speaker.discard_count, 1)
        self.assertEqual(ui.condition.value, "STOPPED")

    def test_local_epoch_estimate_uses_monotonic_time(self):
        from memstack.monitor import MonitorApp
        ui = SimpleNamespace(epoch_anchor=1000., monotonic_anchor=20.)
        with patch("memstack.monitor.time.monotonic", return_value=22.5):
            self.assertEqual(MonitorApp.now_epoch(ui), 1002.5)

    def test_ui_queue_drops_only_visualization_data_when_full(self):
        from memstack.monitor import _publish
        items = queue.Queue(maxsize=1)
        self.assertTrue(_publish(items, "samples", (1,)))
        self.assertFalse(_publish(items, "samples", (2,)))
        self.assertEqual(items.get_nowait(), ("samples", (1,)))

    def test_audio_discard_invalidates_cues_without_launching_speech(self):
        from memstack.monitor import WindowsSpeaker
        speaker = WindowsSpeaker.__new__(WindowsSpeaker)
        speaker.pending = queue.Queue(maxsize=4)
        speaker.pending.put_nowait((0, "Open your eyes"))
        speaker.pending.put_nowait((0, "Close your eyes"))
        speaker.lock = threading.Lock()
        speaker.generation = 0
        speaker.active = None
        speaker.discard()
        self.assertEqual(speaker.generation, 1)
        self.assertTrue(speaker.pending.empty())
        with self.assertRaises(ValueError):
            WindowsSpeaker.say(speaker, "Erase memory")


if __name__ == "__main__":
    unittest.main()
