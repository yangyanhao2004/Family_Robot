"""
Piper TTS wrapper using the piper-tts Python package.
"""

import os
import tempfile
import wave
from pathlib import Path
from typing import Optional

try:
    from piper import PiperVoice
    from piper.voice import SynthesisConfig

    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VOICE_PATH = PROJECT_ROOT / "piper" / "voices" / "en_GB-semaine-medium.onnx"
LEGACY_VOICE_DIRS = [
    Path("/home/ip/piper/voices"),
    Path.home() / "piper" / "voices",
]


def _resolve_voice_path(model_path: str) -> Path:
    """Resolve the Piper voice model from current or legacy locations."""
    requested = Path(model_path).expanduser()
    candidates = []

    if requested.is_absolute():
        candidates.append(requested)
    else:
        candidates.append(PROJECT_ROOT / requested)
        candidates.extend(legacy_dir / requested.name for legacy_dir in LEGACY_VOICE_DIRS)

    if requested.is_absolute():
        candidates.extend(legacy_dir / requested.name for legacy_dir in LEGACY_VOICE_DIRS)
    else:
        candidates.append(requested)

    seen = set()
    ordered_candidates = []
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        candidate_key = str(resolved)
        if candidate_key not in seen:
            seen.add(candidate_key)
            ordered_candidates.append(resolved)

    for candidate in ordered_candidates:
        if candidate.exists():
            return candidate

    searched = "\n".join(f"  - {path}" for path in ordered_candidates)
    raise FileNotFoundError(
        "Voice model not found. Checked:\n{}".format(searched)
    )


class PiperTTS:
    """Piper TTS engine wrapper."""

    def __init__(
        self,
        model_path: str = str(DEFAULT_VOICE_PATH),
        speaker_id: int = 0,
    ):
        self.speaker_id = speaker_id
        self.model_path = str(_resolve_voice_path(model_path))

        if not PIPER_AVAILABLE:
            raise RuntimeError(
                "piper-tts package not installed. Run: pip install piper-tts"
            )

        self._voice = PiperVoice.load(self.model_path)

    def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """Synthesize text into a WAV file and return its path."""
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        syn_config = SynthesisConfig(speaker_id=self.speaker_id)
        with wave.open(output_path, "wb") as wav_file:
            self._voice.synthesize_wav(text, wav_file, syn_config=syn_config)

        return output_path
