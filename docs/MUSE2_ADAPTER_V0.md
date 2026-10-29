# Muse 2 ↔ Lappy BrainFlow adapter v0

**Code is implemented and unit-tested with a fake board. On 2026-10-29, a real BrainFlow installation and direct Muse 2 BLE acquisition were observed on Lappy in short, consented, in-memory sessions. These observations do not independently verify calibration, electrode contact quality, signal origins, or memory decoding.**

This adapter reads *EEG only* from a **Muse 2 directly connected by Bluetooth Low Energy to Lappy**. A phone or Tailscale gateway is not needed for that local link. Tailscale can be considered later for an authenticated computer-to-computer connection, but a Tailscale-connected phone does not automatically expose its Bluetooth peripherals.

## Modes

Run locally from the MemStack repository:

```powershell
# Safe, offline, dependency-free inspection; no BLE discovery or EEG capture
python -m memstack.muse2

# Only when the headset is nearby, and after consciously authorizing the capture:
python -m pip install brainflow
python -m memstack.muse2 --capture --consent --seconds 5

# Optional if BrainFlow cannot auto-discover your Muse:
python -m memstack.muse2 --capture --consent --seconds 5 --serial-number MUSE_DEVICE_NAME
```

`brainflow` is an **optional dependency**. Version 5.23.0 was installed into an isolated Python environment on Lappy for the local pilot, but this repository does not bundle it. Check the active interpreter, installed BrainFlow version, Windows build and Bluetooth availability before each session. BrainFlow documents Windows 10 build 19041 or later for its Muse 2 implementation. The adapter does not change Windows settings or install drivers. A directly connected Muse does not require a phone-mediated Tailscale bridge.

The command records for at most **30 seconds** and prints only a nonclinical signal/timing summary. By design, it neither uploads, saves nor logs personal raw EEG to disk. Live samples exist in the Python process only and are not an encrypted-retention solution. It also does not stream EEG over the network.

## Actual data mapping

- Optional backend: `brainflow.board_shim.BoardShim`, `BoardIds.MUSE_2_BOARD`, `BrainFlowInputParams`.
- Required preset: `p21`, four EEG channels plus IMU. Reads BrainFlow's **default EEG preset**, not its auxiliary IMU or ancillary PPG presets.
- Expected descriptor: board `Muse2` / 256 Hz; ordered EEG rows `[1,2,3,4]` named `[TP9, AF7, AF8, TP10]`, BrainFlow Unix timestamp row `6`, 8 total default-preset rows. A changed descriptor is rejected before connection instead of guessed.
- EEG values are passed through as BrainFlow-provided microvolt values, without calibration, artifact filtering, interpolation, resampling, or transformations. BrainFlow documents microvolts for EXG *wherever possible*; real Muse 2 conversion should still be independently checked during the hardware QA gate.
- BrainFlow's source Unix timestamp row is retained in the acquisition summary for the first sample and converted to **elapsed seconds from that first sample** in `RawEEGFrame.time_s`. Nonfinite, duplicated, decreasing, or implausibly low (non-epoch) timestamps are rejected.
- `sample_index` is **adapter-assigned and sequential**. Large source-timestamp gaps (`>1.5/256 sec`) are reported as *suspected timing discontinuities*, not proof of BLE packet loss. `missing_index_slots=0` is therefore **not** a successful BLE-loss audit. Native sample/packet counters and hardware timing remain unqualified.
- The `source_kind=DEVICE` flag is a claimed acquisition route, **not independent attestation**. The QC summary retains `hardware_acquisition_verified=false` and `memory_decoding_performed=false` until an independently verified evidence path exists.
- Stream identifiers are temporary random identifiers, not names or hardware addresses.

## Permission and data boundaries

- No capture without explicit `--capture --consent`; importing the module and running its default mode never starts Bluetooth.
- Each call attempts one short bounded session; startup, streaming and buffer-drain errors release the session where it was successfully prepared.
- No direct EEG file export in this v0 command. Do **not** add a plain JSONL file option for private EEG until protected storage, consent and deletion policies are implemented and tested.
- No face/identity inference, medical diagnosis, psychological evaluation, recollection, memory extraction or stimulation.
- No claim that timing gaps, noise, blink/eye artifacts or signal reference have been calibrated. These require a real signal-quality study with repeated eyes-open/closed and blink/jaw controls.

## Verification and remaining gates

```sh
python -m unittest discover -s tests -v
python -m memstack.muse2
```

Unit tests use a **fake BrainFlow board boundary**, not a real Bluetooth connection. They independently challenge wrong row layouts, wrong sample rate, malformed EEG/Unix timestamps, gap diagnosis, startup and drain failure cleanup, interrupted capture, and the consent precondition. Separate operator-led runtime observations confirmed a BLE connection and samples on four BrainFlow EEG rows, but do not establish clinical or scientific signal validity.

Before treating a session as real *qualified* EEG: independently verify headset firmware/model, BrainFlow descriptor and data provenance, in-person participant consent, channel timing/unit calibration, electrode/contact quality, source packet loss accounting, and private retention. Recording to a private secure medium is **not part of this version**.

Primary references:

- [BrainFlow: Muse 2 supported-board configuration](https://brainflow.readthedocs.io/en/stable/SupportedBoards.html#muse-2)
- [BrainFlow: timestamp/unit conventions](https://brainflow.readthedocs.io/en/stable/DataFormatDesc.html)
- [BrainFlow: Python acquisition examples](https://brainflow.readthedocs.io/en/stable/Examples.html#python-get-data-from-a-board)
- [BrainFlow source: Muse 2 descriptor and EEG row order](https://github.com/brainflow-dev/brainflow/blob/master/src/board_controller/brainflow_boards.cpp)

Also see [the broader Muse pilot](MUSE2_PILOT_V0.md) and [raw EEG ingest contract](SIGNAL_INGEST_V0.md).
