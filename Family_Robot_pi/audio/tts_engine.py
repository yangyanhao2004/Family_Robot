"""
TTS engines: Piper (English) and Edge TTS (Chinese via Microsoft neural voices).
"""

import asyncio
import os
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Optional


# ─── Piper TTS (English) ────────────────────────────────────────────────

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
    """Piper TTS engine wrapper (English only)."""

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


# ─── Edge TTS (Chinese / multilingual) ──────────────────────────────────

class EdgeTTS:
    """Microsoft Edge neural TTS via edge-tts (free, no API key needed)."""

    def __init__(
        self,
        voice: str = "zh-CN-XiaoxiaoNeural",
    ):
        self.voice = voice
        self._check_installed()

    @staticmethod
    def _check_installed():
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "edge-tts not installed. Run: pip install edge-tts"
            )

    def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """Synthesize Chinese text into an MP3 file, return its path."""
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)

        try:
            asyncio.run(self._synthesize_async(text, output_path))
        except RuntimeError:
            # If there's already a running event loop, fall back to CLI
            self._synthesize_cli(text, output_path)

        return output_path

    async def _synthesize_async(self, text: str, output_path: str):
        import edge_tts

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)

    def _synthesize_cli(self, text: str, output_path: str):
        """Fallback: use edge-tts CLI."""
        subprocess.run(
            [
                "edge-tts",
                "--voice", self.voice,
                "--text", text,
                "--write-media", output_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
