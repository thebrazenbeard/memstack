"""Opt-in Windows Muse 2 monitor. No capture, file I/O, or GUI on import.

Run: python -m memstack.monitor

This viewer shows crude signal warnings only. Neither contact quality, neural
state, nor human memory is decoded. Raw samples and cues remain in process RAM.
"""

from __future__ import annotations

import math
import os
import queue
import statistics
import subprocess
import sys
import threading
import time
from collections import deque
from typing import Iterable

from .muse2 import CHANNELS
from .waveform import RawEEGFrame

TRACE_COLORS = ("#54d6c4", "#69a7fa", "#c693f9", "#f4b45c")
MAX_SESSION_SECONDS = 120.
MAX_VIEW_SAMPLES = 768
DRAW_INTERVAL_MS = 100


class SignalWindow:
    """Bounded volatile display buffer, not a recording repository."""

    def __init__(self, max_samples: int = MAX_VIEW_SAMPLES):
        if not 1 <= max_samples <= 2048:
            raise ValueError("invalid max_samples")
        self.frames: deque[RawEEGFrame] = deque(maxlen=max_samples)

    def add(self, frames: Iterable[RawEEGFrame]) -> None:
        self.frames.extend(frames)

    def clear(self) -> None:
        self.frames.clear()


def signal_flags(frames: Iterable[RawEEGFrame]) -> tuple[str, str, str, str]:
    """Gross artifact/flatline heuristics. UNASSESSED is not a quality pass."""
    recent = tuple(frames)
    if not recent:
        return ("NO_DATA",) * 4
    results = []
    for channel in range(4):
        values = [frame.eeg_uv[channel] for frame in recent]
        if any(not math.isfinite(v) or abs(v) >= 900 for v in values):
            results.append("POSSIBLE_ARTIFACT")
        elif len(values) >= 32 and max(values) - min(values) <= 0.01:
            results.append("POSSIBLE_FLATLINE")
        elif any(abs(b - a) >= 500 for a, b in zip(values, values[1:])):
            results.append("POSSIBLE_ARTIFACT")
        else:
            results.append("UNASSESSED")
    return tuple(results)


def trace_points(values: Iterable[float], *, width: float, height: float,
                 scale_uv: float = 200.) -> list[tuple[float, float]]:
    """Turn a waveform into clipped viewport coordinates."""
    seq = tuple(values)
    if not seq:
        return []
    if width <= 0 or height <= 0 or scale_uv <= 0:
        raise ValueError("drawing dimensions and scale must be positive")
    midpoint = statistics.median(seq)
    return [
        (width * index / max(1, len(seq) - 1),
         min(height, max(0., height / 2 - (value - midpoint) * height / (2 * scale_uv))))
        for index, value in enumerate(seq)
    ]


def _publish(events: queue.Queue, kind: str, value: object = None) -> bool:
    """A slow UI must never block the Bluetooth worker."""
    try:
        events.put_nowait((kind, value))
        return True
    except queue.Full:
        if kind == "samples":
            return False
        try:
            events.get_nowait()
            events.put_nowait((kind, value))
            return True
        except (queue.Empty, queue.Full):
            pass
        return False


class AcquisitionWorker(threading.Thread):
    """One worker thread owns all BrainFlow calls, including cleanup."""

    def __init__(self, serial: str, events: queue.Queue):
        super().__init__(name="memstack-brainflow", daemon=True)
        self.serial = serial
        self.events = events
        self.cancel = threading.Event()
        self.dropped_display_batches = 0

    def request_stop(self) -> None:
        self.cancel.set()

    def run(self) -> None:
        from .live import LiveMuse2
        device = None
        try:
            device = LiveMuse2(serial_number=self.serial, consent=True)
            device.connect()
            _publish(self.events, "connected")
            while not self.cancel.is_set():
                frames = device.poll()
                if frames:
                    # Do not queue a potentially huge BrainFlow backlog in RAM.
                    sent = _publish(
                        self.events, "samples",
                        (frames[-MAX_VIEW_SAMPLES:], len(frames), self.dropped_display_batches),
                    )
                    if not sent:
                        self.dropped_display_batches += 1
                self.cancel.wait(.08)
        except Exception as exc:
            _publish(self.events, "capture_error", f"{type(exc).__name__}: {exc}")
        finally:
            if device is not None:
                try:
                    device.close()
                except Exception as exc:
                    _publish(self.events, "capture_error", f"Release failed: {exc}")
            _publish(self.events, "display_drops", self.dropped_display_batches)
            _publish(self.events, "disconnected")


