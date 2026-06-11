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
from threading import Lock
from typing import Callable, TypeVar

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from audio.audio_manager import AudioManager
from audio.tts_engine import EdgeTTS
from audio.stt_engine import WhisperSTT
from audio.emotion_detector import EmotionDetector
from brain.text_sentiment import TextSentiment, fuse_emotions
from brain.ollama_client import OllamaClient
from brain.router import Router, ToolType
from brain.tools.time_tool import get_current_time
from brain.tools.weather_tool import WeatherTool
from brain.tools.news_tool import NewsTool
from brain.tools.system_tool import get_system_status
from brain.tools.joke_tool import get_joke
from brain.voice_commands import enqueue_voice_command
from brain.cloud_client import KimiClient
from brain.session_manager import session_manager
from senses.wake_word_detector import WakeWordDetector

# Pre-generated filler WAVs in assets/fillers/ (English — unused in Chinese mode)
FILLER_WAVS = {
    "好的！": "assets/fillers/filler_0.wav",
    "让我想想...": "assets/fillers/filler_1.wav",
    "稍等一下。": "assets/fillers/filler_2.wav",
    "让我查一下。": "assets/fillers/filler_3.wav",
    "正在处理。": "assets/fillers/filler_4.wav",
}

PI_USER_ID = 0

T = TypeVar("T")


