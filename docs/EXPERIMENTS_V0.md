# MemStack experiment plan v0 — falsifiable neural memory indexing

**Status: PROPOSAL plus public metadata parser/tests. Small public event/channel TSVs were retrieved; no EDF neural binary, decoder training, human participant or BCI experiment has been conducted by this project.**

## The question that matters

Can neural recordings made during remembering contribute **previously unavailable, independently verified event-specific information** over and above prompts, event metadata, eye gaze, speech, external records and a generative model's priors?

We must separately measure:

- **Event truth:** what can be established happened from sealed independent evidence.
- **Recollection:** what the participant reports remembering at a given time.
- **Neural inference:** what the model predicts from the specified brain signals.
- **Reconstruction:** what a model generates, possibly using extra prior/context information.

A model that matches the participant's *report* may still misdescribe the actual event; a model that matches external video may have learned nothing from a memory.

## Phase A: public-data baselines (no implants)

### A1 — Recognition, practical EEG starter

- Source: [Essex EEG Movie Memory ds006142](https://github.com/OpenNeuroDatasets/ds006142/tree/6af022b2d66e98573bf4fc8ffc7e0d2a02c66f65), [2025 data paper](https://www.nature.com/articles/s41597-025-06203-1): 27 participants, 64-channel EEG, ~24 GB; dataset revision v1.0.2 pinned at `6af022b2d66e98573bf4fc8ffc7e0d2a02c66f65`.
- Task: predict reported recognition/memory strength during **viewing** of short movie clips, not spontaneous memory extraction.
- Guardrails: training/test split grouped by film identity; use first presentations and pre-response EEG only; clip familiarity and participant priors as non-neural baseline; compare across acquisition cohorts; shuffled and wrong-person signals.
- **Confirmed leakage hazard:** [sub-001 events](https://github.com/OpenNeuroDatasets/ds006142/blob/main/sub-001/eeg/sub-001_task-MovieMemory_events.tsv) encode later outcome in first-onset `trial_type` (`startOfRememberedClipFirstWatch`, etc.) and trigger `value`; `stim_file` reveals the film. The trigger channel and these fields, sample/onset timing, second-watch periods and later clicks are forbidden model inputs. Use them only in quarantined target/alignment tables. A grouped split needs a separately verified film-group mapping, not a guessed filename rule.
- Cohort selection differed between 2019 and 2024; report within- and cross-cohort results and distribution shifts separately. This dataset has no dedicated EOG channel or eye tracker, so eye-artifact audits cannot be represented as an independently measured gaze baseline.
- **Execution:** A strict metadata-only parser and 14 unit tests (including pinned audit tests) exist in `memstack/essex.py`, `scripts/audit_essex_metadata.py` and `tests/`. Real `sub-001` public TSV metadata yielded 152 first views (84 not recognized, 20 recognized, 48 remembered) and 64 EEG channels; **no neural binary or decoder was used**. Trial keys are qualified by declared source path and content hash. The declared source reference is not yet bound to an independently validated EDF acquisition.
- **Whole dataset metadata cross-check (model review, not yet independent local job readback):** A Wave-5 reviewer retrieved the exact upstream v1.0.2 events TSVs for all 27 subjects: 4,153 first views (2,212 not recognized, 515 recognized, 1,426 remembered), 1,941 second views, 6,094 clip endings. Subjects 012 and 019 had no `recognised` trials. The finite metadata audit script checks these counts against raw byte hashes; no EDF download occurs.
- **Frozen intended primary endpoint:** binary `recognised or remembered` versus `not_recognised`; paired, held-out **log-loss difference (context-only minus EEG+context)** on identical trials. Retain the three original categories for secondary analysis. Sub-001's majority-class three-way accuracy is 84/152 = 55.3%, not a 33.3% null.
- **Generalization gates:** separate subject-disjoint and independently mapped canonical-film-disjoint held-outs; joint disjoint holdout only if coverage permits. Pre-registered class-prior, context-only, EEG-only, EEG+context, wrong-trial, wrong-subject, grouped shuffling and artifact controls; partition-first preprocessing and cohort-stratified reporting.
- **Unresolved signal gate:** a feature named `eeg__Fp1__alpha` could still contain copied labels. Feature-name linting does not prove lineage; require raw EDF/BIDS channel reconciliation and an EEG-only allowlist, deliberate label-injection tests, filter-support/post-response impulse checks, and no unrestricted or automatically inferred trigger channels. No such signal-level verification has occurred.
- Claim if successful: EEG contributes to recognition prediction, **not** that a movie was copied from memory.

### A2 — Recalled content, fMRI benchmark

- Source: [FilmFestival ds004042 v1.0.1](https://openneuro.org/datasets/ds004042/versions/1.0.1), [data paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9727629/): 20 participants, ~39 GB, movie viewing and free spoken recall.
- Task: compare pre-registered scene/event semantic features predicted from fMRI with timed recall transcripts, while controlling common stimuli, cue information and participants' actual spoken responses.
- Caveat: speech-production-related neural patterns and the same movie set across participants may explain apparent content decoding. No claim of *silent* unprompted memory extraction from this dataset alone.
- Copyright: source films are not freely included in the dataset; honor dataset/media access rights.

### A3 — Memory encoding quality

- Source: [Penn EEG ds004706](https://github.com/OpenNeuroDatasets/ds004706), [Rudoler et al. 2024](https://pubmed.ncbi.nlm.nih.gov/39033965/), [authors' code](https://github.com/pennmem/optimizing-memory). Large dataset (~1.3 TB); download a documented bounded subset.
- Use observational **read-only** sessions first; distinguish from closed-loop sessions where experimental stimulus timing was influenced by neural prediction. Some raw backend logs are not published in the current analysis assets.
- Claim if successful: EEG predicts future remembering in a specific task, **not** remembered content.

Further assets: [PEERS ds004395](https://github.com/OpenNeuroDatasets/ds004395) for large free-recall EEG and [DANDI 000623](https://dandiarchive.org/dandiset/000623) for clinically acquired intracranial movie/recognition signals. Neither alone proves full memories can be downloaded.

## Baselines and negative controls

Pre-register each task and its allowed inputs. At minimum:

| Arm | Inputs | What it tests |
| --- | --- | --- |
| Context-only | Cues, timing, permitted stimuli/history | How much the task already reveals |
| Behavioral-only | Eye gaze, motion/artifacts, timing, permitted self-report | What cheaper observable signals explain |
| Neural-only | Allowed neural window, no hidden event identifiers | Information available through the BCI measurement |
| Neural+context | Permitted neural and contextual inputs | **Incremental neural benefit** |
| Shuffled/mismatched neural | Incorrect trial/participant/event signals | Leakage and nuisance shortcuts |
| Generative no-neural | Same prompts/context, no neural input | Plausible reconstruction from priors |

Use duration-preserving noise, matched-event details, event-wise and participant-wise grouped splits where relevant. [Hadidi et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13324000/) documents how confounds can manufacture misleading apparent language/brain alignment. [Narrative eye-gaze reinstatement study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12374978/) makes gaze a substantive comparison, not a decorative control.

## Phase B: proposed prospective, noninvasive study

**MEMSTACK-EPISODIC-001 — NOT APPROVED OR EXECUTED.** Requires qualified ethics/IRB review, participant protections, and scientific collaborators.

1. Generate one-time, harmless events containing unpredictable combinations of people/objects/locations/order. Include same-category events with discriminating details.
2. Obtain independently recorded event truth. Reserve unpredictable details and prevent answer access by the model's training/prompt pipelines.
3. At recall visits (early, after sleep, and later delayed visits), record a **silent, voluntary recall** window before speech or response movement.
4. Collect the participant's independent recollection *before* any generated reconstruction is displayed; record the elicitation method, assisted communication, prior AI-suggestion exposure and any participant-initiated generated aids.
5. Compare decoder predictions against sealed event truth and separately against reported recollection.
6. Repeat across different sessions and delays to test changing representations and electrode/measurement drift.

Avoid implying that a participant's failure to recall an event means the event did not occur, or that an AI's reconstruction necessarily represents the memory.

### Primary endpoint

Pre-register **two distinct outcome families**: (a) prediction of details in the participant's subsequent report `R` from the preceding silent neural window, and (b) independent verification of those details against event truth `E`. Analyze correctly recalled, misrecalled and unreported details separately. Neither `R` nor `E` is an exhaustive readout of the internal memory `M`.

For predefined withheld targets in each outcome family, pre-register paired held-out predictive log-loss improvement:

```text
delta = log_loss(context_only) - log_loss(neural_plus_context)
```

Positive `delta` suggests incremental predictive benefit from neural data. Report detail-level precision/recall, calibration, false additions, abstention rates, and per-person differences. This is **not** an unbiased estimate of all information contained in a memory. A single unsuccessful sensor/decoder trial cannot falsify the possibility of all future BCIs.

Evaluate at the **participant/event** level with clustered uncertainty, not as independent thousands of time windows. Set meaningful effect size, exclusion rules, model selection, correction for multiple hypotheses and sample size using pilot data/power simulation **before** final evaluation. Do not invent a universal number of subjects or a post hoc significance gate.

When using a balanced K-event identification task, an information-theoretic lower bound on identifiable event-label information may be derived from held-out error via Fano's inequality, with explicit assumptions. Such bits concern K-way event identity, **not the size of a human memory**.

## Go/no-go qualification gates

| Gate | Positive evidence needed | What may be claimed |
| --- | --- | --- |
| G0 — Reproduction | Public dataset preprocessing/splits/model reproduce a bounded published finding | Reproduction of that exact experiment |
| G1 — Event identity | Held-out known-event recall identification exceeds matched context/behavior controls | Restricted neural recall identity decoding |
| G2 — Novel detail | Neural signal adds meaningful accuracy for sealed episode-specific details on new events during silent recall | Partial content extraction beyond cues |
| G3 — Persistence | Above effect generalizes after sleep/weeks with recalibration documented and no evaluation leakage | Durable partial neural representation |
| G4 — Restoration | Separate, approved clinical causal study restores specific information using archived patterns beyond sham/control | Limited memory restoration, not subjective experience transfer |

**Stop claims at the last demonstrated gate.** A failure at G2 still permits an external lifelog plus neural-recognition aid; it does not permit describing it as memory backup.

## Experimental integrity

- Freeze data versions, labels, event/participant/session splits, code commit, models and final analysis plan before reserved evaluation.
- Require controls for spoken-word preparation, eye gaze, task cues, stimulus exposure, time/length signals and participant identity.
- Distinguish source data completeness, paper claims, successful code execution and independently replicated results.
- Archive null results, adverse outcomes, changes after sleep and negative controls.
- Reproducibility checks should include permitted dataset licenses and no copyright-infringing film redistribution.
- No stimulation/implantation for the noninvasive branch. Invasive studies are separately governed clinical research, not a do-it-yourself engineering phase.

## Implementation backlog

- [ ] Pin public dataset versions, licenses and subset manifests.
- [ ] Write a leakage audit before preprocessing.
- [ ] Implement regularized linear/spectral EEG baseline before larger models.
- [ ] Add context-only and eye-gaze baselines wherever data permit.
- [ ] Freeze session/event/subject holdouts and shuffled-neural controls.
- [ ] Publish reproducible task-scoped results, including negative findings.
- [ ] Only then consider a consent-reviewed prospective protocol.

See [evidence](EVIDENCE_REGISTER_20261029.md), [architecture](ARCHITECTURE_V0.md), and [review](../reviews/TKIK_BCI_MEMORY_20261029.md).
