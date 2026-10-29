"""Deterministic adapter contract tests; no device or BrainFlow installation required."""

import unittest

from memstack.muse2 import (
    AcquisitionError,
    BrainFlowBindings,
    Muse2CaptureSettings,
    acquire_muse2,
    inspect_plan,
)


EXPECTED_DESC = {
    "name": "Muse2", "sampling_rate": 256, "num_rows": 8,
    "timestamp_channel": 6, "package_num_channel": 0,
    "eeg_channels": [1, 2, 3, 4], "eeg_names": "TP9,AF7,AF8,TP10",
}
START = 1_799_000_000.0


class FakeParams:
    def __init__(self):
        self.mac_address = ""
        self.serial_number = ""
        self.other_info = ""


class FakeIds:
    class MUSE_2_BOARD:
        value = 38


class FakeShim:
    description = EXPECTED_DESC
    data = None
    instance = None
    fail_at = None

    @classmethod
    def get_board_descr(cls, board_id):
        assert board_id == 38
        return cls.description

    def __init__(self, board_id, params):
        self.events = []
        self.params = params
        self.board_id = board_id
        FakeShim.instance = self

    def prepare_session(self):
        self.events.append("prepare")
        if self.fail_at == "prepare":
            raise OSError("bluetooth unavailable")

    def start_stream(self):
        self.events.append("start")
        if self.fail_at == "start":
            raise OSError("stream unavailable")

    def stop_stream(self):
        self.events.append("stop")

    def get_board_data(self):
        self.events.append("drain")
        if self.fail_at == "drain":
            raise OSError("drain unavailable")
        return self.data

    def release_session(self):
        self.events.append("release")


def fake_data(times=(START, START + 1 / 256, START + 2 / 256)):
    n = len(times)
    return [[float(i) for i in range(n)],
            [1.] * n, [2.] * n, [3.] * n, [4.] * n,
            [50.] * n, list(times), [0.] * n]


BINDINGS = BrainFlowBindings(FakeShim, FakeIds, FakeParams)


class Muse2AdapterTests(unittest.TestCase):
    def setUp(self):
        FakeShim.description = dict(EXPECTED_DESC)
        FakeShim.data = fake_data()
        FakeShim.fail_at = None
        FakeShim.instance = None

    def test_inspection_is_offline_and_explicit_about_nonconnection(self):
        summary = inspect_plan()
        self.assertFalse(summary["device_connected"])
        self.assertFalse(summary["recording_started"])
        self.assertEqual(summary["eeg_channels"], ["TP9", "AF7", "AF8", "TP10"])

    def test_capture_requires_consent_before_board_creation(self):
        with self.assertRaises(PermissionError):
            acquire_muse2(Muse2CaptureSettings(seconds=1), bindings=BINDINGS, sleeper=lambda _: None)
        self.assertIsNone(FakeShim.instance)

    def test_capture_maps_eeg_only_and_preserves_clock_elapsed(self):
        settings = Muse2CaptureSettings(seconds=1, consent=True, serial_number="Muse-TEST")
        result = acquire_muse2(settings, bindings=BINDINGS, sleeper=lambda _: None)
        self.assertEqual(result.spec.source_kind, "DEVICE")
        self.assertEqual(result.spec.channel_names, ("TP9", "AF7", "AF8", "TP10"))
        self.assertEqual(result.spec.clock_domain, "brainflow_unix_timestamp_relative_s")
        self.assertEqual([f.eeg_uv for f in result.frames], [(1., 2., 3., 4.)] * 3)
        self.assertEqual(result.frames[0].time_s, 0.0)
        self.assertAlmostEqual(result.frames[1].time_s, 1 / 256, places=4)
        self.assertEqual(FakeShim.instance.params.other_info, "p21")
        self.assertEqual(FakeShim.instance.events,
                         ["prepare", "start", "stop", "drain", "release"])
        self.assertEqual(result.summary["samples"], 3)
        self.assertFalse(result.summary["hardware_acquisition_verified"])
        self.assertFalse(result.summary["memory_decoding_performed"])
        self.assertEqual(result.summary["source_timestamp_gap_intervals"], 0)

    def test_refuses_changed_brainflow_layout_before_connect(self):
        for delta in ({"eeg_channels": [2, 3, 4, 5]},
                      {"eeg_names": "AF7,AF8,TP9,TP10"},
                      {"sampling_rate": 200},
                      {"timestamp_channel": 4},
                      {"num_rows": 7}):
            FakeShim.description = EXPECTED_DESC | delta
            with self.subTest(delta=delta), self.assertRaises(AcquisitionError):
                acquire_muse2(Muse2CaptureSettings(seconds=1, consent=True),
                              bindings=BINDINGS, sleeper=lambda _: None)
            self.assertIsNone(FakeShim.instance)

    def test_timestamp_gap_diagnosed_without_forging_native_packet_loss(self):
        FakeShim.data = fake_data((START, START + 1 / 256, START + 7 / 256))
        result = acquire_muse2(Muse2CaptureSettings(seconds=1, consent=True),
                               bindings=BINDINGS, sleeper=lambda _: None)
        self.assertEqual(result.summary["source_timestamp_gap_intervals"], 1)
        self.assertEqual(result.summary["missing_index_slots"], 0)
        self.assertEqual(result.summary["native_packet_loss_verified"], False)

    def test_fails_closed_on_bad_timestamps_or_malformed_rows(self):
        bad_values = [
            fake_data((START, START, START + 2 / 256)),
            fake_data((START, START - 1, START + 2 / 256)),
            fake_data((0., 0.01, 0.02)),
            fake_data((START, float("nan"), START + 2 / 256)),
        ]
        malformed = fake_data()
        malformed[2] = [1.0]
        bad_values.append(malformed)
        nonfinite_signal = fake_data()
        nonfinite_signal[1][1] = float("nan")
        bad_values.append(nonfinite_signal)
        for raw in bad_values:
            FakeShim.data = raw
            with self.subTest(raw=raw[6]), self.assertRaises(AcquisitionError):
                acquire_muse2(Muse2CaptureSettings(seconds=1, consent=True),
                              bindings=BINDINGS, sleeper=lambda _: None)
            self.assertIn("release", FakeShim.instance.events)

    def test_cleanup_after_start_failure_or_drain_failure(self):
        for failure, expected in (("start", ["prepare", "start", "release"]),
                                  ("drain", ["prepare", "start", "stop", "drain", "release"])):
            FakeShim.fail_at = failure
            with self.subTest(failure=failure), self.assertRaises(OSError):
                acquire_muse2(Muse2CaptureSettings(seconds=1, consent=True),
                              bindings=BINDINGS, sleeper=lambda _: None)
            self.assertEqual(FakeShim.instance.events, expected)

    def test_cleanup_on_interrupt_during_capture(self):
        def interrupted(_):
            raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            acquire_muse2(Muse2CaptureSettings(seconds=1, consent=True),
                          bindings=BINDINGS, sleeper=interrupted)
        self.assertEqual(FakeShim.instance.events,
                         ["prepare", "start", "stop", "release"])

    def test_duration_and_device_selector_validation(self):
        for args in ({"seconds": -1}, {"seconds": 60},
                     {"seconds": float("nan")}, {"mac_address": "\n"},
                     {"serial_number": "abc\x00def"}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                Muse2CaptureSettings(**args)


if __name__ == "__main__":
    unittest.main()
