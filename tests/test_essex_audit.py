"""Offline contract tests for the pinned whole-dataset metadata audit."""

import unittest

from scripts.audit_essex_metadata import audit_subject, paths_for_subject
from test_essex import EVENTS, CHANNELS


class PublicMetadataAuditTests(unittest.TestCase):
    def test_subject_audit_records_content_hashes_and_counts(self):
        result = audit_subject("sub-001", EVENTS.encode(), CHANNELS.encode())
        self.assertEqual(result["first_watch"], 2)
        self.assertEqual(result["second_watch"], 1)
        self.assertEqual(result["end_of_clip"], 3)
        self.assertEqual(result["usable_eeg_channels"], 2)
        self.assertEqual(result["labels"], {"not_recognised": 1, "remembered": 1})
        self.assertEqual(len(result["events_sha256"]), 64)

    def test_rejects_broken_trial_count_even_if_parser_finds_clip(self):
        no_trial_start = EVENTS.replace("trialStart", "firstRecognitionClick")
        with self.assertRaisesRegex(ValueError, "trial count mismatch"):
            audit_subject("sub-001", no_trial_start.encode(), CHANNELS.encode())

    def test_relative_pinned_dataset_paths(self):
        self.assertEqual(paths_for_subject("sub-019"), (
            "sub-019/eeg/sub-019_task-MovieMemory_events.tsv",
            "sub-019/eeg/sub-019_task-MovieMemory_channels.tsv",
        ))


if __name__ == "__main__":
    unittest.main()
