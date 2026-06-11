"""
Configuration management for Jarvis.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent
PATH_FIELDS = ("piper_voice", "whisper_model", "cloud_soul_path")


@dataclass
class Config:
    """Application configuration."""

    # Paths
    project_root: str = str(PROJECT_ROOT)

    # TTS
    piper_voice: str = "piper/voices/en_GB-semaine-medium.onnx"
    edge_tts_voice: str = "zh-CN-XiaoxiaoNeural"  # Microsoft neural Chinese voice

    # Whisper.cpp
    whisper_path: str = "/usr/local/bin/whisper-cpp"
    whisper_model: str = "whisper.cpp/models/ggml-base-q5_1.bin"
    stt_language: str = "zh"
    whisper_threads: int = 4

    # Models
    chat_model: str = "qwen2.5:1.5b"
    ollama_timeout: float = 120.0
    ollama_num_predict: int = 64
    ollama_num_ctx: int = 768
    ollama_temperature: float = 0.5
    ollama_keep_alive: str = "15m"
    warm_up_ollama: bool = True
    # Keep this off on Pi 4B. Turn it on only when hardware is strong enough
    # to run local Ollama replies with acceptable latency.
    enable_local_llm_routing: bool = False

    # Wake word
    wake_word_name: str = "hey_jarvis"
    wake_word_model: str = ""
    wake_word_threshold: float = 0.45

    # Audio device settings
    mic_sample_rate: int = 48000
    mic_device_name: str = "USB PnP Sound Device"
    speaker_device_name: str = "bcm2835 Headphones"

    # Recording controls
    local_location: str = "Kingston, CA"
    target_sample_rate: int = 16000
    listen_silence_threshold: float = 0.02
    listen_silence_duration: float = 0.7
    listen_max_duration: float = 6.0
    listen_speech_start_timeout: float = 2.5
    listen_block_size: int = 2048

    # API keys (loaded from environment)
    openweather_api_key: str = ""
    moonshot_api_key: str = ""
    newsapi_key: str = ""

    # Prompt files
    cloud_soul_path: str = "config/cloud_soul.md"

    # Features
    enable_filler_audio: bool = False
    enable_emotion_detection: bool = True
    log_stage_timings: bool = True

    # External service URLs
    java_backend_url: str = "http://localhost:8090"

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from file and environment."""
        config = cls()

        if config_path is None:
            config_path = str(PROJECT_ROOT / "config" / "config.json")

        if Path(config_path).exists():
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

        config._normalize_paths()

        env_path = Path(config.project_root) / ".env"
        if env_path.exists():
            config._load_env_file(str(env_path))

        config.openweather_api_key = os.getenv(
            "OPENWEATHER_API_KEY",
            config.openweather_api_key,
        )
        config.moonshot_api_key = os.getenv(
            "MOONSHOT_API_KEY",
            config.moonshot_api_key,
        )
        config.newsapi_key = os.getenv(
            "NEWSAPI_KEY",
            config.newsapi_key,
        )
        config.java_backend_url = os.getenv(
            "JAVA_BACKEND_URL",
            config.java_backend_url,
        )

        return config

    def _normalize_paths(self):
        """Resolve project-relative paths into absolute filesystem paths."""
        project_root = Path(self.project_root).expanduser()
        if not project_root.is_absolute():
            project_root = PROJECT_ROOT / project_root
        self.project_root = str(project_root.resolve())

        for field_name in PATH_FIELDS:
            value = getattr(self, field_name)
            if not value:
                continue
            path = Path(value).expanduser()
            if not path.is_absolute():
                path = Path(self.project_root) / path
            setattr(self, field_name, str(path.resolve()))

    def _load_env_file(self, path: str):
        """Load environment variables from a local .env file."""
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

    def _serialize_value(self, key: str, value):
        """Store known project paths relative to the project root."""
        if key not in PATH_FIELDS:
            return value

        try:
            root = Path(self.project_root).resolve()
            return str(Path(value).resolve().relative_to(root))
        except ValueError:
            return value

    def save(self, config_path: Optional[str] = None):
        """Save configuration to file."""
        if config_path is None:
            config_path = str(Path(self.project_root) / "config" / "config.json")

        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for key, value in self.__dict__.items():
            if key == "project_root":
                continue
            if key.endswith("_api_key") or key.endswith("_key"):
                continue
            data[key] = self._serialize_value(key, value)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
