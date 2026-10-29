# MemStack

**Research status: source-backed concept and experimental design — not an installed BCI, clinical device, or demonstrated human-memory backup.**

MemStack investigates whether brain–computer interfaces can record, index, and eventually reconstruct verifiable aspects of human autobiographical memory in digital storage.

## Current answer (2026-10-29)

- **Established:** BCIs can digitally record neural signals associated with memory and can identify limited remembered content or states in constrained human experiments.
- **Research target:** Consent-controlled, provenance-aware neural memory indexing with measurable benefits beyond non-neural records.
- **Not established:** Copying any person's complete personal experience to a file, replaying it faithfully, or writing an archived experience back into a brain.

See the versioned [evidence register](docs/EVIDENCE_REGISTER_20261029.md), [architecture](docs/ARCHITECTURE_V0.md), [experiment plan](docs/EXPERIMENTS_V0.md), and [T’Kal-in-ket adversarial review](reviews/TKIK_BCI_MEMORY_20261029.md) as they are admitted.

## Executable public-metadata prototype

MemStack now contains a **metadata-only** parser for the [Essex EEG Movie Memory dataset](https://github.com/OpenNeuroDatasets/ds006142/tree/6af022b2d66e98573bf4fc8ffc7e0d2a02c66f65) and a pinned whole-dataset audit runner. These separate first-watch EEG crop times from outcome labels, reject unknown event schemas, and namespace trial identity across recordings. Neither tool loads the neural EDF binary or decodes a memory.

```sh
python -m unittest discover -s tests -v
python -m memstack.essex /path/to/events.tsv /path/to/channels.tsv --source-ref sub-001/eeg/sub-001_task-MovieMemory_events.tsv
python -m scripts.audit_essex_metadata --output reports/essex_metadata_audit.json
```

The final command downloads only small version-pinned public TSV metadata for 27 subjects, verifies expected trial counts, and writes a source-hash report. The report is a **check**, not a trained EEG benchmark. The [Wave 3–5 hostile review](reviews/WAVES_3_TO_5_20261029.md) and [governance design](docs/GOVERNANCE_CONTRACT_V0.md) identify what remains before human data, BCI processing or claims of partial-content extraction could be justified.

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
