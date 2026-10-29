"""Explicitly consented, bounded, in-memory Muse 2 EEG streaming.

The caller owns the polling cadence and must call all session methods from
one thread. No device is discovered on import or during construction. Every
poll drains BrainFlow's bounded ring; no raw EEG is saved or transmitted.
This is acquisition plumbing, **not** proof of signal quality or memory decode.
"""

from __future__ import annotations

import math
import uuid

from .muse2 import (
    AcquisitionError,
    BrainFlowBindings,
    CHANNELS,
    EXPECTED_NUM_ROWS,
    EXPECTED_ROWS,
    EXPECTED_TIMESTAMP_ROW,
    SAMPLE_RATE_HZ,
    Muse2CaptureSettings,
    _default_bindings,
    _validated_descriptor,
)
from .waveform import RawEEGFrame, RawEEGStreamSpec, StreamFormatError, StreamQC


RING_BUFFER_SAMPLES = 4096  # ~16 seconds at 256 Hz; never use BrainFlow's huge default.
CONNECT_TIMEOUT_SECONDS = 8  # BrainFlow discovery / connection timeout, not a thread kill.


class LiveMuse2:
    """One owner, one consented Bluetooth session, repeated draining polls.

    `first_unix_timestamp_s + frame.time_s` reconstructs a device-reported
    Unix timestamp. It does *not* precisely calibrate audio or cue-onset time.
    """

    def __init__(self, serial_number: str = "", mac_address: str = "",
                 consent: bool = False, bindings: BrainFlowBindings | None = None) -> None:
        # Reuse the static opt-in capture contract, including control character
        # rejection, without opening a device or loading optional dependencies.
        Muse2CaptureSettings(seconds=1, consent=consent,
                             serial_number=serial_number, mac_address=mac_address)
        self.serial_number = serial_number
        self.mac_address = mac_address
        self._consent = consent
        self._bindings = bindings
        self._board = None
        self._prepared = False
        self._started = False
        self.first_unix_timestamp_s: float | None = None
        self.last_unix_timestamp_s: float | None = None
        self.timestamp_gap_intervals = 0
        self.samples_seen = 0
        self.spec: RawEEGStreamSpec | None = None
        self._qc: StreamQC | None = None

    @property
    def connected(self) -> bool:
        """True only while the Muse stream was successfully started."""
        return self._started

    def connect(self) -> None:
        if not self._consent:
            raise PermissionError("explicit consent required before reading personal EEG")
        if self._board is not None:
            raise AcquisitionError("Muse 2 stream is already open")

        api = self._bindings if self._bindings is not None else _default_bindings()
        try:
            board_id, _ = _validated_descriptor(api)
            params = api.input_params()
            params.mac_address = self.mac_address
            params.serial_number = self.serial_number
            params.other_info = "p21"  # Four EEG channels, plus unconsumed IMU rows.
            params.timeout = CONNECT_TIMEOUT_SECONDS
            board = api.board_shim(board_id, params)
        except AcquisitionError:
            raise
        except Exception as exc:
            raise AcquisitionError("could not initialize Muse 2 session") from exc

        self._board = board
        self.spec = RawEEGStreamSpec(
            source_kind="DEVICE", stream_id=f"muse2-{uuid.uuid4().hex}",
            sample_rate_hz=SAMPLE_RATE_HZ, channel_names=CHANNELS,
            clock_domain="brainflow_unix_timestamp_relative_s",
        )
        self._qc = StreamQC(self.spec)
        self.first_unix_timestamp_s = None
        self.last_unix_timestamp_s = None
        self.timestamp_gap_intervals = 0
        self.samples_seen = 0
        try:
            board.prepare_session()
            self._prepared = True
            board.start_stream(RING_BUFFER_SAMPLES)
            self._started = True
        except Exception as exc:
            # Some BrainFlow failures occur after the underlying BLE resource
            # is partially allocated. Attempt release even when prepare fails.
            try:
                board.release_session()
            except Exception:
                pass
            self._board = None
            self._prepared = False
            self._started = False
            raise AcquisitionError("Muse 2 connection or streaming failed") from exc

    def poll(self) -> tuple[RawEEGFrame, ...]:
        """Drain new readings once; reject invalid batches and close on failure.

        A zero-sample drain is normal. Sequential local indices are *not*
        evidence of native BLE packet continuity; timestamp gaps are counted.
        """
        if not self._started or self._board is None or self._qc is None:
            raise AcquisitionError("connect the Muse 2 before polling")
        try:
            raw = self._board.get_board_data()
            if len(raw) != EXPECTED_NUM_ROWS:
                raise AcquisitionError("unexpected number of BrainFlow rows")
            n = len(raw[EXPECTED_TIMESTAMP_ROW])
            if n > RING_BUFFER_SAMPLES:
                raise AcquisitionError("oversized BrainFlow batch")
            if any(len(row) != n for row in raw):
                raise AcquisitionError("unequal BrainFlow row lengths")
            if n == 0:
                return ()

            first = self.first_unix_timestamp_s
            previous = self.last_unix_timestamp_s
            next_frames: list[RawEEGFrame] = []
            next_gaps = 0
            for i in range(n):
                try:
                    epoch = float(raw[EXPECTED_TIMESTAMP_ROW][i])
                    values = tuple(float(raw[row][i]) for row in EXPECTED_ROWS)
                except (ValueError, TypeError, IndexError, OverflowError) as exc:
                    raise AcquisitionError(f"unreadable BrainFlow EEG sample {i}") from exc
                if not math.isfinite(epoch) or epoch < 1_000_000_000:
                    raise AcquisitionError("invalid BrainFlow Unix timestamp")
                if previous is not None and epoch <= previous:
                    raise AcquisitionError("duplicate or backwards BrainFlow timestamp")
                if previous is not None and epoch - previous > 1.5 / SAMPLE_RATE_HZ:
                    next_gaps += 1
                if first is None:
                    first = epoch
                frame = RawEEGFrame(
                    self.samples_seen + i, epoch - first, values)
                # Validate all values before exposing any portion of the batch.
                if (not all(math.isfinite(v) for v in values)
                        or frame.time_s < 0):
                    raise AcquisitionError(f"unsafe BrainFlow EEG sample {i}")
                next_frames.append(frame)
                previous = epoch

            # The QC object retains only scalar aggregates, not EEG arrays.
            for frame in next_frames:
                self._qc.push(frame)
            self.first_unix_timestamp_s = first
            self.last_unix_timestamp_s = previous
            self.samples_seen += len(next_frames)
            self.timestamp_gap_intervals += next_gaps
            return tuple(next_frames)
        except Exception as exc:
            # Bad provenance or a BLE failure must not leave a half-valid live
            # source. Preserve the original error even if cleanup also fails.
            try:
                self.close()
            except Exception:
                pass
            if isinstance(exc, AcquisitionError):
                raise
            if isinstance(exc, StreamFormatError):
                raise AcquisitionError(f"invalid streamed EEG: {exc}") from exc
            raise AcquisitionError("Muse 2 streaming poll failed") from exc

    def close(self) -> None:
        """Idempotently stop and release a session, even after poll failures."""
        board = self._board
        if board is None:
            return
        started = self._started
        prepared = self._prepared
        self._board = None
        self._started = False
        self._prepared = False
        stop_error = None
        try:
            if started:
                board.stop_stream()
        except Exception as exc:
            stop_error = exc
        finally:
            try:
                if prepared:
                    board.release_session()
            except Exception as exc:
                if stop_error is None:
                    stop_error = exc
        if stop_error is not None:
            raise AcquisitionError("could not fully stop or release Muse 2") from stop_error


__all__ = ["LiveMuse2", "RING_BUFFER_SAMPLES", "CONNECT_TIMEOUT_SECONDS"]
