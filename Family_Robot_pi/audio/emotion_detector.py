"""
Lightweight speech emotion recognition — pure numpy, no ML deps.

Pipeline:  audio (16kHz int16) → acoustic features → heuristic classifier
Latency:  ~50 ms on Pi 4B for a 4-second utterance.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmotionResult:
    label: str       # "happy", "sad", "angry", "neutral", "fearful"
    confidence: float  # 0–1
    features: dict    # raw acoustic stats for debugging


class EmotionDetector:
    """Speech emotion recognition from raw audio."""

    SAMPLE_RATE = 16000
    FRAME_MS = 25
    HOP_MS = 10
    PREEMPH = 0.97

    def __init__(self):
        self.frame_len = int(self.SAMPLE_RATE * self.FRAME_MS / 1000)
        self.hop_len = int(self.SAMPLE_RATE * self.HOP_MS / 1000)

    def detect(self, audio: np.ndarray) -> Optional[EmotionResult]:
        """
        Detect emotion from a 16kHz int16 or float32 mono audio array.

        Returns None if the audio is too short or silent.
        """
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        else:
            audio = audio.astype(np.float32)

        # Trim leading / trailing silence
        audio = np.trim_zeros(audio, trim="fb")
        if len(audio) < self.frame_len * 2:
            return None  # too short

        # Pre-emphasis
        audio = np.append(audio[0], audio[1:] - self.PREEMPH * audio[:-1])

        # Frame-level features
        rms_list, zcr_list, centroid_list, pitch_list = [], [], [], []
        n_frames = (len(audio) - self.frame_len) // self.hop_len + 1

        for i in range(n_frames):
            start = i * self.hop_len
            frame = audio[start : start + self.frame_len]
            rms = np.sqrt(np.mean(frame ** 2) + 1e-12)

            if rms < 0.005:  # silence frame
                rms_list.append(0.0)
                zcr_list.append(0.0)
                centroid_list.append(0.0)
                pitch_list.append(0.0)
                continue

            rms_list.append(rms)
            zcr_list.append(self._zcr(frame))
            centroid_list.append(self._spectral_centroid(frame))
            pitch_list.append(self._pitch_acf(frame))

        rms = np.array(rms_list)
        zcr = np.array(zcr_list)
        centroid = np.array(centroid_list)
        pitch = np.array(pitch_list)

        # Voice-activity frames only (for pitch / energy stats)
        voice_mask = rms > np.mean(rms) * 0.3
        voice_rms = rms[voice_mask]
        voice_pitch = pitch[voice_mask & (pitch > 80)]

        if len(voice_rms) < 3:
            return EmotionResult("neutral", 0.5, {})

        # ---- Aggregate features ----
        energy_mean = float(np.mean(voice_rms))
        energy_std = float(np.std(voice_rms))
        pitch_mean = float(np.mean(voice_pitch)) if len(voice_pitch) else 120.0
        pitch_std = float(np.std(voice_pitch)) if len(voice_pitch) else 0.0
        zcr_mean = float(np.mean(zcr[voice_mask]))
        centroid_mean = float(np.mean(centroid[voice_mask]))
        speech_rate = len(self._energy_peaks(rms, voice_mask)) / max(len(audio) / self.SAMPLE_RATE, 0.1)

        features = {
            "energy_mean": energy_mean,
            "energy_std": energy_std,
            "pitch_mean": pitch_mean,
            "pitch_std": pitch_std,
            "zcr_mean": zcr_mean,
            "centroid_mean": centroid_mean,
            "speech_rate": speech_rate,
        }

        # ---- Heuristic classifier ----
        label, conf = self._classify(features)
        return EmotionResult(label, conf, features)

    # ── per-frame helpers ──────────────────────────────────────

    def _zcr(self, frame: np.ndarray) -> float:
        return float(np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame)))

    def _spectral_centroid(self, frame: np.ndarray) -> float:
        mag = np.abs(np.fft.rfft(frame * np.hanning(len(frame))))
        freqs = np.fft.rfftfreq(len(frame), 1.0 / self.SAMPLE_RATE)
        s = np.sum(mag)
        return float(np.sum(freqs * mag) / (s + 1e-12)) if s > 0 else 0.0

    def _pitch_acf(self, frame: np.ndarray) -> float:
        """Pitch via autocorrelation (50–500 Hz range)."""
        x = frame * np.hanning(len(frame))
        acf = np.correlate(x, x, mode="full")
        acf = acf[len(acf) // 2:]  # take positive lags
        acf = acf / (acf[0] + 1e-12)

        lo = int(self.SAMPLE_RATE / 500)   # 500 Hz
        hi = int(self.SAMPLE_RATE / 50)    # 50 Hz
        if hi <= lo or hi >= len(acf):
            return 0.0
        region = acf[lo:hi]
        peak_idx = lo + int(np.argmax(region))
        peak_val = acf[peak_idx]

        if peak_val < 0.3:
            return 0.0  # unvoiced or ambiguous
        return self.SAMPLE_RATE / peak_idx

    @staticmethod
    def _energy_peaks(rms: np.ndarray, voice_mask: np.ndarray, min_dist: int = 10) -> list:
        """Count syllable-like energy peaks in voiced segments."""
        v = rms.copy()
        v[~voice_mask] = 0.0
        thresh = np.mean(rms[voice_mask]) * 1.2 if np.any(voice_mask) else 0.01
        peaks = []
        i = 0
        while i < len(v) - 2:
            if v[i] > thresh and v[i] >= v[i - 1] and v[i] >= v[i + 1]:
                peaks.append(i)
                i += min_dist
            else:
                i += 1
        return peaks

    # ── classification ────────────────────────────────────────

    @staticmethod
    def _classify(f: dict):
        """
        Heuristic emotion classifier.

        Decision logic:
          angry   — high energy, high pitch std, fast rate
          happy   — high pitch, high energy, fast rate
          sad     — low pitch, low energy, slow rate
          fearful — high pitch, high energy variation, normal rate
          neutral — everything else
        """
        e_mean = f["energy_mean"]
        e_std = f["energy_std"]
        p_mean = f["pitch_mean"]
        p_std = f["pitch_std"]
        zcr = f["zcr_mean"]
        rate = f["speech_rate"]

        # Thresholds tuned for Chinese speech (higher natural F0 than English)
        high_energy = e_mean > 0.08
        low_energy = e_mean < 0.018
        high_pitch = p_mean > 230       # Chinese: higher baseline
        low_pitch = p_mean < 130        # Chinese: higher baseline
        very_high_pitch_var = p_std > 55
        high_pitch_var = p_std > 40
        fast = rate > 5.5
        slow = rate < 2.2

        if high_energy and very_high_pitch_var and fast:
            return "angry", 0.75
        if high_pitch and high_energy and fast:
            return "happy", 0.78
        if high_pitch and high_pitch_var and not high_energy and not slow:
            return "fearful", 0.60
        if low_pitch and low_energy:
            return "sad", 0.75
        if low_energy and slow:
            return "sad", 0.65

        # Default
        return "neutral", 0.72
