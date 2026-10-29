# MemStack Monitor v0.1 — Windows local EEG pilot

**Purpose:** a small research monitor for a directly connected Muse 2. This is neither a medical EEG system nor a memory reader. It does not infer private thoughts, diagnose health conditions, or retrieve human memories.

## Local setup on Lappy

Use the isolated MemStack Python environment on Windows. If it has already been provisioned, from `D:\VERA\memstack`:

```powershell
.\.venv\Scripts\python.exe -m memstack.monitor
```

Alternatively, double-click `scripts\launch_monitor.cmd` on Lappy. That launcher uses `pythonw.exe` so it opens a GUI without a console; for troubleshooting, run the command above to see errors. Enter the headset's Bluetooth device name in the app, or set a local `MEMSTACK_MUSE_SERIAL` environment variable. Do not commit your personal BLE identifier to public source files.

On a new Windows installation, use a compatible Python version with `tkinter` and install the optional BrainFlow dependency in an isolated virtual environment. Do not assume that the system-default Python has BrainFlow installed. BrainFlow's Muse 2 implementation needs a supported Windows Bluetooth Low Energy adapter. Disconnect the Muse from the phone's Muse app before connecting directly from Lappy: the headset may not support simultaneous host connections.

The application should open in a **disconnected** state. Opening a window or importing the package does not authorize acquisition. The person wearing the headset must explicitly opt in to reading their EEG before the connection and experiment controls become active. Stop and window-close must release the BLE session.

## What the screen means

| Indicator | Meaning | Important limitation |
| --- | --- | --- |
| TP9, AF7, AF8, TP10 traces | BrainFlow-reported four-channel voltage samples | Not source-localized or clinically calibrated brain activity |
| Approximately 256 Hz | BrainFlow's nominal Muse 2 rate | Not a verified packet-loss measurement |
| Large swings / saturation warnings | Potential artifact, poor fit, movement, or noisy acquisition | **Not** a validated electrode-impedance or signal-quality diagnosis |
| Eyes open / eyes closed | Local experiment condition scheduled by this program | Not a direct measurement that the participant actually complied |
| Audio cue marker | When the program scheduled or requested an instruction | Not measured sound onset at the ear |

No raw EEG is written to a local file or uploaded by this monitor version. Display memory is bounded and should be cleared on stop or exit. Even derived quality metrics can be sensitive; do not post per-person EEG analyses publicly without separate consent.

## Guided local experiment

An automatic eyes-open/eyes-closed trial prevents a participant being asked to read a chat message while their eyes are closed. The default local plan is **three repetitions of 10 seconds eyes open and 10 seconds eyes closed**. Instructions are audible on Lappy and the user can stop at any time.

The event schedule uses local Unix-clock timestamps so it can be compared approximately against BrainFlow's reported Unix timestamp channel. Windows audio scheduling, synthesis latency, Bluetooth transport, and hardware clocks may add unknown offsets. **Scheduled cue times are not exact stimulus-onset measurements.** If the application falls behind, missed cues must not be played in a burst; missed conditions should be labeled as timing compromises.

Do not interpret apparent alpha-band changes without first checking blinks, jaw movement, electrode contact, saturation, delayed sample blocks, and transition windows. For scientific analysis, add measured audio-onset synchronization, repeatable artifact exclusion, preregistered statistics, independent held-out runs and a private governed data store.

## Current boundaries

- This is a local pilot for one consented headset wearer, not an always-on neural surveillance service.
- No memory encoding, replay, diagnosis, stimulation, or authenticated cloud EEG storage.
- No guarantee that BrainFlow's normalized voltages originate solely from cortical activity; movement, muscle, reference and contact effects can dominate.
- Live-device performance is a separate qualification step from deterministic offline tests. Tests using fake BrainFlow objects are not a substitute for that step.

See [the four-channel adapter](MUSE2_ADAPTER_V0.md), [pilot plan](MUSE2_PILOT_V0.md), and [governance contract](GOVERNANCE_CONTRACT_V0.md).
