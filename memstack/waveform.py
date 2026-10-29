"""Hardware-independent raw EEG frame validation, replay and synthetic source.

No live headset, Bluetooth connection, memory decoder or clinical measurement
is implemented here. Device-origin metadata is caller-declared, not attested.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Iterable, TextIO


SCHEMA = "memstack.raw_eeg.v0"
SOURCE_KINDS = frozenset(("SYNTHETIC", "DEVICE", "REPLAY"))
SPEC_FIELDS = frozenset(("schema", "source_kind", "stream_id", "sample_rate_hz",
                         "channel_names", "clock_domain", "units"))
FRAME_FIELDS = frozenset(("kind", "sample_index", "time_s", "eeg_uv"))
MAX_REPLAY_FRAMES = 2_000_000


class StreamFormatError(ValueError):
    """A raw EEG frame or its provenance envelope is invalid."""


@dataclass(frozen=True)
class RawEEGStreamSpec:
    source_kind: str
    stream_id: str
    sample_rate_hz: float
    channel_names: tuple[str, ...]
    clock_domain: str
    units: str = "uV"

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, str) or self.source_kind not in SOURCE_KINDS:
            raise StreamFormatError("unknown or unqualified source kind")
        if not self.stream_id or not self.stream_id.strip():
            raise StreamFormatError("stream ID required")
        if not self.clock_domain or not self.clock_domain.strip():
            raise StreamFormatError("clock domain required")
        if (isinstance(self.sample_rate_hz, bool)
                or not isinstance(self.sample_rate_hz, (int, float))
                or not math.isfinite(self.sample_rate_hz)
                or not 0 < self.sample_rate_hz <= 10000):
            raise StreamFormatError("invalid sample rate")
        if (not self.channel_names
                or any(not isinstance(n, str) or not n.strip() for n in self.channel_names)
                or len(self.channel_names) != len(set(self.channel_names))):
            raise StreamFormatError("blank or duplicate EEG channel name")
        if self.units != "uV":
            raise StreamFormatError("this schema accepts microvolt EEG only")

    def to_record(self) -> dict:
        return {
            "schema": SCHEMA,
            "source_kind": self.source_kind,
            "stream_id": self.stream_id,
            "sample_rate_hz": self.sample_rate_hz,
            "channel_names": list(self.channel_names),
            "clock_domain": self.clock_domain,
            "units": self.units,
        }


@dataclass(frozen=True)
class RawEEGFrame:
    sample_index: int
    time_s: float
    eeg_uv: tuple[float, ...]


class StreamQC:
    """Monotonicity and gross continuity checks; not EEG artifact certification."""

    def __init__(self, spec: RawEEGStreamSpec) -> None:
        self.spec = spec
        self.count = 0
        self.missing = 0
        self.first_index: int | None = None
        self.last_index: int | None = None
        self.first_time: float | None = None
        self.last_time: float | None = None
        self.max_abs = [0.0] * len(spec.channel_names)

    def push(self, frame: RawEEGFrame) -> None:
        if (not isinstance(frame.sample_index, int)
                or isinstance(frame.sample_index, bool)
                or frame.sample_index < 0):
            raise StreamFormatError("invalid sample index")
        if (not isinstance(frame.time_s, (int, float))
                or isinstance(frame.time_s, bool)
                or not math.isfinite(frame.time_s) or frame.time_s < 0):
            raise StreamFormatError("invalid sample timestamp")
        if (not isinstance(frame.eeg_uv, (tuple, list))
                or len(frame.eeg_uv) != len(self.spec.channel_names) or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
            for v in frame.eeg_uv
        )):
            raise StreamFormatError("invalid EEG channel values")
        if self.last_index is not None:
            if frame.sample_index <= self.last_index:
                raise StreamFormatError("duplicate or backwards sample index")
            if frame.time_s <= self.last_time:
                raise StreamFormatError("duplicate or backwards sample time")
            self.missing += frame.sample_index - self.last_index - 1
        else:
            self.first_index = frame.sample_index
            self.first_time = frame.time_s
        self.last_index = frame.sample_index
        self.last_time = frame.time_s
        self.count += 1
        for i, value in enumerate(frame.eeg_uv):
            self.max_abs[i] = max(self.max_abs[i], abs(value))

    def summary(self) -> dict:
        if self.count == 0:
            raise StreamFormatError("empty signal stream")
        delta_s = self.last_time - self.first_time
        observed_rate = ((self.last_index - self.first_index) / delta_s
                         if delta_s > 0 else None)
        return {
            "schema": SCHEMA,
            "source_kind": self.spec.source_kind,
            "stream_id": self.spec.stream_id,
            "clock_domain": self.spec.clock_domain,
            "declared_sample_rate_hz": self.spec.sample_rate_hz,
            "observed_sample_rate_hz": observed_rate,
            "channels": list(self.spec.channel_names),
            "units": self.spec.units,
            "samples": self.count,
            "missing_index_slots": self.missing,
            "max_abs_uv": self.max_abs,
            "device_origin_declared": self.spec.source_kind == "DEVICE",
            "hardware_acquisition_verified": False,
            "memory_decoding_performed": False,
        }


def generate_synthetic_eeg(spec: RawEEGStreamSpec, *, duration_s: float):
    """Deterministic 10-Hz test wave, not measured brain activity."""
    if spec.source_kind != "SYNTHETIC":
        raise StreamFormatError("cannot fabricate device or replay EEG")
    if not math.isfinite(duration_s) or not 0 < duration_s <= 60:
        raise ValueError("duration_s must be finite, positive, and at most 60")
    n_samples = round(spec.sample_rate_hz * duration_s)
    if n_samples <= 0:
        raise StreamFormatError("simulation would be empty")
    for index in range(n_samples):
        t = index / spec.sample_rate_hz
        yield RawEEGFrame(index, t, tuple(
            round(20.0 * math.sin(2 * math.pi * 10.0 * t + channel * 0.23), 6)
            for channel in range(len(spec.channel_names))
        ))


def write_stream_jsonl(out: TextIO, spec: RawEEGStreamSpec,
                       frames: Iterable[RawEEGFrame]) -> dict:
    """Write explicit raw sample fields; never embed target or cue labels."""
    qc = StreamQC(spec)
    out.write(json.dumps({"kind": "header", **spec.to_record()}, separators=(",", ":")) + "\n")
    for frame in frames:
        qc.push(frame)
        out.write(json.dumps({"kind": "frame", "sample_index": frame.sample_index,
                              "time_s": frame.time_s, "eeg_uv": frame.eeg_uv},
                             separators=(",", ":")) + "\n")
    return qc.summary()


def _strict_json(text: str) -> dict:
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise StreamFormatError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    try:
        obj = json.loads(text, object_pairs_hook=unique_pairs)
    except (ValueError, TypeError) as exc:
        raise StreamFormatError("invalid signal JSONL") from exc
    if not isinstance(obj, dict):
        raise StreamFormatError("each JSONL line must be an object")
    return obj


def read_stream_jsonl(source: TextIO) -> tuple[RawEEGStreamSpec, tuple[RawEEGFrame, ...]]:
    """Read a bounded envelope; reject all label, cue and extra model fields."""
    first = source.readline()
    if not first:
        raise StreamFormatError("missing header")
    header = _strict_json(first)
    if set(header) != SPEC_FIELDS | {"kind"} or header["kind"] != "header":
        raise StreamFormatError("unexpected stream-header fields")
    if header["schema"] != SCHEMA or not isinstance(header["channel_names"], list):
        raise StreamFormatError("unsupported signal schema")
    spec = RawEEGStreamSpec(
        source_kind=header["source_kind"], stream_id=header["stream_id"],
        sample_rate_hz=header["sample_rate_hz"],
        channel_names=tuple(header["channel_names"]),
        clock_domain=header["clock_domain"], units=header["units"],
    )
    qc = StreamQC(spec)
    frames: list[RawEEGFrame] = []
    for number, line in enumerate(source, start=2):
        if number > MAX_REPLAY_FRAMES + 1:
            raise StreamFormatError("replay exceeds permitted frame count")
        obj = _strict_json(line)
        if set(obj) != FRAME_FIELDS or obj["kind"] != "frame" or not isinstance(obj["eeg_uv"], list):
            raise StreamFormatError(f"unexpected frame fields at line {number}")
        frame = RawEEGFrame(obj["sample_index"], obj["time_s"], tuple(obj["eeg_uv"]))
        qc.push(frame)
        frames.append(frame)
    qc.summary()
    return spec, tuple(frames)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Synthetic-only raw EEG stream check; no headset accessed")
    parser.add_argument("--seconds", type=float, default=2.0)
    args = parser.parse_args()
    spec = RawEEGStreamSpec(
        source_kind="SYNTHETIC", stream_id="synthetic-muse2-4ch",
        sample_rate_hz=256, channel_names=("TP9", "AF7", "AF8", "TP10"),
        clock_domain="synthetic_elapsed_seconds")
    qc = StreamQC(spec)
    for frame in generate_synthetic_eeg(spec, duration_s=args.seconds):
        qc.push(frame)
    print(json.dumps(qc.summary(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
