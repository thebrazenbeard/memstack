"""Contract tests for the Essex metadata-only leakage boundary."""

import io
import unittest

from memstack.essex import (
    DatasetFormatError,
    LeakageError,
    build_first_watch_records,
    reject_unsafe_feature_columns,
    select_eeg_channels,
)

SOURCE_REF = "sub-001/eeg/sub-001_task-moviememory_events.tsv"


EVENTS = """onset\tduration\ttrial_type\tvalue\tsample\tstim_file
10.0\t0.0\ttrialStart\t192\t20480\tn/a
12.12451171875\t0.0\tstartOfNotRecognisedClip\t1\t24831\tNational_treasure_-_Book_of_Secrets_631_641_129.txt
22.1357421875\t0.0\tendOfClip\t129\t45334\tn/a
24.31884765625\t0.0\ttrialEnd\t193\t49805\tn/a
24.5185546875\t0.0\ttrialStart\t192\t50214\tn/a
26.26904296875\t0.0\tstartOfRememberedClipFirstWatch\t3\t53799\tHarry_Potter_7_-_and_the_Deathly_Hallows_-_Part_1_1563_1573_1.txt
36.27734375\t0.0\tendOfClip\t129\t74296\tn/a
41.16064453125\t0.0\tstartOfSecondWatch\t128\t84297\tHarry_Potter_7_-_and_the_Deathly_Hallows_-_Part_1_1563_1573_1.txt
43.0419921875\t0.0\tfirstRecognitionClick\t257\t88150\tn/a
51.1689453125\t0.0\tendOfClip\t129\t104794\tn/a
55.53466796875\t0.0\ttrialEnd\t193\t113735\tn/a
"""

CHANNELS = """name\ttype\tunits\tstatus
Fp1\tEEG\tV\tgood
O1\tEEG\tV\tgood
Status\tTRIG\tn/a\tgood
Fp2\tEEG\tV\tbad
"""


class FirstWatchTests(unittest.TestCase):
    def test_splits_labels_from_neural_epoch_metadata(self):
        windows, targets = build_first_watch_records(io.StringIO(EVENTS), source_ref=SOURCE_REF)
        self.assertEqual(len(windows), 2)
        self.assertEqual([x.label for x in targets], ["not_recognised", "remembered"])
        self.assertEqual([x.trial_id for x in windows], [0, 1])
        self.assertEqual([x.trial_key for x in windows], [x.trial_key for x in targets])
        self.assertNotEqual(windows[0].trial_key, windows[1].trial_key)
        self.assertAlmostEqual(windows[0].start_s, 12.37451171875)
        self.assertAlmostEqual(windows[0].end_s, 21.8857421875)
        self.assertAlmostEqual(windows[1].end_s, 36.02734375)
        self.assertEqual(targets[1].stimulus_ref.startswith("Harry_Potter"), True)
        for window in windows:
            self.assertFalse(any(k in vars(window) for k in ("label", "trial_type", "value", "stim_file", "stimulus_ref")))

    def test_unmatched_first_watch_fails(self):
        unfinished = EVENTS.split("22.1357421875")[0]
        with self.assertRaises(DatasetFormatError):
            build_first_watch_records(io.StringIO(unfinished), source_ref=SOURCE_REF)

    def test_backwards_timestamps_fail(self):
        corrupted = EVENTS.replace("24.5185546875", "2.5185546875")
        with self.assertRaises(DatasetFormatError):
            build_first_watch_records(io.StringIO(corrupted), source_ref=SOURCE_REF)

    def test_stable_source_qualified_trial_keys(self):
        first, _ = build_first_watch_records(io.StringIO(EVENTS), source_ref=SOURCE_REF)
        same, _ = build_first_watch_records(io.StringIO(EVENTS), source_ref=SOURCE_REF)
        other, _ = build_first_watch_records(io.StringIO(EVENTS), source_ref="sub-002/eeg/events.tsv")
        self.assertEqual([r.trial_key for r in first], [r.trial_key for r in same])
        self.assertTrue(set(r.trial_key for r in first).isdisjoint(r.trial_key for r in other))
        with self.assertRaises(ValueError):
            build_first_watch_records(io.StringIO(EVENTS), source_ref="")

    def test_trial_start_inside_clip_fails(self):
        corrupted = EVENTS.replace("22.1357421875", "20.0\t0.0\ttrialStart\t192\t40000\tn/a\n22.1357421875")
        with self.assertRaises(DatasetFormatError):
            build_first_watch_records(io.StringIO(corrupted), source_ref=SOURCE_REF)

    def test_unknown_clip_marker_rejected_even_when_only_trial_is_unknown(self):
        corrupted = EVENTS.replace("startOfRememberedClipFirstWatch", "startOfRememberedClipFirstWatchV2")
        with self.assertRaises(DatasetFormatError):
            build_first_watch_records(io.StringIO(corrupted), source_ref=SOURCE_REF)

    def test_unknown_clip_marker_cannot_cross_epoch(self):
        minimal = "onset\ttrial_type\tstim_file\n1\tstartOfNotRecognisedClip\tx\n3\tstartOfRememberedClipFirstWatchV2\ty\n8\tendOfClip\tn/a\n9\tendOfClip\tn/a\n"
        with self.assertRaises(DatasetFormatError):
            build_first_watch_records(io.StringIO(minimal), source_ref=SOURCE_REF)

    def test_extra_fields_or_duplicate_headers_rejected(self):
        overwide = "onset\ttrial_type\tstim_file\n1\tstartOfNotRecognisedClip\tx\tEXTRA\n11\tendOfClip\tn/a\n"
        duplicate = "onset\ttrial_type\tstim_file\tstim_file\n1\tstartOfNotRecognisedClip\tx\tx\n11\tendOfClip\tn/a\tn/a\n"
        for fixture in (overwide, duplicate):
            with self.subTest(fixture=fixture), self.assertRaises(DatasetFormatError):
                build_first_watch_records(io.StringIO(fixture), source_ref=SOURCE_REF)


class LeakageBoundaryTests(unittest.TestCase):
    def test_good_eeg_only_excludes_trigger_and_bad_channels(self):
        self.assertEqual(select_eeg_channels(io.StringIO(CHANNELS)), ("Fp1", "O1"))

    def test_metadata_columns_are_rejected(self):
        reject_unsafe_feature_columns(["eeg__Fp1__alpha", "eeg__O1__beta"])
        for name in ("trial_type", "value", "stim_file", "sample", "label", "onset", "eeg__trigger__alpha", "eeg__Fp1__stim_file"):
            with self.subTest(name=name), self.assertRaises(LeakageError):
                reject_unsafe_feature_columns(["eeg__Fp1__alpha", name])

    def test_empty_features_rejected(self):
        with self.assertRaises(LeakageError):
            reject_unsafe_feature_columns([])


if __name__ == "__main__":
    unittest.main()
