"""Self-paced, finite eyes-open/eyes-closed cue schedule for EEG pilots.

Cue times are *scheduled* local Unix timestamps. They are neither observations
of headset samples nor measurements of audible cue onset. The UI owns playback
and should mark its attempt separately; no neural interpretation happens here.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from dataclasses import dataclass


@dataclass(frozen=True)
class Cue:
    scheduled_epoch_s: float
    condition: str
    instruction: str


class EyesExperiment:
    """Finite alternating conditions that require no mid-trial chat exchange.

    `advance` yields *every* due cue once. If a UI poll is late, it should retain
    all scheduled event markers but announce only the latest relevant cue, not
    speak a backlog of stale instructions. There is no device access or storage.
    """

    def __init__(self, open_seconds: float = 10.0,
                 closed_seconds: float = 10.0, cycles: int = 3):
        self.open_seconds = _duration("open_seconds", open_seconds)
        self.closed_seconds = _duration("closed_seconds", closed_seconds)
        if type(cycles) is not int or not 1 <= cycles <= 10:
            raise ValueError("cycles must be an integer from 1 to 10")
        if (self.open_seconds + self.closed_seconds) * cycles > 600:
            raise ValueError("experiment must not exceed 600 seconds")
        self.cycles = cycles
        self.total_seconds = (self.open_seconds + self.closed_seconds) * cycles
        self._started_epoch_s: float | None = None
        self._last_advanced_s: float | None = None
        self._scheduled: tuple[Cue, ...] = ()
        self._scheduled_times: tuple[float, ...] = ()
        self._emitted: list[Cue] = []
        self._cursor = 0

    @property
    def events(self) -> tuple[Cue, ...]:
        """Scheduled cues emitted so far (immutable view, not device samples)."""
        return tuple(self._emitted)

    @property
    def end_epoch_s(self) -> float | None:
        if self._started_epoch_s is None:
            return None
        return self._started_epoch_s + self.total_seconds

    def start(self, epoch_s: float) -> list[Cue]:
        """Start once; immediately emit the initial eyes-open instruction."""
        epoch_s = _epoch(epoch_s)
        if self._started_epoch_s is not None:
            raise RuntimeError("experiment already started")
        self._started_epoch_s = epoch_s
        self._last_advanced_s = epoch_s
        cues: list[Cue] = []
        cycle_len = self.open_seconds + self.closed_seconds
        for i in range(self.cycles):
            begin = epoch_s + i * cycle_len
            cues.append(Cue(begin, "OPEN", "Open your eyes"))
            cues.append(Cue(begin + self.open_seconds, "CLOSED", "Close your eyes"))
        cues.append(Cue(epoch_s + self.total_seconds, "DONE", "Experiment complete"))
        self._scheduled = tuple(cues)
        self._scheduled_times = tuple(cue.scheduled_epoch_s for cue in cues)
        return self._drain_due(epoch_s)

    def advance(self, epoch_s: float) -> list[Cue]:
        """Return each newly due scheduled transition exactly once."""
        epoch_s = _epoch(epoch_s)
        if self._started_epoch_s is None:
            return []
        if self._last_advanced_s is not None and epoch_s < self._last_advanced_s:
            raise ValueError("experiment observation clock moved backward")
        self._last_advanced_s = epoch_s
        return self._drain_due(epoch_s)

    def condition(self, epoch_s: float) -> str:
        """Compute the scheduled condition without emitting any cues."""
        epoch_s = _epoch(epoch_s)
        if self._started_epoch_s is None or epoch_s < self._started_epoch_s:
            return "NOT_STARTED"
        # Lookup the same absolute event boundaries used by `advance`. Using
        # elapsed % cycle_length can disagree at fractional-second boundaries
        # because Unix epochs are large floats with limited precision.
        index = bisect_right(self._scheduled_times, epoch_s) - 1
        return self._scheduled[index].condition

    def _drain_due(self, epoch_s: float) -> list[Cue]:
        due: list[Cue] = []
        while (self._cursor < len(self._scheduled)
               and self._scheduled[self._cursor].scheduled_epoch_s <= epoch_s):
            cue = self._scheduled[self._cursor]
            due.append(cue)
            self._emitted.append(cue)
            self._cursor += 1
        return due


def _duration(name: str, value: float) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not 1 <= value <= 60):
        raise ValueError(f"{name} must be a finite number in [1, 60]")
    return float(value)


def _epoch(value: float) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0):
        raise ValueError("epoch_s must be a finite nonnegative Unix timestamp")
    return float(value)
