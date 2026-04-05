"""
Whisper.cpp STT wrapper.
"""

import os
import subprocess
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WHISPER_PATH = Path("/usr/local/bin/whisper-cpp")
DEFAULT_WHISPER_MODEL = PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-tiny.en-q5_0.bin"
ALT_WHISPER_PATHS = [
    PROJECT_ROOT / "whisper.cpp" / "build" / "bin" / "whisper-cli",
    Path("/home/ip/whisper.cpp/build/bin/whisper-cli"),
]
LEGACY_WHISPER_MODEL_DIRS = [
    Path("/home/ip/whisper.cpp/models"),
    Path.home() / "whisper.cpp" / "models",
]
FAST_MODEL_NAMES = [
    "ggml-tiny.en-q5_0.bin",
    "ggml-tiny.en.bin",
    "ggml-base.en-q5_0.bin",
    "ggml-base.en.bin",
]


def _resolve_whisper_binary(whisper_path: str) -> Path:
    """Resolve the whisper binary from common install locations."""
    requested = Path(whisper_path).expanduser()
    candidates = [requested]
    if not requested.is_absolute():
        candidates.append(PROJECT_ROOT / requested)
    candidates.extend(ALT_WHISPER_PATHS)

    seen = set()
    ordered = []
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            ordered.append(resolved)

    for candidate in ordered:
        if candidate.exists():
            return candidate

    searched = "\n".join(f"  - {path}" for path in ordered)
    raise FileNotFoundError("Whisper binary not found. Checked:\n{}".format(searched))


def _build_model_candidates(model_path: str):
    """Build an ordered candidate list for Whisper model lookup."""
    requested = Path(model_path).expanduser()
    candidates = []

    if requested.is_absolute():
        candidates.append(requested)
        candidates.extend(legacy_dir / requested.name for legacy_dir in LEGACY_WHISPER_MODEL_DIRS)
        if requested.name in FAST_MODEL_NAMES:
            candidates.extend(
                legacy_dir / model_name
                for model_name in FAST_MODEL_NAMES
                for legacy_dir in LEGACY_WHISPER_MODEL_DIRS
            )
    else:
        candidates.append(PROJECT_ROOT / requested)
        candidates.append(requested)
        candidates.extend(legacy_dir / requested.name for legacy_dir in LEGACY_WHISPER_MODEL_DIRS)
        if requested.name in FAST_MODEL_NAMES:
            candidates.extend(
                (PROJECT_ROOT / "whisper.cpp" / "models" / model_name)
                for model_name in FAST_MODEL_NAMES
            )
            candidates.extend(
                legacy_dir / model_name
                for model_name in FAST_MODEL_NAMES
                for legacy_dir in LEGACY_WHISPER_MODEL_DIRS
            )

    seen = set()
    ordered = []
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            ordered.append(resolved)

    return ordered


def _resolve_whisper_model(model_path: str) -> Path:
    """Resolve the Whisper model from current or legacy locations."""
    candidates = _build_model_candidates(model_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched = "\n".join(f"  - {path}" for path in candidates)
    raise FileNotFoundError("Whisper model not found. Checked:\n{}".format(searched))


class WhisperSTT:
    """Whisper.cpp speech-to-text engine."""

    def __init__(
        self,
        whisper_path: str = str(DEFAULT_WHISPER_PATH),
        model_path: str = str(DEFAULT_WHISPER_MODEL),
        language: str = "en",
        threads: int = 4,
    ):
        self.whisper_path = str(_resolve_whisper_binary(whisper_path))
        self.model_path = str(_resolve_whisper_model(model_path))
        self.language = language
        self.threads = threads
        print("    Whisper model: {}".format(Path(self.model_path).name))

    def transcribe(self, audio_path: str) -> str:
        """Transcribe a WAV file into text."""
        process = subprocess.run(
            [
                self.whisper_path,
                "-m",
                self.model_path,
                "-f",
                audio_path,
                "-l",
                self.language,
                "-t",
                str(self.threads),
                "--no-timestamps",
                "-np",
            ],
            capture_output=True,
            text=True,
        )

        if process.returncode != 0:
            raise RuntimeError(f"Whisper failed: {process.stderr}")

        return process.stdout.strip().replace("[BLANK_AUDIO]", "").strip()

    def transcribe_audio_array(self, audio, sample_rate: int = 16000) -> str:
        """Transcribe speech from an in-memory audio array."""
        import wave

        temp_dir = "/dev/shm" if Path("/dev/shm").exists() else None
        fd, temp_path = tempfile.mkstemp(suffix=".wav", dir=temp_dir)
        os.close(fd)

        try:
            with wave.open(temp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio.tobytes())

            return self.transcribe(temp_path)
        finally:
            os.unlink(temp_path)