class Orchestrator:
    """Main system orchestrator."""

    def __init__(self, config: Config):
        self.config = config
        self._running = False
        self._state_lock = Lock()
        self._remote_session_active = False
        self._interaction_suspended = False
        self._wake_word_started = False

        # Initialize components
        print("正在初始化贾维斯...")

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
        self.tts = EdgeTTS(voice=config.edge_tts_voice)

        print("  - STT engine")
        self.stt = WhisperSTT(
            whisper_path=config.whisper_path,
            model_path=config.whisper_model,
            language=config.stt_language,
            threads=config.whisper_threads,
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
        print("  - Emotion detector")
        self.emotion = EmotionDetector() if config.enable_emotion_detection else None

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

        # Create persistent Pi chat session for multi-turn conversations
        session_manager.get_or_create(PI_USER_ID)

        print("初始化完成！")

    def start(
        self,
        install_signal_handlers: bool = True,
        force_exit: bool = False,
    ):
        """Start the assistant runtime."""
        self._running = True

        if install_signal_handlers:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

        if self.config.enable_local_llm_routing and self.config.warm_up_ollama:
            print("正在预热 Ollama 模型...")
            if self.ollama.ensure_model_loaded():
                print("  - Ollama 预热完成")
            else:
                print("  - Ollama 预热跳过")
        elif self.config.enable_local_llm_routing and not self.ollama.is_available():
            print("  - Ollama 无法连接 http://localhost:11434")

        if self.config.enable_local_llm_routing and not self.ollama.is_available():
            print("  - 本地对话将保持回退模式，直到 ollama serve 运行")
        elif not self.config.enable_local_llm_routing:
            print("  - 本地 LLM 路由已禁用（Pi 4B 快速模式）")
            print("  - 如果硬件性能足够，可将 enable_local_llm_routing 设为 true")
            if self.cloud:
                print("  - 对话将优先使用云端模型")
            else:
                print("  - 未检测到云端 API Key，仅支持规则回复和本地工具")

        # Speak startup message BEFORE starting wake word detection
        # (otherwise the speaker saying "Hey Jarvis" triggers the detector)
        self._speak("你好！我是贾维斯，你的语音助手。对我说'嘿贾维斯'来唤醒我。")

        # Start wake word detection after greeting finishes
        self.wake_word.start(callback=self._on_wake_word)
        with self._state_lock:
            self._wake_word_started = True

        # If a remote session was already active before startup completed,
        # suspend local emotional chat immediately.
        if self.is_remote_session_active():
            self._suspend_emotional_chat("startup")

        print("贾维斯已启动。说'嘿贾维斯'来唤醒我。")
        print("按 Ctrl+C 退出。")

        # Main loop
        while self._running:
            time.sleep(0.1)

        self._cleanup()
        if force_exit:
            os._exit(0)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n正在关闭...")
        self.stop()

    def stop(self):
        """Stop the assistant loop."""
        self._running = False

    def pause_wake_word_detector(self):
        """Pause wake word detection so WebRTC can take the mic."""
        with self._state_lock:
            if not self._wake_word_started:
                return
        self.wake_word.pause()
        print("[mic] 唤醒词检测已暂停（麦克风释放给 WebRTC）")

    def resume_wake_word_detector(self):
        """Resume wake word detection if system state allows."""
        with self._state_lock:
            if not self._wake_word_started:
                return
            if self._remote_session_active:
                return
        self.wake_word.resume()
        print("[mic] 唤醒词检测已恢复")

    def is_remote_session_active(self) -> bool:
        with self._state_lock:
            return self._remote_session_active

    def set_remote_session_active(self, active: bool):
        active = bool(active)
        with self._state_lock:
            if self._remote_session_active == active:
                return
            self._remote_session_active = active

        if active:
            self._suspend_emotional_chat("remote_session")
        else:
            self._resume_emotional_chat("remote_session")

    def _suspend_emotional_chat(self, reason: str):
        with self._state_lock:
            if self._interaction_suspended:
                return
            self._interaction_suspended = True
            wake_word_started = self._wake_word_started

        print(f"[session] 语音助手已暂停 ({reason})")
        if wake_word_started:
            self.wake_word.pause()

    def _resume_emotional_chat(self, reason: str):
        with self._state_lock:
            if not self._interaction_suspended:
                return
            if self._remote_session_active:
                return
            self._interaction_suspended = False
            wake_word_started = self._wake_word_started

        print(f"[session] 语音助手已恢复 ({reason})")
        if wake_word_started:
            self.wake_word.resume()

    def _resume_wake_word_if_allowed(self):
        with self._state_lock:
            allow = (
                self._running
                and not self._remote_session_active
                and not self._interaction_suspended
                and self._wake_word_started
            )
        if allow:
            self.wake_word.resume()

    def _cleanup(self):
        """Clean up resources."""
        with self._state_lock:
            self._wake_word_started = False
        self.wake_word.stop()
        session_manager.destroy(PI_USER_ID)

    def speak_reminder(self, text: str):
        """Speak a voice reminder via TTS, bypassing remote session check."""
        if not text:
            return
        print(f"提醒播报: {text}")
        try:
            audio_path = self.tts.synthesize(text)
            self.audio.play_wav(audio_path)
        except Exception as e:
            print(f"Reminder TTS error: {e}")

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

        if self.is_remote_session_active():
            print("[session] 远程会话活跃，忽略唤醒词")
            return

        print("检测到唤醒词！")
        total_start = time.perf_counter()

        # Clear conversation history so each wake word starts fresh.
        self.router.clear_history()

        # Pause wake word detection
        self.wake_word.pause()

        # Record user speech
        print("正在聆听...")
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
            print("未检测到语音")
            self._resume_wake_word_if_allowed()
            return

        # Emotion detection (before STT — uses raw audio features)
        emotion_result = None
        if self.emotion is not None:
            emotion_result = self._timed("emotion", lambda: self.emotion.detect(audio))
            if emotion_result:
                print(f"  情感: {emotion_result.label} (置信度 {emotion_result.confidence:.2f})")

        # Transcribe
        print("正在识别...")
        try:
            text = self._timed("stt", lambda: self.stt.transcribe_audio_array(audio))
            print(f"用户说: {text}")
        except Exception as e:
            print(f"识别错误: {e}")
            self._speak("抱歉，我没有听清楚。")
            self._resume_wake_word_if_allowed()
            return

        if not text.strip():
            self._speak("我没有听到声音。")
            self._resume_wake_word_if_allowed()
            return

        # Text sentiment (after STT — TextSentiment handles Trad→Simp internally)
        text_sentiment = TextSentiment.analyze(text)
        print(f"  文本情感: {text_sentiment.label} (极性 {text_sentiment.polarity:+.2f}, 置信度 {text_sentiment.confidence:.2f})")

        # Fuse acoustic + text emotion
        if emotion_result:
            fused_label, fused_conf = fuse_emotions(
                emotion_result.label, emotion_result.confidence,
                text_sentiment.label, text_sentiment.confidence,
            )
            emotion_result.label = fused_label
            emotion_result.confidence = fused_conf
            if fused_label != "neutral":
                print(f"  融合情感: {fused_label} (置信度 {fused_conf:.2f})")

        # Speak a random filler phrase before processing when enabled.
        if self.config.enable_filler_audio:
            self._speak_filler()

        # Route and respond
        try:
            self._timed("response", lambda: self._process_query(text, emotion_result))
        except Exception as e:
            print(f"处理错误: {e}")
            self._speak("抱歉，出了点问题。")
            time.sleep(1)
        finally:
            if self.config.log_stage_timings:
                total_elapsed = time.perf_counter() - total_start
                print("[timing] total interaction: {:.2f}s".format(total_elapsed))

        self._resume_wake_word_if_allowed()

    def _speak_filler(self):
        """Play a random pre-generated filler phrase."""
        if not self._filler_wavs:
            return
        phrase = random.choice(list(self._filler_wavs.keys()))
        wav_path = self._filler_wavs[phrase]
        print(f"填充语: {phrase}")
        try:
            self.audio.play_wav(wav_path)
        except Exception as e:
            print(f"Filler playback error: {e}")

    def _process_query(self, text: str, emotion_result=None):
        """Process user query through router, with optional emotion context."""
        result = self._timed("route", lambda: self.router.route(text))

        session = session_manager.get_or_create(PI_USER_ID)
        session.add_message("user", text)

        if result.tool == ToolType.NONE:
            print("[对话] 直接回复")
            session.add_message("assistant", result.response)
            self._speak(result.response, emotion_result)

        elif result.tool == ToolType.TIME:
            print("[tool] get_current_time")
            response = get_current_time()
            session.add_message("assistant", response)
            self._speak(response, emotion_result)

        elif result.tool == ToolType.WEATHER:
            if self.weather:
                location = result.arguments.get("location") or self.config.local_location
                print(f"[tool] get_weather -> {location}")
                response = self.weather.get_weather(location)
                session.add_message("assistant", response)
                self._speak(response, emotion_result)
            else:
                self._speak("抱歉，天气查询功能未配置。", emotion_result)

        elif result.tool == ToolType.NEWS:
            if self.news:
                category = result.arguments.get("category", "")
                print(f"[tool] get_news -> {category or 'general'}")
                response = self.news.get_news(category)
                session.add_message("assistant", response)
                self._speak(response, emotion_result)
            else:
                self._speak("抱歉，新闻查询功能未配置。", emotion_result)

        elif result.tool == ToolType.SYSTEM_STATUS:
            print("[tool] get_system_status")
            response = get_system_status()
            session.add_message("assistant", response)
            self._speak(response, emotion_result)

        elif result.tool == ToolType.JOKE:
            print("[tool] get_joke")
            response = get_joke()
            session.add_message("assistant", response)
            self._speak(response, emotion_result)

        elif result.tool == ToolType.COMMAND:
            # Set low speed for controlled movement
            enqueue_voice_command("speed_low", 90.0)
            steps = result.arguments.get("steps")
            if steps:
                # Multi-step command
                for step in steps:
                    cmd = step.get("command", "stop")
                    duration = step.get("duration")
                    print(f"[tool] control_robot -> {cmd}" + (f" for {duration}s" if duration else ""))
                    enqueue_voice_command(cmd, 90.0, duration)
            else:
                cmd = result.arguments.get("command", "stop")
                duration = result.arguments.get("duration")
                print(f"[tool] control_robot -> {cmd}" + (f" for {duration}s" if duration else ""))
                enqueue_voice_command(cmd, 90.0, duration)
            explanation = result.arguments.get("explanation", "OK")
            session.add_message("assistant", explanation)
            self._speak(explanation)  # no emotion prefix for commands

        elif result.tool == ToolType.CLOUD:
            print("[云端] 转交云端 AI (kimi-latest)")
            query = result.arguments.get("query", text)
            self._handle_cloud_query(query, emotion_result)

    def _handle_cloud_query(self, query: str, emotion_result=None):
        """Handle cloud API query with multi-turn conversation history."""
        if not self.cloud:
            self._speak("抱歉，云端 AI 未配置。")
            return

        try:
            session = session_manager.get_or_create(PI_USER_ID)

            messages = []
            if self.cloud.soul_prompt:
                soul = self.cloud.soul_prompt
                if emotion_result and emotion_result.label != "neutral":
                    soul += (
                        f"\n\n用户当前情绪状态：{emotion_result.label}（置信度 {emotion_result.confidence:.0%}）。"
                        "请在回复中适当体现共情，但不要刻意强调。"
                    )
                messages.append({"role": "system", "content": soul})
            messages.extend(session.get_messages())

            response = self.cloud.chat_messages(messages)
            session.add_message("assistant", response)
            self._speak(response, emotion_result)
        except Exception as e:
            print(f"云端错误: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                print("云端转交已禁用，等待 API Key 修复。")
                self.cloud = None
                self.router.set_cloud_handoff_enabled(False)
                self._speak("云端 AI 的密钥目前无效，云端回复已禁用。")
            else:
                self._speak("抱歉，无法连接到云端 AI。")

    _EMOTION_PREFIX = {
        "sad": "我感觉到你有些难过。",
        "angry": "我能感受到你的情绪。",
        "fearful": "别担心，我在这里。",
        "happy": "听你心情不错！",
    }

    def _speak(self, text: str, emotion_result=None):
        """Speak text through TTS, with optional empathetic prefix."""
        if not text:
            return

        if self.is_remote_session_active():
            print("[session] 远程会话活跃，跳过本地 TTS")
            return

        # Prepend empathetic prefix for strong emotions
        if emotion_result and emotion_result.label in self._EMOTION_PREFIX and emotion_result.confidence > 0.6:
            prefix = self._EMOTION_PREFIX[emotion_result.label]
            text = f"{prefix}{text}"

        print(f"正在播报: {text}")

        try:
            audio_path = self.tts.synthesize(text)
            self.audio.play_wav(audio_path)
        except Exception as e:
            print(f"TTS error: {e}")


def main():
    """Main entry point."""
    config = Config.load()
    orchestrator = Orchestrator(config)
    orchestrator.start(install_signal_handlers=True, force_exit=False)


if __name__ == "__main__":
    main()
