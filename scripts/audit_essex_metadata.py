"""Bounded public-metadata-only audit of OpenNeuro Essex Movie Memory.

Fetches only events.tsv and channels.tsv files, never EDF, videos or people data.
Each source URL is pinned to one upstream Git commit. No model is trained.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.request
from collections import Counter
from pathlib import Path

from memstack.essex import build_first_watch_records, select_eeg_channels


UPSTREAM_SHA = "6af022b2d66e98573bf4fc8ffc7e0d2a02c66f65"
BASE_URL = f"https://raw.githubusercontent.com/OpenNeuroDatasets/ds006142/{UPSTREAM_SHA}"
EXPECTED_FIRST_WATCH = 4153
EXPECTED_FIRST_WATCH_LABELS = {
    "not_recognised": 2212,
    "recognised": 515,
    "remembered": 1426,
}
SUBJECTS = tuple(f"sub-{i:03d}" for i in range(1, 28))


def paths_for_subject(subject: str) -> tuple[str, str]:
    root = f"{subject}/eeg/{subject}_task-MovieMemory"
    return root + "_events.tsv", root + "_channels.tsv"


def fetch_metadata(relative_path: str) -> bytes:
    """Read at most 2 MiB; prohibit a response larger than expected metadata."""
    request = urllib.request.Request(f"{BASE_URL}/{relative_path}", headers={
        "User-Agent": "MemStack-public-metadata-research/0.1",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError(f"metadata unexpectedly large: {relative_path}")
    return data


def audit_subject(subject: str, events_bytes: bytes, channels_bytes: bytes) -> dict:
    event_path, channel_path = paths_for_subject(subject)
    windows, targets = build_first_watch_records(
        io.StringIO(events_bytes.decode("utf-8-sig")), source_ref=event_path)
    channels = select_eeg_channels(io.StringIO(channels_bytes.decode("utf-8-sig")))
    if len(windows) != len(targets):
        raise AssertionError(f"window/target count mismatch: {subject}")
    if len(set(window.trial_key for window in windows)) != len(windows):
        raise AssertionError(f"colliding trial keys: {subject}")
    event_types = Counter(
        line.split("\t")[2] for line in events_bytes.decode("utf-8-sig").splitlines()[1:]
    )
    if event_types["trialStart"] != len(windows):
        raise ValueError(f"trial count mismatch: {subject}")
    if event_types["endOfClip"] != len(windows) + event_types["startOfSecondWatch"]:
        raise ValueError(f"clip-end count mismatch: {subject}")
    return {
        "subject": subject,
        "events_ref": event_path,
        "events_sha256": hashlib.sha256(events_bytes).hexdigest(),
        "channels_ref": channel_path,
        "channels_sha256": hashlib.sha256(channels_bytes).hexdigest(),
        "first_watch": len(windows),
        "labels": dict(sorted(Counter(target.label for target in targets).items())),
        "second_watch": event_types["startOfSecondWatch"],
        "end_of_clip": event_types["endOfClip"],
        "usable_eeg_channels": len(channels),
    }


def audit_all(fetch=fetch_metadata) -> dict:
    subjects = []
    totals = Counter()
    labels = Counter()
    for subject in SUBJECTS:
        event_path, channel_path = paths_for_subject(subject)
        result = audit_subject(subject, fetch(event_path), fetch(channel_path))
        subjects.append(result)
        for key in ("first_watch", "second_watch", "end_of_clip"):
            totals[key] += result[key]
        labels.update(result["labels"])
    if totals["first_watch"] != EXPECTED_FIRST_WATCH or dict(labels) != EXPECTED_FIRST_WATCH_LABELS:
        raise ValueError("pinned source counts differ from independently audited reference")
    return {
        "dataset": "openneuro.ds006142.v1.0.2",
        "upstream_git_commit": UPSTREAM_SHA,
        "audit_kind": "PUBLIC_METADATA_ONLY",
        "subject_count": len(subjects),
        "totals": dict(totals),
        "labels": dict(sorted(labels.items())),
        "neural_data_loaded": False,
        "memory_decoding_performed": False,
        "subjects": subjects,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_all()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "git_commit": UPSTREAM_SHA,
        "subjects": result["subject_count"],
        "first_watch": result["totals"]["first_watch"],
        "labels": result["labels"],
        "neural_data_loaded": False,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
