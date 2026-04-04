"""
Wake word detection using openWakeWord.
"""

import os
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Thread
from typing import Callable, Optional

import numpy as np
import sounddevice as sd


# Force CPU inference on Raspberry Pi.
os.environ["ORT_DISABLE_CUDA"] = "1"

try:
    import openwakeword
    from openwakeword.model import Model

    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False


DEFAULT_MIC_NAME = "USB PnP Sound Device"


def _find_mic_device(name_substring: str) -> Optional[int]:
    """Find the microphone device index by partial name."""
    if not name_substring:
        return None

    devices = sd.query_devices()
    for index, device in enumerate(devices):
        if (
            name_substring.lower() in device["name"].lower()
            and device["max_input_channels"] > 0
        ):
            return index

    raise RuntimeError(
        "Mic '{}' not found. Available: {}".format(
            name_substring,
            [(i, d["name"]) for i, d in enumerate(devices)],
        )
    )


def _find_bundled_model(name: str) -> str:
    """Find a bundled openWakeWord model by name."""
    pkg_dir = Path(openwakeword.__file__).parent / "resources" / "models"
    for model_path in pkg_dir.glob("{}*.onnx".format(name)):
        return str(model_path)
    raise FileNotFoundError(
        "Bundled model {} not found in {}".format(name, pkg_dir)
    )


class WakeWordDetector:
    """Detect a wake word using openWakeWord."""

    def __init__(
        self,
        wake_word_name: str = "hey_jarvis",
        model_path: str = "",
        threshold: float = 0.5,
        sample_rate: int = 16000,
        mic_sample_rate: int = 48000,
        gain_target_peak: float = 0.9,
        mic_device_name: str = DEFAULT_MIC_NAME,
    ):
        if not OPENWAKEWORD_AVAILABLE:
            raise RuntimeError(
                "openwakeword not installed. Run: pip install openwakeword"
            )

        self.wake_word_name = wake_word_name
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.mic_sample_rate = mic_sample_rate
        self.gain_target_peak = gain_target_peak
        self.mic_device_name = mic_device_name
        self.mic_chunk_size = int(1280 * (self.mic_sample_rate / self.sample_rate))

        self.mic_device = _find_mic_device(self.mic_device_name)
        if self.mic_device is None:
            print("    Wake word mic: default input device")
        else:
            print(
                "    Wake word mic: device {} ({})".format(
                    self.mic_device,
                    self.mic_device_name,
                )
            )

        if model_path and Path(model_path).exists():
            self.model = Model(wakeword_model_paths=[model_path])
        else:
            bundled_model_path = _find_bundled_model(self.wake_word_name)
            self.model = Model(wakeword_model_paths=[bundled_model_path])
            print("    Wake word model: bundled {}".format(self.wake_word_name))

        self._running = False
        self._stop_event = Event()
        self._resume_event = Event()
        self._thread: Optional[Thread] = None
        self._callback: Optional[Callable] = None
        self._paused = False
        self._audio_queue: Queue = Queue(maxsize=8)
        self._gain = 6.0

    def start(self, callback: Callable[[], None]):
        """Start listening for the wake word."""
        self._callback = callback
        self._running = True
        self._paused = False
        self._stop_event.clear()
        self._resume_event.set()

        self._thread = Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop listening."""
        self._running = False
        self._stop_event.set()
        self._resume_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def pause(self):
        """Pause detection and release the microphone stream."""
        self._paused = True
        self._resume_event.clear()

    def resume(self):
        """Resume detection and reopen the microphone stream."""
        self._paused = False
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except Empty:
                break
        self._resume_event.set()

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        """Apply adaptive gain normalization for weak microphones."""
        peak = np.max(np.abs(audio))
        if peak < 50:
            return audio.astype(np.int16)

        target = self.gain_target_peak * 32767
        desired_gain = target / peak
        desired_gain = min(desired_gain, 15.0)
        self._gain = 0.3 * desired_gain + 0.7 * self._gain
        self._gain = min(self._gain, 15.0)
        gained = np.clip(audio * self._gain, -32768, 32767)
        return gained.astype(np.int16)

    def _listen_loop(self):
        """Listen continuously, reopening the stream after pause/resume."""
        while self._running:
            self._resume_event.wait()
            if not self._running:
                break

            while not self._audio_queue.empty():
                try:
                    self._audio_queue.get_nowait()
                except Empty:
                    break

            def audio_callback(indata, frames, time_info, status):
                try:
                    self._audio_queue.put_nowait(bytes(indata))
                except Full:
                    try:
                        self._audio_queue.get_nowait()
                    except Empty:
                        pass
                    try:
                        self._audio_queue.put_nowait(bytes(indata))
                    except Full:
                        pass

            try:
                stream = sd.RawInputStream(
                    device=self.mic_device,
                    samplerate=self.mic_sample_rate,
                    channels=1,
                    dtype="int16",
                    blocksize=self.mic_chunk_size,
                    latency="high",
                    callback=audio_callback,
                )
                stream.start()
            except Exception as e:
                print("Wake word stream error: {}".format(e))
                if self._running:
                    self._stop_event.wait(timeout=1.0)
                continue

            detected = False
            while self._running and not self._paused:
                try:
                    raw = self._audio_queue.get(timeout=0.1)
                except Empty:
                    continue

                audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                normalized = self._normalize(audio)
                decimated = normalized[::3]
                predictions = self.model.predict(decimated)

                for model_name, score in predictions.items():
                    if score >= self.threshold:
                        print(
                            "Wake word detected! ({}, score: {:.3f})".format(
                                model_name,
                                score,
                            )
                        )
                        detected = True
                        break

                if detected:
                    break

            stream.stop()
            stream.close()

            if detected and self._callback:
                self._paused = True
                self._resume_event.clear()
                self.model.reset()
                self._callback()
