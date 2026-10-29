"""Leakage-aware metadata extraction for OpenNeuro ds006142 (Essex Movie Memory).

This does *not* decode memory or load EEG data. The original event annotations
contain post-hoc recognition outcomes at clip start, so target-bearing metadata
must be quarantined from neural model features.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO


DATASET_ID = "openneuro.ds006142.v1.0.2"
FIRST_WATCH_LABELS = {
    "startOfNotRecognisedClip": "not_recognised",
    "startOfRecognisedClipFirstWatch": "recognised",
    "startOfRememberedClipFirstWatch": "remembered",
}
NON_FIRST_WATCH_MARKERS = {
    "trialStart", "trialEnd", "endOfClip", "startOfSecondWatch",
    "firstRecognitionClick", "recognitionClick",
}
ALLOWED_EVENT_MARKERS = frozenset(FIRST_WATCH_LABELS) | NON_FIRST_WATCH_MARKERS
REQUIRED_EVENT_COLUMNS = {"onset", "trial_type", "stim_file"}
REQUIRED_CHANNEL_COLUMNS = {"name", "type", "status"}
_FEATURE_PATTERN = re.compile(r"eeg__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+\Z")
_UNSAFE_TOKENS = (
    "trigger", "status", "trial", "target", "label", "stim", "film",
    "recogn", "response", "click", "onset", "sample", "value", "time",
)


class DatasetFormatError(ValueError):
    """Input cannot be safely interpreted as expected BIDS metadata."""


class LeakageError(ValueError):
    """A proposed predictive feature may contain target/context information."""


@dataclass(frozen=True)
class EpochWindow:
    """Timing information used only to crop EEG, never as predictive features."""

    trial_id: int
    trial_key: str
    start_s: float
    end_s: float


@dataclass(frozen=True)
class HeldOutTarget:
    """Labels and stimulus references held outside the neural feature pipeline."""

    trial_id: int
    trial_key: str
    label: str
    stimulus_ref: str


def _required(reader: csv.DictReader, columns: set[str]) -> None:
    if reader.fieldnames is None or not columns.issubset(reader.fieldnames):
        missing = sorted(columns - set(reader.fieldnames or ()))
        raise DatasetFormatError(f"missing required columns: {missing}")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise DatasetFormatError("duplicate column names")


def _complete_row(row: dict, line_number: int) -> None:
    if None in row or any(value is None for value in row.values()):
        raise DatasetFormatError(f"malformed TSV row at line {line_number}")


def build_first_watch_records(
    input_tsv: TextIO, *, source_ref: str, edge_margin_s: float = 0.25
) -> tuple[tuple[EpochWindow, ...], tuple[HeldOutTarget, ...]]:
    """Pair first-view starts with their first end; drop all second-view periods.

    No label, trigger value, sample index or stimulus name enters EpochWindow.
    Edge margins reduce direct onset/offset artifacts but do not certify that
    remaining EEG is free of stimulus, eye-movement or other confounds.
    """
    if not math.isfinite(edge_margin_s) or edge_margin_s < 0:
        raise ValueError("edge_margin_s must be finite and nonnegative")
    if not source_ref or not source_ref.strip() or ".." in source_ref.split("/"):
        raise ValueError("source_ref must identify the BIDS-relative recording path")
    if source_ref.startswith("/") or "\\" in source_ref:
        raise ValueError("source_ref must use a relative, slash-delimited path")

    source_text = input_tsv.read()
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    source_key = f"{DATASET_ID}:{source_ref}@sha256:{source_hash}"
    reader = csv.DictReader(io.StringIO(source_text), delimiter="\t")
    _required(reader, REQUIRED_EVENT_COLUMNS)
    windows: list[EpochWindow] = []
    targets: list[HeldOutTarget] = []
    pending: tuple[float, str, str] | None = None
    previous_onset = -math.inf

    for line_number, row in enumerate(reader, start=2):
        _complete_row(row, line_number)
        try:
            onset = float(row["onset"])
        except (TypeError, ValueError) as exc:
            raise DatasetFormatError(f"invalid onset at line {line_number}") from exc
        if not math.isfinite(onset) or onset < 0 or onset < previous_onset:
            raise DatasetFormatError(f"out-of-order or invalid onset at line {line_number}")
        previous_onset = onset
        marker = row["trial_type"]
        if marker not in ALLOWED_EVENT_MARKERS:
            raise DatasetFormatError(f"unknown event marker {marker!r} at line {line_number}")
        if pending is not None and marker not in ("endOfClip",):
            raise DatasetFormatError(f"intervening event while first-watch clip open at line {line_number}")

        if marker in FIRST_WATCH_LABELS:
            stimulus = row["stim_file"]
            if not stimulus or stimulus == "n/a":
                raise DatasetFormatError(f"missing stimulus reference at line {line_number}")
            pending = (onset, FIRST_WATCH_LABELS[marker], stimulus)
        elif marker == "endOfClip" and pending is not None:
            start, label, stimulus = pending
            if onset - start <= 2 * edge_margin_s:
                raise DatasetFormatError(f"clip too short for safe window at line {line_number}")
            trial_id = len(windows)
            trial_key = f"{source_key}:trial:{trial_id}"
            windows.append(EpochWindow(trial_id, trial_key, start + edge_margin_s, onset - edge_margin_s))
            targets.append(HeldOutTarget(trial_id, trial_key, label, stimulus))
            pending = None

    if pending is not None:
        raise DatasetFormatError("unmatched first-watch start at end of file")
    if not windows:
        raise DatasetFormatError("no first-watch epochs found")
    return tuple(windows), tuple(targets)


def select_eeg_channels(input_tsv: TextIO) -> tuple[str, ...]:
    """Only explicitly typed, good EEG channels; never a trigger channel."""
    reader = csv.DictReader(input_tsv, delimiter="\t")
    _required(reader, REQUIRED_CHANNEL_COLUMNS)
    names: list[str] = []
    for line_number, row in enumerate(reader, start=2):
        _complete_row(row, line_number)
        if row["type"].upper() == "EEG" and row["status"].lower() == "good":
            name = row["name"]
            if not name or name in names:
                raise DatasetFormatError("blank or duplicate EEG channel name")
            names.append(name)
    if not names:
        raise DatasetFormatError("no usable EEG channels")
    return tuple(names)


def reject_unsafe_feature_columns(columns: Iterable[str]) -> None:
    """Fail closed if candidate model inputs are not explicitly EEG features.

    This is a naming-boundary check, not a proof of causal data lineage.
    Upstream feature extraction must independently verify channel selections.
    """
    names = tuple(columns)
    if not names:
        raise LeakageError("no neural features")
    for name in names:
        if (
            not isinstance(name, str)
            or not _FEATURE_PATTERN.fullmatch(name)
            or any(token in name.lower() for token in _UNSAFE_TOKENS)
        ):
            raise LeakageError(f"unsafe predictive feature column: {name!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Metadata-only Essex first-watch audit; no EEG decoding")
    parser.add_argument("events", type=Path)
    parser.add_argument("channels", type=Path)
    parser.add_argument("--source-ref", required=True,
                        help="Canonical dataset-relative events path, e.g. sub-001/eeg/sub-001_task-..._events.tsv")
    args = parser.parse_args()
    with args.events.open("r", encoding="utf-8", newline="") as f:
        windows, targets = build_first_watch_records(f, source_ref=args.source_ref)
    with args.channels.open("r", encoding="utf-8", newline="") as f:
        channels = select_eeg_channels(f)
    print(json.dumps({
        "dataset": DATASET_ID,
        "task": "first_watch_recognition_metadata_audit",
        "source_ref": args.source_ref,
        "source_key": windows[0].trial_key.rsplit(":trial:", 1)[0],
        "first_watch_count": len(windows),
        "labels": dict(sorted(Counter(t.label for t in targets).items())),
        "usable_eeg_channels": len(channels),
        "neural_data_loaded": False,
        "memory_decoding_performed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
