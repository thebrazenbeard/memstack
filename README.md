# MemStack

**Research status: source-backed concept, research prototype, and local Muse 2 acquisition pilot — not a clinical device or demonstrated human-memory backup.**

MemStack investigates whether brain–computer interfaces can record, index, and eventually reconstruct verifiable aspects of human autobiographical memory in digital storage.

## Current answer (2026-10-29)

- **Established:** BCIs can digitally record neural signals associated with memory and can identify limited remembered content or states in constrained human experiments.
- **Research target:** Consent-controlled, provenance-aware neural memory indexing with measurable benefits beyond non-neural records.
- **Not established:** Copying any person's complete personal experience to a file, replaying it faithfully, or writing an archived experience back into a brain.

The first four research documents are reviewable in [draft PR #1](https://github.com/thebrazenbeard/memstack/pull/1): an evidence register, architecture, experiment plan, and T’Kal-in-ket-style adversarial review. They are **not yet merged into main**.

## Executable public-metadata prototype

MemStack now contains a **metadata-only** parser for the [Essex EEG Movie Memory dataset](https://github.com/OpenNeuroDatasets/ds006142/tree/6af022b2d66e98573bf4fc8ffc7e0d2a02c66f65) and a pinned whole-dataset audit runner. These separate first-watch EEG crop times from outcome labels, reject unknown event schemas, and namespace trial identity across recordings. Neither tool loads the neural EDF binary or decodes a memory.

```sh
python -m unittest discover -s tests -v
python -m memstack.essex /path/to/events.tsv /path/to/channels.tsv --source-ref sub-001/eeg/sub-001_task-MovieMemory_events.tsv
python -m scripts.audit_essex_metadata --output reports/essex_metadata_audit.json
```

The final command downloads only small version-pinned public TSV metadata for 27 subjects, verifies expected trial counts, and writes a source-hash report. The report is a **check**, not a trained EEG benchmark. The [Wave 3–5 hostile review](reviews/WAVES_3_TO_5_20261029.md) and [governance design](docs/GOVERNANCE_CONTRACT_V0.md) identify what remains before human data, BCI processing or claims of partial-content extraction could be justified.

### Personal hardware feasibility: Muse 2

Patrick reports owning a Muse 2. The source-backed [Muse 2 pilot plan](docs/MUSE2_PILOT_V0.md) separates a four-channel, 256-Hz local signal-quality/recognition research path from the 64-channel Essex public benchmark. On October 29, 2026, BrainFlow was installed on the user's Windows host (Lappy); a directly connected Muse 2 was observed returning live four-channel readings in short, consented, in-memory sessions. **This does not independently establish electrode quality, calibrated brain activity, neural source authenticity, or memory decoding.** The device is not a whole-memory reader.

### Brainwave reading foundation (hardware-independent)

The [raw-signal ingest contract](docs/SIGNAL_INGEST_V0.md) now has an executable deterministic four-channel waveform source, strict timing/channel validation, gap accounting and raw-sample replay. Test it without Bluetooth or human data:

```sh
python -m memstack.waveform --seconds 2
python -m unittest discover -s tests -q
```

`SYNTHETIC` never means a live brainwave; the result explicitly states hardware acquisition and memory decoding are not verified. Device adapters and private encrypted retention are separate future gates.

The initial optional [Muse 2 → Lappy BrainFlow adapter](docs/MUSE2_ADAPTER_V0.md) is now implemented with hardware-free tests. `python -m memstack.muse2` safely inspects the offline plan; an actual short in-memory BLE recording requires BrainFlow, a compatible nearby headset, and explicit `--capture --consent`. The local trial above does not authorize public disclosure of raw personal EEG, and none belongs in this repository.

### Windows monitor prototype

The optional [MemStack Monitor v0.1](docs/MONITOR_V01.md) adds a local, consent-gated four-channel display, bounded live acquisition, basic artifact warnings, and a self-contained eyes-open/eyes-closed protocol with audible instructions. Unlike a memory decoder, this is primarily a **signal-quality and experimental-timing tool**. It neither uploads nor saves raw EEG, and auditory prompts have scheduled markers rather than independently measured sound-onset times.

On Windows in the MemStack directory, after installing the optional `brainflow` dependency:

```powershell
.\.venv\Scripts\python.exe -m memstack.monitor
```

Or double-click `scripts\launch_monitor.cmd` from File Explorer if the repository's `.venv` is already provisioned.

Launching the window alone does not connect to the headset or read neural data. Start requires a visible consent action. See the monitor guide for usage, privacy limits, and known omissions.

## Non-negotiable distinctions

A neural voltage recording, a participant's report, a sensor recording of an event, a statistical decoder output, and AI-generated imagery are **different evidence classes**. No one class silently becomes a verified memory of the event. Neural recordings require specific consent, protected storage, and a right to stop participation.

## Initial source anchors

- [Chadwick et al. (2010): constrained identification of recalled events](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849012/)
- [Hampson et al. (2018): hippocampal stimulation-assisted memory encoding](https://pmc.ncbi.nlm.nih.gov/articles/PMC6576290/)
- [Tang et al. (2023): semantic language reconstruction from fMRI](https://www.nature.com/articles/s41593-023-01304-9)
- [Anderson et al. (2025): autobiographical imagery feature decoding](https://www.nature.com/articles/s41467-025-65541-1)
- [Ding et al. (2025–2026): concept decoding in intracranial recordings (preprint)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12236671/)

## Review scope

Initial research began 2026-10-29 with six native specialist subagents, followed by a second wave of six. Waves 3–5 added 18 role-specialist native reviewer executions and a working metadata prototype. The 13 BT2 identities were represented as **role prompts**, not 13 independently deployed, qualified model instances. The reviews are *internal model research*, not independently authenticated external models or original wet-lab/clinical evidence.

The [T’Kal-in-ket protocol](https://github.com/thebrazenbeard/t-kal-in-ket/blob/main/docs/PROTOCOL.md) informs the challenge method. Its live remote quorum is not established here; a review note is not a machine-issued formal SUSTAIN verdict.

**Boundary:** No new human participants, neural capture, stimulation, device construction, deployment, or medical intervention has been performed or authorized by this document.
