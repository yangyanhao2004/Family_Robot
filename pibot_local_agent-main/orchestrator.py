#!/usr/bin/env python3
"""
Main orchestrator - ties all components together.
"""

import sys
import os
import signal
import time
import random
from pathlib import Path
from typing import Callable, TypeVar

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from audio.audio_manager import AudioManager
from audio.tts_engine import PiperTTS
from audio.stt_engine import WhisperSTT
from brain.ollama_client import OllamaClient
from brain.router import Router, ToolType
from brain.tools.time_tool import get_current_time
from brain.tools.weather_tool import WeatherTool
from brain.tools.news_tool import NewsTool
from brain.tools.system_tool import get_system_status
from brain.tools.joke_tool import get_joke
from brain.cloud_client import KimiClient
from senses.wake_word_detector import WakeWordDetector

# Pre-generated filler WAVs in assets/fillers/
FILLER_WAVS = {
    "On it!": "assets/fillers/filler_0.wav",
    "Thinking...": "assets/fillers/filler_1.wav",
    "Give me a sec.": "assets/fillers/filler_2.wav",
    "Let me check.": "assets/fillers/filler_3.wav",
    "Working on it.": "assets/fillers/filler_4.wav",
}

T = TypeVar("T")


class Orchestrator:
    """Main system orchestrator."""

    def __init__(self, config: Config):
        self.config = config
        self._running = False

        # Initialize components
        print("Initializing Jarvis...")

        # Audio
        print("  - Audio manager")
        self.audio = AudioManager(
            sample_rate=config.target_sample_rate,
            mic_sample_rate=config.mic_sample_rate,
            input_blocksize=config.listen_block_size,
            mic_device_name=config.mic_device_name,
            speaker_device_name=config.speaker_device_name,
        )

        print("  - TTS engine")
        self.tts = PiperTTS(model_path=config.piper_voice)

        print("  - STT engine")
        self.stt = WhisperSTT(
            whisper_path=config.whisper_path,
            model_path=config.whisper_model
        )

        # Brain
        print("  - Ollama client")
        self.ollama = OllamaClient(
            model=config.chat_model,
            timeout=config.ollama_timeout,
            num_predict=config.ollama_num_predict,
            num_ctx=config.ollama_num_ctx,
            temperature=config.ollama_temperature,
            keep_alive=config.ollama_keep_alive
        )

        print("  - Router")
        self.router = Router(
            self.ollama,
            enable_local_llm_routing=config.enable_local_llm_routing,
            allow_cloud_handoff=False,
        )

        # Tools (optional, may fail if API keys not set)
        self.weather = None
        self.cloud = None
        self.news = None

        if config.openweather_api_key:
            print("  - Weather tool")
            try:
                self.weather = WeatherTool(api_key=config.openweather_api_key)
            except Exception as e:
                print(f"    Warning: Weather tool unavailable: {e}")

        if config.newsapi_key:
            print("  - News tool")
            try:
                self.news = NewsTool(api_key=config.newsapi_key)
            except Exception as e:
                print(f"    Warning: News tool unavailable: {e}")

        if config.moonshot_api_key:
            print("  - Cloud client")
            try:
                self.cloud = KimiClient(
                    api_key=config.moonshot_api_key,
                    soul_path=config.cloud_soul_path
                )
                self.router.set_cloud_handoff_enabled(True)
            except Exception as e:
                print(f"    Warning: Cloud client unavailable: {e}")

        print("  - System status tool")
        print("  - Joke tool")

        # Senses
        print("  - Wake word detector")
        self.wake_word = WakeWordDetector(
            wake_word_name=config.wake_word_name,
            model_path=config.wake_word_model,
            threshold=config.wake_word_threshold,
            mic_sample_rate=config.mic_sample_rate,
            mic_device_name=config.mic_device_name,
        )

        # Load pre-generated filler WAVs
        self._filler_wavs = {}
        if config.enable_filler_audio:
            for phrase, rel_path in FILLER_WAVS.items():
                abs_path = os.path.join(config.project_root, rel_path)
                if os.path.exists(abs_path):
                    self._filler_wavs[phrase] = abs_path
                else:
                    print(f"    Warning: Filler WAV missing: {rel_path}")
            if self._filler_wavs:
                print(f"  - Loaded {len(self._filler_wavs)} filler phrases")

        print("Initialization complete!")

    def start(self):
        """Start the assistant."""
        self._running = True

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        if self.config.enable_local_llm_routing and self.config.warm_up_ollama:
            print("Warming up Ollama model...")
            if self.ollama.ensure_model_loaded():
                print("  - Ollama warm-up complete")
            else:
                print("  - Ollama warm-up skipped")
        elif self.config.enable_local_llm_routing and not self.ollama.is_available():
            print("  - Ollama is not reachable at http://localhost:11434")

        if self.config.enable_local_llm_routing and not self.ollama.is_available():
            print("  - Local chat will stay in fallback mode until `ollama serve` is running")
        elif not self.config.enable_local_llm_routing:
            print("  - Local LLM routing is disabled for Pi 4B fast mode")
            print("  - Set `enable_local_llm_routing` to true later if hardware is strong enough")
            if self.cloud:
                print("  - Dialogue will prefer the cloud model")
            else:
                print("  - No cloud key detected, so only rule-based replies and local tools are available")

        # Speak startup message BEFORE starting wake word detection
        # (otherwise the speaker saying "Hey Jarvis" triggers the detector)
        self._speak("Hello! I'm Jarvis. Say hey Jarvis to get my attention.")

        # Start wake word detection after greeting finishes
        self.wake_word.start(callback=self._on_wake_word)

        print("Jarvis is running. Say 'Hey Jarvis' to activate.")
        print("Press Ctrl+C to exit.")

        # Main loop
        while self._running:
            time.sleep(0.1)

        self._cleanup()
        # Force exit to kill any lingering daemon threads (e.g. sounddevice streams)
        os._exit(0)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\nShutting down...")
        self._running = False

    def _cleanup(self):
        """Clean up resources."""
        self.wake_word.stop()

    def _timed(self, label: str, func: Callable[[], T]) -> T:
        """Run a callable and optionally log its duration."""
        start = time.perf_counter()
        result = func()
        if self.config.log_stage_timings:
            elapsed = time.perf_counter() - start
            print("[timing] {}: {:.2f}s".format(label, elapsed))
        return result

    def _on_wake_word(self):
        """Called when wake word is detected."""
        if not self._running:
            return

        print("Wake word detected!")
        total_start = time.perf_counter()

        # Clear conversation history so each wake word starts fresh.
        self.router.clear_history()

        # Pause wake word detection
        self.wake_word.pause()

        # Record user speech
        print("Listening...")
        audio = self._timed(
            "record",
            lambda: self.audio.record_until_silence(
                silence_threshold=self.config.listen_silence_threshold,
                silence_duration=self.config.listen_silence_duration,
                max_duration=self.config.listen_max_duration,
                speech_start_timeout=self.config.listen_speech_start_timeout
            )
        )

        if audio is None or len(audio) == 0:
            print("No speech detected")
            self.wake_word.resume()
            return

        # Transcribe
        print("Transcribing...")
        try:
            text = self._timed("stt", lambda: self.stt.transcribe_audio_array(audio))
            print(f"User said: {text}")
        except Exception as e:
            print(f"Transcription error: {e}")
            self._speak("Sorry, I didn't catch that.")
            self.wake_word.resume()
            return

        if not text.strip():
            self._speak("I didn't hear anything.")
            self.wake_word.resume()
            return

        # Speak a random filler phrase before processing when enabled.
        if self.config.enable_filler_audio:
            self._speak_filler()

        # Route and respond
        try:
            self._timed("response", lambda: self._process_query(text))
        except Exception as e:
            print(f"Processing error: {e}")
            self._speak("Sorry, something went wrong.")
            time.sleep(1)
        finally:
            if self.config.log_stage_timings:
                total_elapsed = time.perf_counter() - total_start
                print("[timing] total interaction: {:.2f}s".format(total_elapsed))

        self.wake_word.resume()

    def _speak_filler(self):
        """Play a random pre-generated filler phrase."""
        if not self._filler_wavs:
            return
        phrase = random.choice(list(self._filler_wavs.keys()))
        wav_path = self._filler_wavs[phrase]
        print(f"Filler: {phrase}")
        try:
            self.audio.play_wav(wav_path)
        except Exception as e:
            print(f"Filler playback error: {e}")

    def _process_query(self, text: str):
        """Process user query through router."""
        result = self._timed("route", lambda: self.router.route(text))

        if result.tool == ToolType.NONE:
            print("[dialogue] Direct chat response")
            self._speak(result.response)

        elif result.tool == ToolType.TIME:
            print("[tool] get_current_time")
            response = get_current_time()
            self._speak(response)

        elif result.tool == ToolType.WEATHER:
            if self.weather:
                location = result.arguments.get("location") or self.config.local_location
                print(f"[tool] get_weather -> {location}")
                response = self.weather.get_weather(location)
                self._speak(response)
            else:
                self._speak("Sorry, weather lookup is not configured.")

        elif result.tool == ToolType.NEWS:
            if self.news:
                category = result.arguments.get("category", "")
                print(f"[tool] get_news -> {category or 'general'}")
                response = self.news.get_news(category)
                self._speak(response)
            else:
                self._speak("Sorry, news lookup is not configured.")

        elif result.tool == ToolType.SYSTEM_STATUS:
            print("[tool] get_system_status")
            response = get_system_status()
            self._speak(response)

        elif result.tool == ToolType.JOKE:
            print("[tool] get_joke")
            response = get_joke()
            self._speak(response)

        elif result.tool == ToolType.CLOUD:
            print("[cloud kimi-k2.5] Handing off to cloud AI")
            query = result.arguments.get("query", text)
            self._handle_cloud_query(query)

    def _handle_cloud_query(self, query: str):
        """Handle cloud API query."""
        if not self.cloud:
            self._speak("Sorry, cloud AI is not configured.")
            return

        try:
            # Non-streaming for simplicity
            response = self.cloud.chat(query, stream=False)
            self._speak(response)
        except Exception as e:
            print(f"Cloud error: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                print("Cloud handoff disabled until the API key is fixed.")
                self.cloud = None
                self.router.set_cloud_handoff_enabled(False)
                self._speak("The cloud AI key is invalid right now, so cloud replies are disabled.")
            else:
                self._speak("Sorry, I couldn't reach the cloud AI.")

    def _speak(self, text: str):
        """Speak text through TTS."""
        if not text:
            return

        print(f"Speaking: {text}")

        try:
            audio_path = self.tts.synthesize(text)
            self.audio.play_wav(audio_path)
        except Exception as e:
            print(f"TTS error: {e}")


def main():
    """Main entry point."""
    config = Config.load()
    orchestrator = Orchestrator(config)
    orchestrator.start()


if __name__ == "__main__":
    main()
