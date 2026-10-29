"""In-memory live Muse 2 source contracts; no Bluetooth devices are opened."""

import unittest

from memstack.live import CONNECT_TIMEOUT_SECONDS, LiveMuse2
from memstack.muse2 import AcquisitionError, BrainFlowBindings


START = 1_799_000_000.0
DESC = {
    "name": "Muse2", "sampling_rate": 256, "num_rows": 8,
    "timestamp_channel": 6, "eeg_channels": [1, 2, 3, 4],
    "eeg_names": "TP9,AF7,AF8,TP10",
}


def sample_matrix(times):
    n = len(times)
    return [list(range(n)), [10.0] * n, [20.0] * n,
            [30.0] * n, [40.0] * n, [0.0] * n,
            list(times), [0.0] * n]


class Params:
    def __init__(self):
        self.other_info = ""
        self.serial_number = ""
        self.mac_address = ""
        self.timeout = 0


class Ids:
    class MUSE_2_BOARD:
        value = 38


class FakeBoard:
    instance = None
    queued = []
    fail_at = None
    descriptor = DESC

    @classmethod
    def get_board_descr(cls, board_id):
        assert board_id == 38
        return cls.descriptor

    def __init__(self, board_id, params):
        self.params = params
        self.events = []
        self.buffer_size = None
        FakeBoard.instance = self

    def prepare_session(self):
        self.events.append("prepare")
        if self.fail_at == "prepare":
            raise OSError("prepare failed")

    def start_stream(self, buffer_size=450000):
        self.events.append("start")
        self.buffer_size = buffer_size
        if self.fail_at == "start":
            raise OSError("start failed")

    def get_board_data(self):
        self.events.append("poll")
        if self.fail_at == "poll":
            raise OSError("poll failed")
        if not self.queued:
            return sample_matrix(())
        return self.queued.pop(0)

    def stop_stream(self):
        self.events.append("stop")
        if self.fail_at == "stop":
            raise OSError("stop failed")

    def release_session(self):
        self.events.append("release")


API = BrainFlowBindings(FakeBoard, Ids, Params)


class LiveMuse2Tests(unittest.TestCase):
    def setUp(self):
        FakeBoard.instance = None
        FakeBoard.queued = []
        FakeBoard.fail_at = None
        FakeBoard.descriptor = dict(DESC)

    def test_consent_required_before_any_hardware_api(self):
        stream = LiveMuse2(consent=False, bindings=API)
        with self.assertRaises(PermissionError):
            stream.connect()
        self.assertIsNone(FakeBoard.instance)

    def test_connection_and_multiple_poll_batches_share_timeline(self):
        FakeBoard.queued = [
            sample_matrix((START, START + 1 / 256)),
            sample_matrix(()),
            sample_matrix((START + 2 / 256, START + 3 / 256)),
        ]
        source = LiveMuse2(consent=True, serial_number="Muse-TEST", bindings=API)
        source.connect()
        self.assertTrue(source.connected)
        self.assertEqual(FakeBoard.instance.params.other_info, "p21")
        self.assertEqual(FakeBoard.instance.params.serial_number, "Muse-TEST")
        self.assertEqual(FakeBoard.instance.params.timeout, CONNECT_TIMEOUT_SECONDS)
        self.assertEqual(CONNECT_TIMEOUT_SECONDS, 8)
        self.assertEqual(FakeBoard.instance.buffer_size, 4096)
        one = source.poll()
        self.assertEqual(source.poll(), ())
        two = source.poll()
        self.assertEqual([f.sample_index for f in one + two], [0, 1, 2, 3])
        self.assertEqual([f.eeg_uv for f in one + two], [(10., 20., 30., 40.)] * 4)
        self.assertAlmostEqual(one[0].time_s, 0.)
        self.assertAlmostEqual(two[1].time_s, 3 / 256, places=4)
        self.assertEqual(source.first_unix_timestamp_s, START)
        self.assertAlmostEqual(source.last_unix_timestamp_s, START + 3 / 256, places=5)
        source.close()
        source.close()
        self.assertFalse(source.connected)
        self.assertEqual(FakeBoard.instance.events,
                         ["prepare", "start", "poll", "poll", "poll", "stop", "release"])

    def test_poll_without_connection_is_rejected(self):
        with self.assertRaises(AcquisitionError):
            LiveMuse2(consent=True, bindings=API).poll()

    def test_changed_descriptor_is_rejected_before_device_construction(self):
        FakeBoard.descriptor = {**DESC, "eeg_channels": [1, 2, 3]}
        with self.assertRaises(AcquisitionError):
            LiveMuse2(consent=True, bindings=API).connect()
        self.assertIsNone(FakeBoard.instance)

    def test_timestamp_gap_count_crosses_poll_boundaries_without_loss_claim(self):
        FakeBoard.queued = [sample_matrix((START,)),
                            sample_matrix((START + 5 / 256,))]
        source = LiveMuse2(consent=True, bindings=API)
        source.connect()
        source.poll()
        source.poll()
        self.assertEqual(source.timestamp_gap_intervals, 1)
        self.assertEqual(source.samples_seen, 2)
        source.close()

    def test_duplicate_or_backward_timestamp_across_batches_fails_closed(self):
        for second in (START, START - 1):
            FakeBoard.queued = [sample_matrix((START,)), sample_matrix((second,))]
            source = LiveMuse2(consent=True, bindings=API)
            source.connect()
            source.poll()
            with self.subTest(second=second), self.assertRaises(AcquisitionError):
                source.poll()
            self.assertFalse(source.connected)
            self.assertEqual(FakeBoard.instance.events[-2:], ["stop", "release"])

    def test_malformed_nonfinite_and_unix_epoch_are_rejected(self):
        for raw in (sample_matrix((0.,)), sample_matrix((float("nan"),)),
                    [[0.0]] * 7, sample_matrix((START, START + 1 / 256))):
            if len(raw) == 8 and len(raw[1]) == 2:
                raw[1] = [10.0]  # asymmetric shape
            FakeBoard.queued = [raw]
            source = LiveMuse2(consent=True, bindings=API)
            source.connect()
            with self.subTest(raw=raw), self.assertRaises(AcquisitionError):
                source.poll()
            self.assertFalse(source.connected)

    def test_start_failure_releases_session(self):
        FakeBoard.fail_at = "start"
        source = LiveMuse2(consent=True, bindings=API)
        with self.assertRaises(AcquisitionError):
            source.connect()
        self.assertFalse(source.connected)
        self.assertEqual(FakeBoard.instance.events, ["prepare", "start", "release"])

    def test_stop_failure_still_releases_session(self):
        source = LiveMuse2(consent=True, bindings=API)
        source.connect()
        FakeBoard.fail_at = "stop"
        with self.assertRaises(AcquisitionError):
            source.close()
        self.assertFalse(source.connected)
        self.assertEqual(FakeBoard.instance.events[-2:], ["stop", "release"])

    def test_poll_failure_closes_session(self):
        FakeBoard.fail_at = "poll"
        source = LiveMuse2(consent=True, bindings=API)
        source.connect()
        with self.assertRaises(AcquisitionError):
            source.poll()
        self.assertFalse(source.connected)
        self.assertEqual(FakeBoard.instance.events[-2:], ["stop", "release"])

    def test_invalid_selector_fails_before_board_access(self):
        with self.assertRaises(ValueError):
            LiveMuse2(serial_number="bad\x00serial", consent=True, bindings=API)
        self.assertIsNone(FakeBoard.instance)


if __name__ == "__main__":
    unittest.main()
