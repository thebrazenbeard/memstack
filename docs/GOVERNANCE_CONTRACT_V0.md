# MemStack governance contract v0 — design-only acceptance gates

**Status: design candidate, not an implemented authorization service, approved study, or legal opinion.** No identifiable human neural recordings belong in this repository.

The right to capture a signal does not imply the right to train on it, export it, show it to another person, or retain descendants indefinitely. Use W3C [PROV-O](https://www.w3.org/TR/prov-o/) concepts rather than inventing new origin semantics.

## Three append-only event families

### `AuthorizationDecision`

Required fields: `decision_id`, pseudonymous `subject_id`, authenticated `actor_id`, `action` (capture, process, train, share, export, delete), `purpose`, precise `input_artifact_ids`, `policy_version_hash`, `decision_time`, `effective_interval`, `decision` (`ALLOW`/`DENY`), `reason_code`, and `authorizing_basis_ref`.

The processor must evaluate an **authorization decision at the operation time**. A mere `consent_scope_ref` attached to a recording is not a decision receipt. If any scope, expiry, subject/third-party authority or derivative provenance is unknown, fail closed for that processing action. Preserve denials and later policy changes without rewriting the original event.

### `SuggestionExposure`

Required fields: `exposure_id`, pseudonymous `subject_id`, `session_id`, `content_hash`, `content_class`, `display_time`, `exposure_status` (`VERIFIED_DISPLAY`, `REPORTED_EXTERNAL`, `UNKNOWN`), `initiation_source`, `disclosure_label_version`, and `preceding_report_id` (nullable). Each `PARTICIPANT_REPORT` should additionally reference `elicitation_prompt_hash`, `collection_time`, and all known prior exposures.

An unobserved client display is `UNKNOWN`, **not** proof that exposure did not occur. The first recollection in an experiment is classified as independently elicited only if the protocol establishes that no prior generated aid was displayed in the controlled interface; unknown external exposure is a distinct limitation. A disclosure label alone is not sufficient to prevent altered recollection.

### `DerivativeManifest`

Required fields: `artifact_id`, `artifact_type`, `parent_artifact_ids`, `source_subject_manifest_hash`, `transform_code_hash`, `creation_time`, `storage_locations`, `retention_policy_ref`, `revocation_review_status`. Trace source inputs into every derived feature array, embedding, training set, adapter, model checkpoint, export and backup. Append revocation and remediation outcomes; do not overwrite their history.

The system must distinguish `DELETED_VERIFIED`, `ACCESS_RESTRICTED`, `RETAINED_UNDER_APPLICABLE_AUTHORITY`, `REVIEW_PENDING`, and `UNRECOVERABLE/UNKNOWN`. Source-file deletion is not proof that model weights have been unlearned.

## Hostile acceptance cases (unimplemented)

| Condition | Expected behavior |
| --- | --- |
| Policy reference valid, but no current `ALLOW` for model training | Deny training |
| Consent for local retrieval, not third-party export | Deny export |
| Expired authorization or participant withdrawal before scheduled run | Block run pending policy review |
| Withdrawal after checkpoint creation | Enumerate transitive derivatives; never claim automatic unlearning |
| Bystander voice/face in participant evidence | Independently evaluate third-party use; exclude or redact when unqualified |
| Generated aid displayed before the first report | Mark report suggestion-exposed, not independent |
| Exposure receipt missing | Record unknown, not none |
| Model output lacking source-to-feature-to-checkpoint lineage | Fail qualification |

Research withdrawal and erasure are not always equivalent. [HHS OHRP guidance](https://www.hhs.gov/ohrp/regulations-and-policy/guidance/guidance-on-withdrawal-of-subject/index.html) describes circumstances where an approved study can retain/analyze already-collected data after withdrawal; applicability depends on the specific protocol and jurisdiction. [HHS 45 CFR 46](https://www.hhs.gov/ohrp/regulations-and-policy/regulations/45-cfr-46/index.html) and [UNESCO's 2025 recommendation](https://www.unesco.org/en/node/86248) are relevant context, not authorization to run a study.

## Claim and product restrictions

- No assertion that generated material verifies a past event, recovers repressed trauma, authenticates forensic eyewitness memory, or restores a patient's memories.
- Do not present the archive as a consciousness or identity transfer mechanism without separate rigorous evidence.
- An optional no-generation external lifelog must remain functional, even when neural inference and suggestions are unavailable.
- No identifiable personal data, recordings, inferred private attributes, or secret keys committed to Git.

**Implementation status:** Contracts are proposed only. Enforcement, consent interfaces, human review and end-to-end derivative accounting are NOT BUILT or VERIFIED.
