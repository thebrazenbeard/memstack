"""Hardware-free tests for the raw EEG stream foundation."""

import io
import json
import unittest

from memstack.waveform import (
    RawEEGFrame,
    RawEEGStreamSpec,
    StreamFormatError,
    StreamQC,
    generate_synthetic_eeg,
    read_stream_jsonl,
    write_stream_jsonl,
)


SPEC = RawEEGStreamSpec(
    source_kind="SYNTHETIC", stream_id="test-sim", sample_rate_hz=256,
    channel_names=("TP9", "AF7", "AF8", "TP10"),
    clock_domain="synthetic_elapsed_seconds",
)


class WaveformFoundationTests(unittest.TestCase):
    def test_four_channel_simulation_and_quality_summary(self):
        frames = tuple(generate_synthetic_eeg(SPEC, duration_s=2))
        self.assertEqual(len(frames), 512)
        qc = StreamQC(SPEC)
        for frame in frames:
            qc.push(frame)
        summary = qc.summary()
        self.assertEqual(summary["source_kind"], "SYNTHETIC")
        self.assertEqual(summary["samples"], 512)
        self.assertEqual(summary["missing_index_slots"], 0)
        self.assertEqual(summary["channels"], ["TP9", "AF7", "AF8", "TP10"])
        self.assertAlmostEqual(summary["observed_sample_rate_hz"], 256)
        self.assertFalse(summary["hardware_acquisition_verified"])
        self.assertFalse(summary["memory_decoding_performed"])

    def test_gap_is_counted_not_silently_interpolated(self):
        qc = StreamQC(SPEC)
        for index in (0, 1, 3):
            qc.push(RawEEGFrame(index, index / 256, (1.0, 2.0, 3.0, 4.0)))
        self.assertEqual(qc.summary()["missing_index_slots"], 1)

    def test_bad_frame_values_and_time_order_fail_closed(self):
        bad = [
            RawEEGFrame(0, 0.0, (1.0, 2.0)),
            RawEEGFrame(0, float("nan"), (1.0, 2.0, 3.0, 4.0)),
            RawEEGFrame(0, 0.0, (1.0, float("inf"), 3.0, 4.0)),
        ]
        for frame in bad:
            with self.subTest(frame=frame), self.assertRaises(StreamFormatError):
                StreamQC(SPEC).push(frame)
        qc = StreamQC(SPEC)
        qc.push(RawEEGFrame(0, 0.0, (1.0, 2.0, 3.0, 4.0)))
        for frame in (
            RawEEGFrame(0, 0.01, (1.0, 2.0, 3.0, 4.0)),
            RawEEGFrame(1, 0.0, (1.0, 2.0, 3.0, 4.0)),
        ):
            with self.subTest(frame=frame), self.assertRaises(StreamFormatError):
                qc.push(frame)

    def test_spec_rejects_invalid_channels_or_units(self):
        kwargs = dict(source_kind="SYNTHETIC", stream_id="s", sample_rate_hz=256,
                      channel_names=("AF7", "AF8"), clock_domain="sim")
        for extra in ({"channel_names": ("AF7", "AF7")},
                      {"channel_names": ("AF7", "")},
                      {"sample_rate_hz": 0}, {"units": "volts"},
                      {"source_kind": "UNKNOWN"}):
            with self.subTest(extra=extra), self.assertRaises(StreamFormatError):
                RawEEGStreamSpec(**(kwargs | extra))

    def test_jsonl_roundtrip_preserves_raw_samples(self):
        frames = tuple(generate_synthetic_eeg(SPEC, duration_s=0.25))
        buf = io.StringIO()
        write_stream_jsonl(buf, SPEC, frames)
        buf.seek(0)
        spec, replay = read_stream_jsonl(buf)
        self.assertEqual(spec, SPEC)
        self.assertEqual(replay, frames)

    def test_jsonl_refuses_label_or_other_model_metadata(self):
        header = {"kind": "header", **SPEC.to_record()}
        injected = {"kind": "frame", "sample_index": 0, "time_s": 0,
                    "eeg_uv": [0, 0, 0, 0], "recognition_label": "remembered"}
        with self.assertRaises(StreamFormatError):
            read_stream_jsonl(io.StringIO(json.dumps(header) + "\n" + json.dumps(injected) + "\n"))

    def test_jsonl_rejects_untrusted_channel_shape_and_duplicate_keys(self):
        header = {"kind": "header", **SPEC.to_record()}
        header["channel_names"] = [["TP9"], "AF7", "AF8", "TP10"]
        with self.assertRaises(StreamFormatError):
            read_stream_jsonl(io.StringIO(json.dumps(header) + "\n"))
        duplicate = '{"kind":"header","kind":"header"}'
        with self.assertRaises(StreamFormatError):
            read_stream_jsonl(io.StringIO(duplicate + "\n"))


if __name__ == "__main__":
    unittest.main()
