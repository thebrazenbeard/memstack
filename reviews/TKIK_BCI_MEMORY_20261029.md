# T’Kal-in-ket-style adversarial case — BCI digital memory (2026-10-29)

**Status:** INTERNAL MODEL REVIEW / **advisory REFINE**, **not** an executed or formally adjudicated `tkik.core.Case`. The underlying [T’Kal-in-ket protocol](https://github.com/thebrazenbeard/t-kal-in-ket/blob/main/docs/PROTOCOL.md) was inspected at `thebrazenbeard/t-kal-in-ket` main `b0af150c2405b519fd921bac33e5f9f1f35f92d7`, protocol blob `eaaa5c815192bbc7c3ddd3d71bc97671d9db57ff`.

## Claim ownership and freeze

Patrick **asked a question**: “Can a brain-computer interface be used to store human memories onto digital storage?” He did **not** assert that a complete memory backup exists.

For falsification, the research team operationalized the following stronger **HYPOTHESIS**, ID `BCI-MEM-20261029-v1`:

> A brain–computer interface can capture arbitrary human autobiographical episodic memories in digital form and later reconstruct their contents with independently verifiable fidelity.

Definitions:

- **Arbitrary:** not just selecting from a small known/rehearsed set.
- **Autobiographical episode:** person-specific event details including what, where, when and meaningful sensory/contextual aspects.
- **Stored:** persisted digital representation usable after the source recording session.
- **Faithful:** demonstrable recovery of independently verifiable details, including measurement of omissions, incorrect additions and uncertainty.
- **Neural contribution:** independently measurable value of the recorded brain signals beyond prompts, event media, model priors and observable behavior.
- **Restoration/write-back:** a separate and stronger hypothesis that stimulating a brain with archived codes reinstates specific remembered experience.

The above proposition is **HYPOTHESIS / TEAM OPERATIONALIZATION**, not `USER_DIRECT`.

**Falsifiability boundary:** The broad future-technology question cannot be experimentally disproven by one failed decoder. It remains `UNKNOWN`. A future executable `Case` must instead freeze a candidate-specific claim and explicit falsifier: named sensor, cohort, voluntary task, permitted context, held-out episodes, delay, outcome metric and preregistered threshold. Failure then rejects *that candidate's* performance claim only.

## Evidence classes

- `EXTERNAL_EVIDENCE`: primary human papers and public data records listed in [evidence register](../docs/EVIDENCE_REGISTER_20261029.md).
- `REPOSITORY_SOURCE`: inspected T’Kal-in-ket protocol and MemStack files.
- `INFERENCE`: interpretation of their limits and proposed engineering roadmap.
- `UNKNOWN`: whether future, higher-bandwidth brain interfaces can achieve general episodic backup.
- **Absent:** original lab observations, human clinical review, code execution of the TKI state machine, independent model/provider receipts, memory-decoder benchmark results.

## Three lenses

### Purist Logic — identifiability and terminology

> **Challenge:** Recording voltages correlated with recollection is not equivalent to recording the complete memory. If two experiences yield indistinguishable available neural observations under the same context, a decoder cannot identify which experience was recalled from those observations alone.

**Answer / concession:** Distinguish `NEURAL_MEASUREMENT`, `NEURAL_INFERENCE`, `EXTERNAL_RECORD`, `PARTICIPANT_REPORT`, and `GENERATED_HYPOTHESIS`. A reconstruction must show where each detail originated. For a fixed interface and context C, identical observation distributions for distinct M imply that they cannot be separated through N alone. This is **not** evidence that all imaginable future interfaces will fail.

Under an explicit model where output is computed from neural data N and declared context C, the data-processing principle prevents a decoder from manufacturing additional *neural-attributable* evidence. Generative priors may improve apparent output plausibility without increasing measured neural information.

**Disposition proposed:** REFINE. Survives as a restricted partial-decoding research target, not as demonstrated full extraction.

### Pragmatism — engineering, evidence and controls

> **Challenge:** Strong-looking experiments use known stimuli, selected neural coverage, intensive calibration, clinical patient cohorts, verbal prompts or fMRI scanners. Stimulus recognition, speech preparation, eye gaze and AI priors can masquerade as episodic extraction.

**Answer:** Evidence supports restricted classifiers and partial semantic/experiential feature decoding: [Chadwick 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2849012/), [Tang 2023](https://www.nature.com/articles/s41593-023-01304-9), [Anderson 2025](https://www.nature.com/articles/s41467-025-65541-1), [Ding preprint 2025–26](https://pmc.ncbi.nlm.nih.gov/articles/PMC12236671/). [Hampson 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6576290/) improved memory task performance through stimulation; it did not export contents. [Roeder 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10881797/) includes harmful-to-performance stimulation conditions.

**Proposed decisive control:** Pre-register novel one-time episodes with unpredictable hidden details. Evaluate silent-recall neural-only, context-only, gaze/behavior-only and neural+context predictions using held-out event/day/participant splits. Add wrong-person/event, shuffled neural and generative no-neural controls. Report calibrated detail accuracy and invented facts, not just plausible images.

**Disposition proposed:** REFINE. Build a provenance-aware memory index and require incremental neural benefit.

### Bridge — human effects, scope and privacy

> **Challenge:** If generated reconstructions are repeatedly shown as the person's real past, false recollections may be reinforced. A subject's memory report and recorded history can legitimately diverge. Raw neurodata, inferred states, personal models and third-party media are sensitive; storing more for future AI creates future attack surface.

**Answer:** Preserve separate evidence and correction histories. Display generated content as unverified, but do not assume labeling prevents suggestion-induced recollection. Obtain the person's independent recollection *before* revealing predictions during studies; log prior exposures. Require opt-in speculative generation, third-party privacy decisions and accessible communication/consent. Set voluntary capture and retention controls, encrypted local-first storage, separate training/sharing permissions, threat-model personalized weights and backups, and independent security review before identifiable uploads. See [Pataranutaporn et al. 2025](https://www.media.mit.edu/publications/synthetic-human-memories/), [Shao et al. 2026](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3003886), [UNESCO 2025 Recommendation](https://www.unesco.org/en/node/86248) and [Sandbrink & Young 2026](https://www.nature.com/articles/s43856-026-01797-y).

**Disposition proposed:** REFINE. Archival utility does not prove continuity/identity transfer or authorize invasive interventions.

## Material dissent retained

1. **Overly pessimistic calibration assumption rejected:** [2025 cross-participant semantic decoder transfer](https://pubmed.ncbi.nlm.nih.gov/39919742/) shows that semantic alignment can generalize more than the original person-specific models suggested. This does not establish arbitrary covert decoding; never present poor transfer as a permanent privacy guarantee.
2. **Existing memory decoding must not be dismissed:** Specific studied memory traces, recalled concepts and autobiographical imagery features *have* been decoded in constrained human settings. The strong proposition does not fail merely because all observed signals are meaningless.
3. **Stimulation has useful causal effects in some tasks:** Clinical memory enhancements are genuine evidence for neuroprosthetic mechanisms, but do not demonstrate preserved experiences were recreated.
4. **Future feasibility unresolved:** Today's coverage, longitudinal drift, task biases and validation limitations are substantial but are not a proof of impossibility for future systems.

## Advisory disposition

| Proposition | Review conclusion |
| --- | --- |
| Save raw memory-associated neural recordings | SURVIVES as demonstrated technique |
| Decode known recalled events / concepts in bounded experiments | SURVIVES within specified study scope |
| Combine archive + calibrated neural index as assistive system | Plausible engineering hypothesis; BCI-specific benefit NOT TESTED |
| Backup and faithfully reconstruct arbitrary autobiographical episodes | **NOT DEMONSTRATED; future feasibility UNKNOWN** |
| Write such backups into a brain to restore the remembered experience | **NOT DEMONSTRATED; future feasibility UNKNOWN** |

**Advisory REFINE:** Replace the strong claim with:

> A consent-controlled, person-calibrated BCI may preserve measurable neural correlates of experiences and recollection, decode limited associated content, and link these with a provenance-aware digital archive. Greater fidelity, generality and longevity of neural memory-content recovery are falsifiable scientific targets.

This is **not** `SUSTAIN` under the repository's source implementation. No executed `Case`, three distinct recorded reviewer identities with the required directed answered/conceded cross-examination cycle, or full adjudication log exists. Those are source-level gates for `SUSTAIN`; **authenticated independent-provider receipts are an additional evidence-integrity requirement, not something the current in-memory Python state machine itself verifies**. The written lenses here are a transparent model-synthesized hearing only.

## Acceptance and next falsifiers

- [ ] Reproduce a bounded public-memory decoding result with pinned data and code.
- [ ] Show neural addition over cue/time/gaze/speech baselines on held-out tasks.
- [ ] Recover independently verified, previously withheld details during silent voluntary recollection without giving the model those facts.
- [ ] Replicate across delayed sessions and participants with measured drift.
- [ ] Identify hallucinated details and abstain reliably when data do not support claims.
- [ ] Keep stimulation/write-back in a distinct, qualified clinical research protocol.
- [ ] If formal TKI adjudication is requested, register frozen claim digest, separate reviewer identities, supported remote execution receipts, directed answered/conceded cross-examination and no outstanding challenge before determination.

## Reviewer provenance

**Wave 1:** `/root/neural_encoding`, `/root/bci_hardware`, `/root/memory_prosthetics`, `/root/skeptic_ethics`, `/root/architecture`, `/root/repo_github`.

**Wave 2:** `/root/datasets_audit_v2`, `/root/infotheory_v2`, `/root/methods_v2`, `/root/experiment_v2`, `/root/security_v2`, `/root/tkik_cross_exam_v2`.

All were genuine native child research tasks. Distinct task paths are **not** independently attested different model providers, laboratory replications, or an executed TKI quorum. Scope was source review and conceptual design; none claimed direct access to a live memory BCI or to a subject's private experience.

**Chair integration:** `/root` assembled and classified the claims, preserved dissent, and left the strong claim unresolved. No runtime or empirical qualification is implied.
