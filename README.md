# MemStack — neural-memory evidence research brief

**A research framework for studying whether neural observations can contribute to consent-governed, verifiable records of human memory.** MemStack defines an evidence problem and a candidate evaluation path; it is **not** a deployed brain–computer interface, an installable library, a memory-backup product, or a validated clinical intervention.

## What is available

| Surface | Current state | What it establishes |
| --- | --- | --- |
| Problem statement and evidence rules | This README on `main` | A reviewable research framing, not experimental results |
| Evidence/architecture/experiment/review documents | [Draft research PR #1](https://github.com/thebrazenbeard/memstack/pull/1), **not merged into `main`** | Proposed documents for scrutiny, not released implementation |
| Neural acquisition, decoding, storage service, or re-stimulation | **Not present on `main`** | No operational or safety qualification |
| Test suite, datasets, models, CLI, API, or installer | **Not present on `main`** | No executable product acceptance tests |

This distinction is part of the product contract: **a research design can be reusable without its proposed technology already existing**.

## Research question

Can ethically acquired neural signals add independently measurable information to a person's own memory record beyond ordinary diaries, images, audio, and other non-neural evidence?

The proposed approach must not assume that recording neural activity means recording the associated experience. Any decoded scene, word, or remembered state is a **model output with uncertainty**, not a recovered original memory by definition.

## Evidence types must stay separate

| Evidence type | Example | Limit |
| --- | --- | --- |
| Neural observation | Time-bounded EEG, intracranial, or imaging measurement from a consented study | A signal sample does not on its own specify what happened |
| Participant account | A person's own report of recall or experience | It records a report, not independent event truth |
| External event record | A contemporaneous photo, audio clip, or document | It may corroborate parts of an event, not the person's subjective experience |
| Decoder estimate | A predicted concept, feature, or image from a bounded model | Must preserve model version, uncertainty, training domain, and comparison controls |
| Generated reconstruction | AI-produced words, imagery, or narration | A hypothesis or visualization, never silently promoted to ground truth |

Provenance should bind observation time, collection method, participant consent scope, access controls, source identity, and transformations. A retrieval interface must preserve these distinctions instead of flattening them into a single “memory” object.

## Candidate development and evaluation path

These are **research proposals**, not implemented MemStack features:

1. **Define the scope.** Start with one falsifiable, consented task and a precise target (for example, a constrained recall classification) rather than “back up a life.”
2. **Preserve raw and derived data separately.** Keep acquisition metadata and versioned transformations; treat any decoder output as a derivative with its own provenance.
3. **Compare against non-neural controls.** Establish whether neural input adds reliable information over participants' reports and ordinary event records.
4. **Measure error and abstention.** Report false identifications, coverage, uncertainty calibration, distribution shifts, and subject-specific variation.
5. **Evaluate privacy and withdrawal.** Limit collection and retention to exact consent, audit access, and define how collection can stop and how retained derivatives are handled.
6. **Submit to adversarial review.** Test alternative explanations and negative controls before making claims about autobiographical memory reconstruction.

The eventual experimental protocol would require independent ethics, regulatory, device, security, and participant-safety review as applicable. Nothing in this repository grants authority to enroll people, collect neural data, stimulate a brain, or deploy a clinical or consumer device.

## Research starting points

The following publications are **reading leads**, not MemStack validation receipts. A later evidence register should inspect their actual experimental populations, tasks, measurement modalities, controls, limitations, and replication before promoting particular conclusions:

- [Chadwick et al. (2010): constrained identification of recalled events](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849012/)
- [Hampson et al. (2018): hippocampal stimulation and memory encoding](https://pmc.ncbi.nlm.nih.gov/articles/PMC6576290/)
- [Tang et al. (2023): semantic reconstruction from fMRI](https://www.nature.com/articles/s41593-023-01304-9)
- [Anderson et al. (2025): autobiographical imagery decoding research](https://www.nature.com/articles/s41467-025-65541-1)
- [Ding et al. (2025–2026): intracranial concept decoding preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC12236671/)

## Explicit exclusions

- No evidence that a complete autobiographical life or subjective experience can be copied into a file, faithfully replayed, or written back into a brain.
- No participant data, neural recordings, decoding weights, benchmark results, or demonstrated benefit in this repository's current `main`.
- No claim that model agreement, plausible generated imagery, or a review note provides independent scientific verification.
- No claim that the [T’Kal-in-ket-inspired adversarial review protocol](https://github.com/thebrazenbeard/t-kal-in-ket/blob/main/docs/PROTOCOL.md) has produced an authenticated external-model quorum or formal clinical verdict for MemStack.

**License status:** No root software or content license is present in this `main` snapshot. Public visibility allows inspection, but must not be taken as an express grant of redistribution, commercial, or dataset-use rights. Obtain permission and review third-party paper licenses before reusing materials.
