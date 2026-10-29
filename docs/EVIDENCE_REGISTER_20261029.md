# Evidence register — BCI and human memory (2026-10-29)

**Status:** SOURCE_REVIEW. Literature and public data records were inspected; no source study was replicated, neural data downloaded, model trained, or participant measured for MemStack.

## Claim levels

| Claim | Current verdict |
| --- | --- |
| Preserve measured neural signals digitally | Demonstrated technology |
| Classify a small set of previously experienced/recalled stimuli | Demonstrated in constrained studies |
| Recover limited concepts or features associated with recollection | Limited empirical support, cohort/task dependent |
| Reliably recover novel, unpredictable episodic details from neural data alone | UNKNOWN / unproven |
| Recover a complete autobiographical experience at independent fidelity | UNKNOWN / not demonstrated |
| Restore a particular archived experience through stimulation | UNKNOWN / not demonstrated |

A true negative finding here means **not demonstrated in the reviewed evidence**, not a theorem that future interfaces cannot succeed.

## Primary human studies

| Source | What was actually shown | What it does not show |
| --- | --- | --- |
| [Chadwick et al., Current Biology (2010)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849012/) | fMRI distinguished which of three short, extensively rehearsed event clips was being recalled. | An open-set decoder or digitally reconstructed sensory experience. |
| [Hampson et al., J Neural Engineering (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6576290/) | Subject-specific hippocampal CA3-to-CA1 model-informed stimulation improved short-term image-memory and delayed recognition outcomes, reported as 37% and 35% improvements, in a small epilepsy cohort. | Extraction, storage, or reinstallation of the remembered images. |
| [Ezzyat et al., Nature Communications (2018)](https://www.nature.com/articles/s41467-017-02753-0) | Closed-loop stimulation based on predicted memory-encoding state improved task recall. | Reading specific autobiographical contents. |
| [Distinct cortical systems reinstate content/context, Nature Communications (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8295370/) | Intracranial recordings distinguished semantic content and temporal context in distributed cortical networks. | A single stable stored episode vector. |
| [Lee et al., 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10424734/) | Constrained fMRI decoding of semantic dimensions linked to naturalistic scene recollection in four intensively scanned participants. | Full, objectively faithful playback of recalled scenes. |
| [Tang et al., Nature Neuroscience (2023)](https://www.nature.com/articles/s41593-023-01304-9) | Cooperative participant-specific fMRI decoders produced meaning-level approximations of perceived and imagined language. | Verbatim thoughts, effortless transfer to arbitrary people, or episodes reconstructed from neural signals alone. |
| [Human hippocampal episode-selective neurons (2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10663153/) | Episode-associated cell firing was reinstated at retrieval in constrained association experiments. | A complete representation recoverable through limited electrodes. |
| [Roeder et al., Frontiers in Computational Neuroscience (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10881797/) | Hippocampal image-category-linked stimulation altered recognition in some patient/category comparisons; improvements and impairments both occurred. | A reliable memory-writing procedure or proof of encoded visual content. |
| [Rudoler et al., J Neuroscience Methods (2024)](https://pubmed.ncbi.nlm.nih.gov/39033965/) | Noninvasive EEG predicts some variation in subsequent memory success in a naturalistic navigation task. | Memory content recovery. |
| [Anderson et al., Nature Communications (2025)](https://www.nature.com/articles/s41467-025-65541-1) | In 50 people imagining personally grounded, pre-cued scenarios, fMRI decoded limited experiential features; semantic features and prompts were consequential. | Recovering the audiovisual event itself; fully open-set autobiographical decoding. |
| [Narrative neural + eye-gaze reinstatement, Nature Communications (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12374978/) | Neural and gaze-pattern reinstatement jointly tracked recall of watched narrative events. | Evidence that neural signals outperform all simpler behavioral signals in an archive. |
| [Ding et al., bioRxiv preprint (2025–26)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12236671/) | Initial ten implanted patients saw a TV episode; person-calibrated models identified eight predefined concepts associated with subsequent verbal recall; a 2026 revision expanded the cohort. | Peer-reviewed proof of general memory download, arbitrary details, or playback. **PREPRINT.** |
| [Bausch et al., Nature (2026)](https://www.nature.com/articles/s41586-025-09910-2) | 3,109 neurons in 16 implanted participants; content, context, and conjunction coding involved partly distinct populations. | A single localized “memory file” or enough recording coverage for complete recall. |
| [Population code for semantics in human hippocampus, Nature Neuroscience (2026)](https://www.nature.com/articles/s41593-026-02436-4) | Contextual semantic representations during narrative listening. [Publisher correction](https://www.nature.com/articles/s41593-026-02501-y) dated October 2026. | Retrieval of original autobiographical memories. |
| [Stimulus-specific amygdala activity predicts episodic encoding success, Nature Neuroscience (2026)](https://www.nature.com/articles/s41593-026-02493-9) | Category/stimulus-related responses forecast later recognition in clinical cohorts. | Reconstruction of the memory's content from a saved trace. |
| [Autobiographical visual imagery, Science Advances (2026)](https://pubmed.ncbi.nlm.nih.gov/42777057/) | Neural representational similarity to synthetic image models based on participant descriptions. | Neural-only extraction of a photographic memory. |

## Methodological falsifiers and contrary evidence

- [Hadidi et al., Nature Communications (2026)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13324000/) warns that confounds, shuffled splitting and method choices can produce spurious apparent language-model/brain alignment. Neuro-decoding claims require leakage and nuisance controls.
- [Cross-participant semantic decoding (2025)](https://pubmed.ncbi.nlm.nih.gov/39919742/) weakens blanket statements that individualized calibration will *always* be necessary. It does not establish covert mind-reading.
- [Multidimensional autobiographical memory topography (2022)](https://www.nature.com/articles/s41467-022-34075-1) combines thousands of personal-video events with neural signals, while highlighting confounding stimulus properties.
- A generated scene that looks plausible is not validated memory content. Inspect exact event-detail precision, false additions, abstentions, and incremental predictive benefit over a prompt-only model.

## Data and analysis assets (different tasks; do not pool indiscriminately)

| Dataset / authors' code | Task and use | Limitation |
| --- | --- | --- |
| [Essex EEG Movie Memory ds006142](https://github.com/OpenNeuroDatasets/ds006142); [data paper](https://www.nature.com/articles/s41597-025-06203-1) | 27 participants, 64-channel EEG, ~24 GB, recognition during 10-second movie clips; practical first benchmark | Movie is shown during recording: stimulus-driven recognition, not uncued memory extraction. |
| [FilmFestival ds004042](https://openneuro.org/datasets/ds004042/versions/1.0.1); [data paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9727629/) | 20 adults, ~39 GB fMRI, film viewing and free spoken recall; memory-content benchmark | Speech production, task prompts and common movie set confound neural-only inference; copyrighted movies omitted. |
| [Penn ds004706](https://github.com/OpenNeuroDatasets/ds004706); [authors' analysis](https://github.com/pennmem/optimizing-memory) | 34 participants, ~1.3 TB EEG, encoding success; observational/read-only sessions first | Closed-loop timing changes training distribution; raw backend logs incomplete for some analyses. |
| [Penn PEERS ds004395](https://github.com/OpenNeuroDatasets/ds004395) | Large EEG free-recall corpus; useful later | Multi-terabyte scale, word-list rather than fully naturalistic memories. |
| [Content/context neuron analysis](https://github.com/mabausch/ContentContextNeurons) | Author code/data for representations | Perception/controlled experimental context, not general backup. |
| [Hippocampal semantics code](https://github.com/mcfranch/PopulationCodeForSemanticsHippocampus) | Author analysis and linked neural dataset | Semantic perception, not autobiographical retrieval. |
| [Narrative gaze/recollection OSF](https://osf.io/baw39/) | Non-neural eye gaze and recall controls | May only cover the particular cohort/tasks. |

Public data licensing, allowed media uses, actual download subsets and version-specific contents must be revalidated before downloading or redistributing. Subject counts/sizes are source metadata, not dataset readback.

## Evidence separation

- **EXTERNAL_EVIDENCE:** linked primary publications and dataset records.
- **SOURCE_INSPECTION:** research repository structure/description, where inspected.
- **INFERENCE/HYPOTHESIS:** proposed integrated MemStack architecture and gates.
- **NOT PERFORMED:** original experiment, clinical test, dataset ingestion, replication, device qualification, formal independent peer review.

Keep an individual claim's source, publication status, cohort, task, inference route, confounds and uncertainty when reusing it. Do not elevate a preprint, perspective article or review to an experimental demonstration.