class WindowsSpeaker:
    """Serialized System.Speech messages; playback onset is NOT measured."""

    ALLOWED = frozenset((
        "Audio check. You should hear this message.",
        "Open your eyes", "Close your eyes", "Experiment complete",
        "Experiment stopped. Sensor signal lost.",
    ))

    def __init__(self, events: queue.Queue):
        self.events = events
        self.pending: queue.Queue = queue.Queue(maxsize=4)
        self.cancel = threading.Event()
        self.lock = threading.Lock()
        self.generation = 0
        self.active: subprocess.Popen | None = None
        self.thread = threading.Thread(target=self._run, name="memstack-speech", daemon=True)
        self.thread.start()

    def say(self, message: str) -> bool:
        if message not in self.ALLOWED:
            raise ValueError("unsupported audio instruction")
        if sys.platform != "win32" or self.cancel.is_set():
            return False
        try:
            with self.lock:
                self.pending.put_nowait((self.generation, message))
            return True
        except queue.Full:
            return False

    def discard(self) -> None:
        """Discard stale voice cues and interrupt an in-flight instruction."""
        with self.lock:
            self.generation += 1
            if self.active is not None and self.active.poll() is None:
                try:
                    self.active.terminate()
                except OSError:
                    pass  # Process may exit between poll and terminate.
        while True:
            try:
                self.pending.get_nowait()
            except queue.Empty:
                break

    def close(self) -> None:
        self.cancel.set()
        self.discard()
        try:
            self.pending.put_nowait(None)
        except queue.Full:
            pass

    def _run(self) -> None:
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$voice.Speak([Console]::In.ReadToEnd())"
        )
        while not self.cancel.is_set():
            try:
                item = self.pending.get(timeout=.2)
            except queue.Empty:
                continue
            if item is None:
                break
            generation, message = item
            process = None
            try:
                with self.lock:
                    if generation != self.generation:
                        continue
                    process = subprocess.Popen(
                        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True,
                    )
                    self.active = process
                _, stderr = process.communicate(input=message, timeout=12)
                if process.returncode:
                    raise RuntimeError(
                        f"System.Speech exited {process.returncode}: {stderr.strip()[:180]}"
                    )
                with self.lock:
                    if generation == self.generation:
                        _publish(self.events, "speech_ok", message)
            except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
                if process is not None and process.poll() is None:
                    process.kill()
                    process.communicate()
                with self.lock:
                    if generation == self.generation:
                        _publish(self.events, "speech_error", str(exc))
            finally:
                with self.lock:
                    if self.active is process:
                        self.active = None


class MonitorApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.root.title("MemStack Monitor v0.1")
        self.root.minsize(820, 560)
        self.events: queue.Queue = queue.Queue(maxsize=32)
        self.view = SignalWindow()
        self.worker: AcquisitionWorker | None = None
        self.speaker = WindowsSpeaker(self.events)
        self.experiment = None
        self.epoch_anchor = time.time()
        self.monotonic_anchor = time.monotonic()
        self.connected_mono: float | None = None
        self.last_samples_mono: float | None = None
        self.closing = False
        self.audio_checked = False
        self.experiment_completed = False
        self.accept_samples = False
        self.samples_seen = 0
        self.display_drops = 0

        self.serial = tk.StringVar(value=os.environ.get("MEMSTACK_MUSE_SERIAL", ""))
        self.consent = tk.BooleanVar(value=False)
        self.heard_audio = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Disconnected · no EEG saved")
        self.condition = tk.StringVar(value="NOT STARTED")
        self.quality = tk.StringVar(value="Signal flags: no samples")
        self.sample_count = tk.StringVar(value="Samples admitted to display: 0")
        self.audio_status = tk.StringVar(value="Test voice instructions before the experiment")

        shell = ttk.Frame(root, padding=14)
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="MemStack Monitor", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(shell, text="Research-only Muse 2 EEG viewer; not a memory reader or clinical tool").pack(anchor="w")
        controls = ttk.Frame(shell)
        controls.pack(fill="x", pady=(14, 7))
        ttk.Label(controls, text="Device").pack(side="left")
        self.serial_entry = ttk.Entry(controls, width=18, textvariable=self.serial)
        self.serial_entry.pack(side="left", padx=(7, 12))
        self.consent_checkbox = ttk.Checkbutton(
            controls, text="I consent to local EEG capture", variable=self.consent
        )
        self.consent_checkbox.pack(side="left", padx=(0, 12))
        self.start_button = ttk.Button(controls, text="Connect", command=self.start_capture)
        self.start_button.pack(side="left", padx=(0, 4))
        self.stop_button = ttk.Button(controls, text="Stop capture", command=self.stop_capture,
                                      state="disabled")
        self.stop_button.pack(side="left")

        ttk.Label(shell, textvariable=self.status).pack(anchor="w")
        self.canvas = tk.Canvas(shell, height=350, bg="#151a24", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=(12, 8))
        ttk.Label(shell, textvariable=self.quality, wraplength=850).pack(anchor="w")
        ttk.Label(shell, textvariable=self.sample_count).pack(anchor="w")
        row = ttk.Frame(shell)
        row.pack(fill="x", pady=(12, 5))
        ttk.Label(row, text="Eyes open/closed · 3 cycles, 60 seconds").pack(side="left")
        self.audio_test_button = ttk.Button(row, text="Test audio", command=self.test_audio)
        self.audio_test_button.pack(side="left", padx=(12, 5))
        self.experiment_button = ttk.Button(
            row, text="Start guided experiment", command=self.start_experiment, state="disabled"
        )
        self.experiment_button.pack(side="left")
        ttk.Label(row, textvariable=self.condition).pack(side="right")
        self.heard_checkbox = ttk.Checkbutton(
            shell, text="I heard the spoken audio test", variable=self.heard_audio,
            command=self._update_experiment_button,
        )
        self.heard_checkbox.pack(anchor="w")
        ttk.Label(shell, textvariable=self.audio_status, wraplength=850).pack(anchor="w")
        ttk.Label(
            shell, wraplength=850,
            text="Cues are scheduled locally; actual sound onset is not measured. "
                 "Samples and event times are RAM-only; no disk or network export.",
        ).pack(anchor="w", pady=(8, 0))
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(DRAW_INTERVAL_MS, self.tick)

    def now_epoch(self) -> float:
        """Monotonic-driven timeline anchored to Unix time at app startup."""
        return self.epoch_anchor + time.monotonic() - self.monotonic_anchor

    def start_capture(self) -> None:
        from tkinter import messagebox
        if self.worker is not None and self.worker.is_alive():
            return
        if not self.consent.get():
            messagebox.showwarning(
                "Consent required", "Select local EEG consent before connecting."
            )
            return
        serial = self.serial.get().strip()
        if not serial:
            messagebox.showwarning("Device required", "Enter the Muse Bluetooth name.")
            return
        self.view.clear()
        self.speaker.discard()
        self.samples_seen = 0
        self.display_drops = 0
        self.experiment_completed = False
        self.accept_samples = True
        self.connected_mono = None
        self.last_samples_mono = None
        self.experiment = None
        self.condition.set("NOT STARTED")
        self.status.set("Connecting to Muse 2 ...")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.experiment_button.configure(state="disabled")
        self.serial_entry.configure(state="disabled")
        self.consent_checkbox.configure(state="disabled")
        self.worker = AcquisitionWorker(serial, self.events)
        self.worker.start()

    def stop_capture(self, *, completed: bool = False) -> None:
        if self.worker is not None and self.worker.is_alive():
            self.worker.request_stop()
            self.status.set("Stopping and releasing Muse 2 ...")
        self.experiment = None
        self.experiment_completed = completed
        self.accept_samples = False
        if not completed:
            self.speaker.discard()
        self.view.clear()
        self.last_samples_mono = None
        self.experiment_button.configure(state="disabled")
        self.audio_test_button.configure(state="normal")
        self.condition.set("DONE" if completed else "STOPPED")

    def test_audio(self) -> None:
        if self.experiment is not None:
            return
        self.audio_checked = False
        self.heard_audio.set(False)
        self._update_experiment_button()
        if self.speaker.say("Audio check. You should hear this message."):
            self.audio_status.set("Audio test requested · listen to Windows speakers")
        else:
            self.audio_checked = False
            self.audio_status.set("Audio unavailable. Guided experiment cannot start.")

    def say_cues(self, cues) -> bool:
        if not cues:
            return True
        latest = cues[-1]  # After a delayed UI tick, don't speak obsolete cues.
        if not self.speaker.say(latest.instruction):
            self.audio_status.set("Audio unavailable · experiment aborted")
            self.experiment = None
            self.condition.set("ABORTED")
            self.stop_capture()
            return False
        self.audio_status.set(
            f"Voice requested: {latest.instruction} · scheduled event, sound onset not measured"
        )
        return True

    def start_experiment(self) -> None:
        from tkinter import messagebox
        from .protocol import EyesExperiment
        if self.connected_mono is None or self.experiment is not None:
            return
        if not self.audio_checked or not self.heard_audio.get():
            messagebox.showwarning(
                "Audio check required", "Run the audio test and confirm you heard the voice."
            )
            return
        if self.last_samples_mono is None or time.monotonic() - self.last_samples_mono > 1.5:
            messagebox.showwarning(
                "EEG stream unavailable", "Wait for fresh Muse EEG samples before starting."
            )
            return
        self.experiment = EyesExperiment(open_seconds=10, closed_seconds=10, cycles=3)
        cues = self.experiment.start(self.now_epoch())
        if not self.say_cues(cues):
            return
        self.condition.set("OPEN")
        self.experiment_button.configure(state="disabled")
        self.audio_test_button.configure(state="disabled")

    def _update_experiment_button(self) -> None:
        ready = (
            self.connected_mono is not None and self.audio_checked
            and self.heard_audio.get() and self.experiment is None
            and self.last_samples_mono is not None
            and time.monotonic() - self.last_samples_mono <= 1.5
        )
        self.experiment_button.configure(state="normal" if ready else "disabled")

    def tick(self) -> None:
        if self.closing and (self.worker is None or not self.worker.is_alive()):
            self.speaker.close()
            self.root.destroy()
            return
        for _ in range(32):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "connected":
                if not self.accept_samples:
                    continue
                self.connected_mono = time.monotonic()
                self.status.set("Connected · capture in RAM · 120s automatic cutoff")
                self._update_experiment_button()
            elif kind == "samples":
                if not self.accept_samples:
                    continue
                display_frames, _received_count, dropped_batches = value
                self.view.add(display_frames)
                self.samples_seen += len(display_frames)
                self.display_drops = max(self.display_drops, dropped_batches)
                self.last_samples_mono = time.monotonic()
                self.sample_count.set(
                    f"Samples admitted to display: {self.samples_seen} · "
                    f"dropped UI batches: at least {self.display_drops} "
                    "(not a Bluetooth packet-loss measure)"
                )
                self._update_experiment_button()
            elif kind == "display_drops":
                self.display_drops = max(self.display_drops, value)
                self.sample_count.set(
                    f"Samples admitted to display: {self.samples_seen} · "
                    f"dropped UI batches: at least {self.display_drops} "
                    "(not a Bluetooth packet-loss measure)"
                )
            elif kind == "capture_error":
                self.status.set(f"Capture error: {value}")
            elif kind == "disconnected":
                self.accept_samples = False
                self.connected_mono = None
                self.experiment = None
                self.view.clear()
                self.last_samples_mono = None
                self.consent.set(False)
                self.audio_checked = False
                self.heard_audio.set(False)
                self.condition.set("DONE" if self.experiment_completed else "NOT RUNNING")
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.experiment_button.configure(state="disabled")
                self.serial_entry.configure(state="normal")
                self.consent_checkbox.configure(state="normal")
                if not self.status.get().startswith("Capture error"):
                    self.status.set("Disconnected · session ended")
            elif kind == "speech_ok":
                if value == "Audio check. You should hear this message.":
                    self.audio_checked = True
                    self.audio_status.set("Audio test process succeeded (check Windows volume)")
                    self._update_experiment_button()
            elif kind == "speech_error":
                self.audio_checked = False
                self.heard_audio.set(False)
                self.audio_status.set(f"Spoken instruction failed: {value}")
                if self.experiment is not None:
                    self.stop_capture()
                    self.condition.set("ABORTED: AUDIO")

        if self.connected_mono is not None and self.worker is not None:
            if time.monotonic() - self.connected_mono >= MAX_SESSION_SECONDS:
                self.status.set("120-second safety limit reached")
                self.stop_capture()
            elif self.experiment is not None:
                if (self.last_samples_mono is None
                        or time.monotonic() - self.last_samples_mono > 2.):
                    self.stop_capture()
                    self.condition.set("ABORTED: EEG STALLED")
                    self.status.set("EEG stream stalled during guided experiment")
                    self.speaker.say("Experiment stopped. Sensor signal lost.")
                    # The next GUI tick will observe the device release.
                    self.draw()
                    self.root.after(DRAW_INTERVAL_MS, self.tick)
                    return
                epoch = self.now_epoch()
                cues = self.experiment.advance(epoch)
                if self.say_cues(cues):
                    condition = self.experiment.condition(epoch)
                    self.condition.set(condition)
                    if condition == "DONE":
                        self.status.set("Guided experiment finished")
                        self.stop_capture(completed=True)
        if self.last_samples_mono is None or time.monotonic() - self.last_samples_mono > 2:
            self.quality.set("Signal flags: no recent EEG · contact not established")
        else:
            flags = signal_flags(self.view.frames)
            message = " · ".join(f"{label}: {flag}" for label, flag in zip(CHANNELS, flags))
            self.quality.set("Signal flags: " + message +
                             " · heuristic only (UNASSESSED is not a good-contact verdict)")
        self.draw()
        self.root.after(DRAW_INTERVAL_MS, self.tick)

    def draw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        width = max(500, canvas.winfo_width())
        height = max(250, canvas.winfo_height())
        band_height = height / 4
        frames = tuple(self.view.frames)
        for channel, label in enumerate(CHANNELS):
            top = channel * band_height
            center = top + band_height / 2
            canvas.create_line(80, center, width, center, fill="#343b4b", dash=(3, 5))
            canvas.create_text(10, center, anchor="w", text=label,
                               fill=TRACE_COLORS[channel], font=("Segoe UI", 11, "bold"))
            if channel:
                canvas.create_line(0, top, width, top, fill="#2a3040")
            if len(frames) < 2:
                continue
            stride = max(1, math.ceil(len(frames) / 450))
            values = [sample.eeg_uv[channel] for sample in frames[::stride]]
            points = trace_points(values, width=width - 90, height=band_height - 12)
            coords = []
            for x, y in points:
                coords.extend((80 + x, top + 6 + y))
            canvas.create_line(*coords, fill=TRACE_COLORS[channel], width=1.3)

    def on_close(self) -> None:
        self.closing = True
        self.stop_capture()
        if self.worker is None or not self.worker.is_alive():
            self.speaker.close()
            self.root.destroy()


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("MemStack Monitor v0.1 is supported on Windows/Lappy only.")
    import tkinter as tk
    root = tk.Tk()
    MonitorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
