"""Opt-in Muse 2 / BrainFlow adapter for *raw* four-channel EEG only.

Nothing connects on import or on the default CLI invocation. Real recording
requires explicit consent, a working Muse 2 and an optional BrainFlow install.
No raw private EEG is saved to disk or transmitted by this module.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import uuid
from dataclasses import dataclass
from typing import Callable

from .waveform import RawEEGFrame, RawEEGStreamSpec, StreamFormatError, StreamQC


CHANNELS = ("TP9", "AF7", "AF8", "TP10")
SAMPLE_RATE_HZ = 256
MAX_SECONDS = 30.0
EXPECTED_ROWS = (1, 2, 3, 4)
EXPECTED_TIMESTAMP_ROW = 6
EXPECTED_NUM_ROWS = 8


class AcquisitionError(RuntimeError):
    """The readout cannot safely be admitted as four-channel Muse 2 EEG."""


@dataclass(frozen=True)
class Muse2CaptureSettings:
    seconds: float = 5.0
    consent: bool = False
    mac_address: str = ""
    serial_number: str = ""

    def __post_init__(self) -> None:
        if (isinstance(self.seconds, bool) or not isinstance(self.seconds, (int, float))
                or not math.isfinite(self.seconds) or not 0 < self.seconds <= MAX_SECONDS):
            raise ValueError(f"seconds must be in (0, {MAX_SECONDS}]")
        if not isinstance(self.consent, bool):
            raise ValueError("consent must be an explicit boolean")
        for field in ("mac_address", "serial_number"):
            value = getattr(self, field)
            if (not isinstance(value, str) or (value and not value.strip())
                    or any(ord(c) < 32 or ord(c) == 127 for c in value)):
                raise ValueError(f"invalid {field}")


@dataclass(frozen=True)
class BrainFlowBindings:
    """Injectable BrainFlow API boundary for offline contract testing."""

    board_shim: type
    board_ids: type
    input_params: type


@dataclass(frozen=True)
class Muse2Acquisition:
    spec: RawEEGStreamSpec
    frames: tuple[RawEEGFrame, ...]
    summary: dict


def inspect_plan() -> dict:
    """Safe, dependency-free preflight; this does not scan or connect Bluetooth."""
    return {
        "adapter": "brainflow_muse2_p21",
        "eeg_channels": list(CHANNELS),
        "nominal_sample_rate_hz": SAMPLE_RATE_HZ,
        "brainflow_required_for_capture": True,
        "consent_required_for_capture": True,
        "raw_eeg_disk_storage_enabled": False,
        "device_connected": False,
        "recording_started": False,
        "hardware_acquisition_verified": False,
        "memory_decoding_performed": False,
    }


def _default_bindings() -> BrainFlowBindings:
    try:
        from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
    except ImportError as exc:
        raise AcquisitionError(
            "BrainFlow is not installed. Install the optional 'brainflow' package "
            "on Lappy before attempting a consented Muse 2 recording."
        ) from exc
    return BrainFlowBindings(BoardShim, BoardIds, BrainFlowInputParams)


def _validated_descriptor(bindings: BrainFlowBindings) -> tuple[int, dict]:
    board_id = bindings.board_ids.MUSE_2_BOARD.value
    desc = bindings.board_shim.get_board_descr(board_id)
    if not isinstance(desc, dict):
        raise AcquisitionError("BrainFlow board descriptor is not an object")
    if (desc.get("name") != "Muse2"
            or desc.get("sampling_rate") != SAMPLE_RATE_HZ
            or desc.get("eeg_channels") != list(EXPECTED_ROWS)
            or desc.get("eeg_names") != ",".join(CHANNELS)
            or desc.get("timestamp_channel") != EXPECTED_TIMESTAMP_ROW
            or desc.get("num_rows") != EXPECTED_NUM_ROWS):
        raise AcquisitionError("unexpected Muse 2 layout or sampling rate; no connection attempted")
    return board_id, desc


def _convert_matrix(raw: object, *, stream_id: str) -> Muse2Acquisition:
    """Map BrainFlow's rows x samples array, retaining its reported timestamps.

    Source packet counters are not interpreted: BrainFlow's packet-number row
    does not by itself establish a per-sample loss counter for this adapter.
    """
    try:
        if len(raw) != EXPECTED_NUM_ROWS:
            raise AcquisitionError("unexpected number of BrainFlow rows")
        n_samples = len(raw[EXPECTED_TIMESTAMP_ROW])
        if not 0 < n_samples <= int(MAX_SECONDS * SAMPLE_RATE_HZ * 2):
            raise AcquisitionError("empty or oversized BrainFlow EEG result")
        if any(len(row) != n_samples for row in raw):
            raise AcquisitionError("unequal BrainFlow row lengths")
    except (TypeError, IndexError) as exc:
        raise AcquisitionError("malformed BrainFlow data array") from exc

    first_epoch = float(raw[EXPECTED_TIMESTAMP_ROW][0])
    # BrainFlow documents Unix seconds for the timestamp row. Reject zero,
    # relative ticks and obviously malformed epochs rather than guessing.
    if not math.isfinite(first_epoch) or first_epoch < 1_000_000_000:
        raise AcquisitionError("invalid BrainFlow Unix timestamp")

    spec = RawEEGStreamSpec(
        source_kind="DEVICE", stream_id=stream_id,
        sample_rate_hz=SAMPLE_RATE_HZ, channel_names=CHANNELS,
        clock_domain="brainflow_unix_timestamp_relative_s",
    )
    qc = StreamQC(spec)
    frames = []
    gap_intervals = 0
    last_epoch = None
    for i in range(n_samples):
        try:
            epoch = float(raw[EXPECTED_TIMESTAMP_ROW][i])
            values = tuple(float(raw[row][i]) for row in EXPECTED_ROWS)
        except (TypeError, ValueError, IndexError, OverflowError) as exc:
            raise AcquisitionError(f"unreadable BrainFlow EEG at sample {i}") from exc
        if not math.isfinite(epoch) or epoch < first_epoch:
            raise AcquisitionError("invalid, backward or nonfinite BrainFlow timestamp")
        if last_epoch is not None and epoch - last_epoch > 1.5 / SAMPLE_RATE_HZ:
            gap_intervals += 1
        frame = RawEEGFrame(i, epoch - first_epoch, values)
        try:
            qc.push(frame)
        except StreamFormatError as exc:
            raise AcquisitionError(f"unsafe BrainFlow sample {i}: {exc}") from exc
        frames.append(frame)
        last_epoch = epoch
    summary = qc.summary()
    summary.update({
        "adapter": "brainflow_muse2_p21",
        "brainflow_unix_first_timestamp_s": first_epoch,
        "source_timestamp_gap_intervals": gap_intervals,
        "native_packet_loss_verified": False,
        "raw_eeg_disk_storage_enabled": False,
    })
    return Muse2Acquisition(spec, tuple(frames), summary)


def acquire_muse2(
    settings: Muse2CaptureSettings,
    *,
    bindings: BrainFlowBindings | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> Muse2Acquisition:
    """Opt-in, bounded in-memory recording with cleanup even on failures.

    *No* data leaves process memory via this function. The adapter does not
    claim packet-loss verification, signal contact quality, or human memory.
    """
    if not settings.consent:
        raise PermissionError("explicit consent required before reading personal EEG")
    api = bindings if bindings is not None else _default_bindings()
    board_id, _ = _validated_descriptor(api)
    params = api.input_params()
    params.mac_address = settings.mac_address
    params.serial_number = settings.serial_number
    params.other_info = "p21"  # 4 EEG + IMU; read only the default EEG preset.

    board = api.board_shim(board_id, params)
    prepared = False
    started = False
    try:
        board.prepare_session()
        prepared = True
        board.start_stream()
        started = True
        sleeper(settings.seconds)
        board.stop_stream()
        started = False
        raw = board.get_board_data()
    finally:
        try:
            if started:
                board.stop_stream()
        finally:
            if prepared:
                board.release_session()

    # Local ephemeral identifier; neither a user name nor a hardware address.
    return _convert_matrix(raw, stream_id=f"muse2-{uuid.uuid4().hex}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Muse 2 adapter: offline inspect by default")
    parser.add_argument("--capture", action="store_true", help="attempt an actual Muse 2 BLE recording")
    parser.add_argument("--consent", action="store_true", help="confirm you consent to in-memory EEG capture")
    parser.add_argument("--seconds", type=float, default=5.0, help="bounded recording duration (max 30s)")
    parser.add_argument("--mac-address", default="", help="optional Muse BLE MAC address")
    parser.add_argument("--serial-number", default="", help="optional Muse BLE device name")
    args = parser.parse_args()
    if not args.capture:
        if args.consent:
            parser.error("--consent has no effect without --capture")
        print(json.dumps(inspect_plan(), indent=2))
        return 0
    try:
        recording = acquire_muse2(Muse2CaptureSettings(
            seconds=args.seconds, consent=args.consent,
            mac_address=args.mac_address, serial_number=args.serial_number))
    except (AcquisitionError, PermissionError, ValueError) as exc:
        parser.exit(2, f"Muse 2 acquisition unavailable: {exc}\n")
    print(json.dumps(recording.summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
