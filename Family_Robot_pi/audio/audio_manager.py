"""
Audio manager for microphone capture and speaker playback.
"""

import subprocess
import time
import wave
from threading import Lock
from typing import Optional

import numpy as np
import sounddevice as sd


DEFAULT_MIC_NAME = "USB PnP Sound Device"
DEFAULT_SPEAKER_NAME = "bcm2835 Headphones"


def _find_device_by_name(name_substring: str, kind: str) -> Optional[int]:
    """Find a sounddevice index by partial device name."""
    if not name_substring:
        return None

    devices = sd.query_devices()
    channel_key = "max_input_channels" if kind == "input" else "max_output_channels"
    for index, device in enumerate(devices):
        if (
            name_substring.lower() in device["name"].lower()
            and device[channel_key] > 0
        ):
            return index

    raise RuntimeError(
        "Audio device matching '{}' ({}) not found. Available: {}".format(
            name_substring,
            kind,
            [(i, d["name"]) for i, d in enumerate(devices)],
        )
    )


def _find_alsa_card_by_name(name_substring: str) -> str:
    """Find an ALSA playback device by partial card name."""
    if not name_substring:
        return "default"

    try:
        result = subprocess.run(
            ["aplay", "-l"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            line_lower = line.lower()
            if line.startswith("card ") and name_substring.lower() in line_lower:
                card_num = line.split(":")[0].replace("card ", "").strip()
                return "plughw:{},0".format(card_num)
    except Exception:
        pass

    raise RuntimeError(
        "Speaker '{}' not found in ALSA device list.".format(name_substring)
    )


class AudioManager:
    """Manage microphone input and speaker playback with mic muting."""

    def __init__(
        self,
        sample_rate: int = 16000,
        mic_sample_rate: int = 48000,
        channels: int = 1,
        dtype: str = "int16",
        input_blocksize: int = 2048,
        input_latency: str = "high",
        mic_device_name: str = DEFAULT_MIC_NAME,
        speaker_device_name: str = DEFAULT_SPEAKER_NAME,
    ):
        self.sample_rate = sample_rate
        self.mic_sample_rate = mic_sample_rate
        self.channels = channels
        self.dtype = dtype
        self.input_blocksize = input_blocksize
        self.input_latency = input_latency
        self.mic_device_name = mic_device_name
        self.speaker_device_name = speaker_device_name
        self.is_muted = False
        self._mute_lock = Lock()
        self._recording = False
        self._audio_buffer = []

        self.mic_device = _find_device_by_name(self.mic_device_name, "input")
        self.speaker_alsa = _find_alsa_card_by_name(self.speaker_device_name)

        if self.mic_device is None:
            print("    Mic: default input device")
        else:
            print(
                "    Mic: device {} ({})".format(
                    self.mic_device,
                    self.mic_device_name,
                )
            )
        print(
            "    Speaker: {} ({})".format(
                self.speaker_alsa,
                self.speaker_device_name or "default",
            )
        )

    def mute(self):
        """Mute microphone input during playback."""
        with self._mute_lock:
            self.is_muted = True

    def unmute(self):
        """Unmute microphone input."""
        with self._mute_lock:
            self.is_muted = False

    def _normalize(self, audio: np.ndarray, target_peak: float = 0.9) -> np.ndarray:
        """Apply gain normalization for weak USB microphones."""
        peak = np.max(np.abs(audio.astype(np.float64)))
        if peak < 50:
            return audio
        gain = (target_peak * 32767) / peak
        return np.clip(audio.astype(np.float64) * gain, -32768, 32767).astype(np.int16)

    def record_until_silence(
        self,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        max_duration: float = 30.0,
        speech_start_timeout: float = 2.5,
    ) -> Optional[np.ndarray]:
        """
        Record until speech ends or until speech never starts.
        """
        if self.is_muted:
            return None

        self._audio_buffer = []
        self._recording = True
        speech_started = False
        blocksize = self.input_blocksize
        poll_ms = max(20, int((blocksize / self.mic_sample_rate) * 1000))
        start_time = time.perf_counter()
        last_speech_time = None
        noise_floor = max(silence_threshold * 0.5, 0.001)

        def callback(indata, frames, time_info, status):
            if status:
                return
            if self.is_muted or not self._recording:
                return
            self._audio_buffer.append(indata.copy())

        stream = sd.InputStream(
            device=self.mic_device,
            samplerate=self.mic_sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=blocksize,
            latency=self.input_latency,
            callback=callback,
        )
        stream.start()

        try:
            while self._recording:
                sd.sleep(poll_ms)
                now = time.perf_counter()

                if (now - start_time) >= max_duration:
                    break

                if not self._audio_buffer:
                    if (now - start_time) >= speech_start_timeout:
                        break
                    continue

                recent = self._audio_buffer[-1]
                rms = np.sqrt(np.mean(recent.astype(np.float32) ** 2)) / 32768
                if not speech_started:
                    noise_floor = 0.9 * noise_floor + 0.1 * rms
                elif rms < max(silence_threshold * 1.5, noise_floor * 2.0):
                    noise_floor = 0.98 * noise_floor + 0.02 * rms

                effective_threshold = max(
                    silence_threshold,
                    min(noise_floor * 2.5, 0.03),
                )

                if rms >= effective_threshold:
                    speech_started = True
                    last_speech_time = now
                elif speech_started and last_speech_time is not None:
                    if (now - last_speech_time) >= silence_duration:
                        break
                else:
                    if (now - start_time) >= speech_start_timeout:
                        break
        finally:
            stream.stop()
            stream.close()

        self._recording = False

        if not self._audio_buffer or not speech_started:
            return None

        raw_audio = np.concatenate(self._audio_buffer, axis=0).flatten()
        normalized = self._normalize(raw_audio)
        return normalized[::3]

    def save_to_wav(self, audio: np.ndarray, filepath: str):
        """Save audio array to a WAV file."""
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())

    def play_wav(self, filepath: str):
        """Play a WAV file through the configured speaker."""
        self.mute()
        try:
            subprocess.run(
                ["aplay", "-D", self.speaker_alsa, filepath],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError:
            import wave as wav_mod

            with wav_mod.open(filepath, "rb") as wf:
                audio_data = np.frombuffer(
                    wf.readframes(wf.getnframes()),
                    dtype=np.int16,
                )
                sd.play(audio_data, wf.getframerate())
                sd.wait()
        except Exception as e:
            print("Playback error: {}".format(e))
        finally:
            self.unmute()

    def play_audio(self, audio: np.ndarray):
        """Play an in-memory audio array."""
        self.mute()
        try:
            sd.play(audio, self.sample_rate)
            sd.wait()
        finally:
            self.unmute()
