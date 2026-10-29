# MemStack Muse 2 feasibility pilot v0

**Status:** SOURCE-BACKED DESIGN / NOT INSTALLED / NOT RUN. Patrick reports owning one Muse 2. I have not verified the device's pairing, charge, firmware, data-stream access, actual sensor quality, or host compatibility. No personal neural recording has been made for MemStack.

## Exact hardware boundary

The manufacturer lists **four dry EEG sensing locations: `TP9`, `AF7`, `AF8`, `TP10`**, plus an FPz reference, sampled at **256 Hz** with **12-bit** EEG resolution. Muse 2 also has motion and PPG sensing, which are **not additional EEG channels**. It is a low-density consumer device, not an intracranial interface and not a 64-channel substitute for the [Essex EEG benchmark](https://pmc.ncbi.nlm.nih.gov/articles/PMC12685955/). [Manufacturer's Muse comparison](https://choosemuse.my.site.com/s/article/Comparing-Muse-Headbands).

The Muse consumer app does not offer raw EEG export. Manufacturer [SDK access](https://choosemuse.com/pages/developers) is licensed, with distinct research/commercial terms; possession of the device does not implicitly grant commercial SDK or research-tools rights. [BrainFlow's Muse 2 documentation](https://brainflow.readthedocs.io/en/stable/SupportedBoards.html) offers an open-source development route using `BoardIds.MUSE_2_BOARD`. Its default Muse command `p21` streams four EEG plus IMU data. Other commands can include PPG and a separate auxiliary input; these must not silently become additional neural features.

## Capture routes to qualify, in priority order

1. **Lappy / Windows BLE + BrainFlow:** verify current Windows build and working Bluetooth Low Energy hardware before installing anything. Use the official Muse 2 board ID, query actual EEG-channel indices and sampling rate from the installed library, and explicitly select only four named EEG channels. Do not hard-code dataframe columns from an unrelated board or Muse S version.
2. **Android / existing Muse-compatible recording app:** investigate a documented raw-EEG CSV export workflow if such an app is already installed/licensed. Export locally and preserve exact device/app version, time base and channel identities. Do not silently grant an app extra personal-data permissions.
3. **Linux host with BLE access:** BrainFlow notes Linux may need `libdbus` and compilation for its BLE backend. Do not install/compile or alter another node without a verified host, current permission and bounded plan.

The existing [Muse-LSL](https://github.com/alexandrebarachant/muse-lsl) project is a possible alternative, but version/platform behavior, OSC/LSL transport latency, timestamp quality and marker handling require fresh verification before use. One successful packet does not qualify a continuous recording.

## M0: non-memory signal-quality experiment

**Purpose:** Determine whether this exact Muse 2 and host can consistently capture usable, time-aligned four-channel EEG. Not a test of recalling memories. No stimulation, diagnosis, treatment or clinical claim.

1. Obtain explicit local recording consent and a designated private, encrypted-at-rest storage destination outside Git. Disable cloud synchronization unless separately authorized. Capture source/consent/version receipts without exposing identifiers in repository logs.
2. Confirm four EEG identities, actual rate and time base; preserve raw samples and independently stored timestamps; separately label motion/PPG streams if used. Record acquisition firmware/app/library versions, packet loss and clock drift estimates. Never infer a sampling rate from an unrelated recording.
3. Record a short voluntary quality sequence (e.g. eyes open, eyes closed, deliberate blink, still rest, modest jaw movement) with bounded duration and separately logged event markers. Include frequent sensor-contact checks.
4. Validate rate and continuity, gaps, clipping, flatlines, amplitude, and repeatability across sessions. Show that alpha modulation/artifacts can be distinguished at a *signal-quality* level, but do not turn those observations into a memory-decoder claim.
5. Preserve artifact exclusions and every processing transform. Test whether injecting an impulse **after** a crop can change any retained epoch; reject whole-recording noncausal filtering if it contaminates the target window.

**M0 PASS:** source-pinned hardware/driver evidence, an inspectable local recording with correct four channels, a reproducible timestamp/gap/quality report, and a second-session consistency check. **M0 UNKNOWN:** device inaccessible, absent timestamps, excess loss, mismatch or unmeasured confounds. If M0 fails, the memory experiment does not proceed on that host.

## M1: optional constrained research, not memory backup

Only after M0, a personal, consent-controlled **cue-recognition or voluntary recall-state** pilot can test whether Muse 2 EEG contributes more than prompt identity, timing, motion/eye artifacts, and reported attention. Freeze instructions, targets, randomization, within-person train/test days, negatives and metrics before collecting held-out trials. Keep recording and labels in separate artifacts; never train on event-marker text, trial timestamps, cue IDs or answer-key fields as neural features. Use identical held-out observations for context-only, neural-only, combined and shuffled/wrong-trial controls.

Avoid asserting an independent autobiographical-content target unless independently sealed, previously unknown event details are provided under a reviewed protocol. A Muse 2 classifier of familiarity, attention, eye movements or response preparation is **not** evidence that it saved the remembered movie, event or subjective experience.

## Hard stops and privacy

> **High risk:** Forehead/temporal EEG electrodes are strongly vulnerable to ocular and muscle artifacts. Four sparse channels cannot directly sample deep hippocampal memory traces. A striking accuracy score under random-window splits is not sufficient evidence of mnemonic information.

> **High risk:** Neural recordings and derived features can be sensitive. Do not push raw recordings, sample timestamps tied to personal activity, subject reports or learned personal embeddings to GitHub. Any personal-data capture/export/storage must pass the consent and derivative lineage gates in [governance](GOVERNANCE_CONTRACT_V0.md).

This is a personal exploratory pilot. A regulated or prospective human-subject study would require the applicable independent scientific and ethics/IRB evaluation. The manufacturer itself describes Muse as a general-wellness product, not a medical device.

## Evidence and next gates

- [Official Muse 2 sensor comparison](https://choosemuse.my.site.com/s/article/Comparing-Muse-Headbands)
- [BrainFlow Muse 2 board and preset documentation](https://brainflow.readthedocs.io/en/stable/SupportedBoards.html)
- [Official Muse SDK and licensing routes](https://choosemuse.com/pages/developers)
- [Independent consumer EEG BCI assessment](https://pmc.ncbi.nlm.nih.gov/articles/PMC11502727/)
- [Muse 2 versus research headsets, artifacts and contact](https://pmc.ncbi.nlm.nih.gov/articles/PMC12972051/)

**Acceptance before a live probe:** confirm the intended host/BLE route and recording scope. No software install, Bluetooth pairing, private EEG capture or transfer is authorized merely by this design document.
