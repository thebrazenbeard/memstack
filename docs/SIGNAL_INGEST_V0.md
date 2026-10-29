# MemStack signal-ingest foundation v0

**Status: CODE + UNIT TESTS, HARDWARE-UNVERIFIED.** This is a measurement and replay contract, not a BCI connection, validated clinical pipeline, neural-memory decoder or external-memory backup.

## Why this precedes memory research

The first falsifiable milestone is to read and preserve a time-indexed signal **without changing what was measured**. A memory experiment cannot recover from unlabeled or corrupted channels, undetected recording gaps, disputed time bases or accidental target-label leakage. A classifier can have impressive accuracy while using only time, prompt identity, eye movement or an answer-key trigger.

## Minimal code

- `memstack/waveform.py`: a hardware-independent `RawEEGStreamSpec`, `RawEEGFrame`, monotonicity/continuity validator, deterministic synthetic 10-Hz signal source and strict JSONL replay.
- `tests/test_waveform.py`: valid synthetic frames, four-channel mapping, missing index slots, malformed frames, duplicate/out-of-order timestamps, bad units, roundtrip and injected-label rejection.
- `python -m memstack.waveform --seconds 2`: prints a compact **synthetic** four-channel quality summary; no Bluetooth, EEG hardware, patient information or machine-learning inference is accessed.

### Frame contract

```json
{
  "kind": "frame",
  "sample_index": 17,
  "time_s": 0.06640625,
  "eeg_uv": [1.0, 2.0, 3.0, 4.0]
}
```

The preceding header separately declares schema version, `source_kind` (`SYNTHETIC`, `DEVICE` or `REPLAY`), stream ID, sampling rate, ordered EEG channel names, clock domain and microvolt units. **Declared device origin is not attested device provenance.** Unexpected fields (including labels, film ID, recognition outcomes or cue names) are rejected from this format.

The `sample_index` is *adapter-provided*. The validator reports missing **index slots**, not physical BLE packet loss: an adapter that reassigns consecutive indices after lost packets can conceal loss. Future device adapters must retain native counters or independently verify delivery/clock continuity. The observed sample rate derived from indices and elapsed time is a diagnostic, not proof that the actual ADC sampled at that rate.

### What is not allowed

- No stimulus or eventual-response label in raw neural frame fields. Alignment to experimental events lives in a separate quarantined record, not in EEG predictor values.
- No automatic promotion of a claimed `DEVICE` source into **verified** hardware data merely because a string says so.
- No bandpower interpretation, calibration, artifact cleaning, zero-phase filtering or upsampling silently performed by the raw validator.
- No use of the plain JSONL format for private human EEG at rest without an authorized encrypted-storage design. Personal raw signals and their derived models must not be committed to GitHub.
- No inference from synthetic 10-Hz sine waves that a person has a particular brain state, memory, diagnosis or consciousness state.

## Independent acceptance before Muse 2 integration

1. Detect a real BLE Muse 2 connection and obtain actual firmware/library identity on Lappy; manufacturer and BrainFlow source documentation establish **support**, not this host's functionality.
2. Cross-check raw device EEG channels explicitly against `TP9`, `AF7`, `AF8`, `TP10` and the actual BrainFlow board configuration. Keep auxiliary, accelerometer, gyro, PPG and stimulus markers in distinct channels/streams.
3. Preserve source-native timestamps/counters, verify jitter, discontinuities, contact quality, reference, packet loss and ADC-to-microvolt conversion under a test recording. No clock resampling without provenance.
4. Compare repeated eyes-open/closed and blink/jaw controls, with session-level artifact exclusions. This establishes signal viability, **not** a recovered memory.
5. Crop pre-response windows and test a post-event synthetic impulse before applying any noncausal filter. Prevent answer-key event fields from entering training features.
6. Only after that, preregister within-person memory-*related* prediction experiments against non-neural and shuffled controls, using session-disjoint reserved trials.

See the [Muse 2 pilot](MUSE2_PILOT_V0.md), [Essex experiment protocol](EXPERIMENTS_V0.md), and [governance plan](GOVERNANCE_CONTRACT_V0.md). The software state reported here is a strict contract prototype; real acquisition, usable signal, raw-to-feature provenance, model generalization and clinical effectiveness remain **UNKNOWN**.

The optional [Muse 2 BrainFlow adapter v0](MUSE2_ADAPTER_V0.md) now maps the documented four EEG rows and source Unix timestamp to this schema with an explicit in-memory capture gate. Its unit tests use a fake backend; this is **not** proof that the adapter has communicated with physical hardware. Native packet loss and true EEG units still need independent on-device qualification.
