# Product Requirements Document: `pibot_local_agent-main`

**Version:** 3.0  
**Last Updated:** 2026-03-24  
**Status:** Aligned to the current codebase  
**Primary Runtime:** Raspberry Pi 4B 8GB  
**Operating Mode:** Headless voice agent, no local GUI

---

## 1. Purpose

This document defines the current product scope and technical expectations for
`pibot_local_agent-main`.

This repository is the edge-side voice and emotional-companionship subproject of
the larger Family Robot system. Its job is to run on the Raspberry Pi, listen
for a wake word, capture speech, route the request, and speak a response.

This PRD intentionally reflects the code that exists today. It replaces older
research/prototype assumptions such as:

- higher-spec hardware as the only target
- custom wake-word training as the default path
- local fullscreen face UI
- streaming TTS as the primary runtime mode

---

## 2. Product Scope

### 2.1 In Scope

- Always-on wake-word listening using `openWakeWord`
- Default built-in wake word: `hey_jarvis`
- Speech capture after wake-word detection
- Local speech-to-text with `whisper.cpp`
- Local-first response routing
- Fast-path emotional and greeting replies without invoking the local LLM
- Local Ollama-based chat/tool routing for supported queries
- Cloud handoff for complex queries when API credentials are configured
- Text-to-speech playback through Piper
- Headless operation on Raspberry Pi 4B 8GB
- Timing logs for performance tuning

### 2.2 Out of Scope

- Any fullscreen or desktop-covering UI
- PyGame face animation
- Camera display
- WebRTC audio/video calls
- Robot motion control
- Web control integration
- Mandatory custom wake-word training

Those capabilities belong either to the larger Family Robot project or to a
future integration layer.

---

## 3. Target Platform and Constraints

### 3.1 Hardware Target

- Raspberry Pi 4B, 8GB RAM
- 64-bit Raspberry Pi OS
- USB microphone
- USB speaker or 3.5mm speaker output
- Network connection optional for local mode, required for weather/news/cloud

### 3.2 Runtime Constraints

- The system must run without a display
- The system must be stoppable with `Ctrl+C`
- The system must not grab the whole desktop
- Memory and CPU usage must be kept lower than the earlier prototype draft
- Wake-word and common emotional interaction should feel responsive on Pi 4B

### 3.3 Design Direction for Pi 4B

The current codebase is tuned for Pi 4B by default in these ways:

- no GUI/UI subsystem
- built-in `hey_jarvis` wake word
- Ollama warm-up enabled by default
- reduced Ollama generation length and context
- shorter silence detection window
- shorter maximum listen window
- filler audio disabled by default
- fast-path replies for common emotional interaction

---

## 4. User Experience

### 4.1 Main Interaction Flow

1. The device waits for `hey_jarvis`.
2. After wake-word detection, it records the user's speech.
3. Speech is transcribed locally by `whisper.cpp`.
4. The query is routed:
   - common emotional/greeting cases may be answered immediately
   - simple tool requests may be routed without local LLM inference
   - general chat may go to local Ollama
   - complex requests may go to cloud if configured
5. The response is spoken through Piper TTS.
6. The system resumes wake-word listening.

### 4.2 Expected Behavior

- The device should feel like a voice companion, not a kiosk application.
- The default wake word is `hey_jarvis`.
- Emotional companionship is a first-class use case, not only utility Q and A.
- The system should degrade gracefully if cloud APIs are unavailable.

---

## 5. Functional Requirements

### FR-1 Wake Word

- The system shall continuously listen for the built-in wake word `hey_jarvis`.
- The system shall use bundled `openWakeWord` resources by default.
- A custom wake-word model may still be supplied, but it is optional.

### FR-2 Speech Capture

- After wake-word detection, the system shall pause wake-word listening.
- The system shall record microphone input until speech ends or time limits are reached.
- The system shall stop early if no speech starts within the configured timeout.

### FR-3 Speech-to-Text

- The system shall transcribe speech locally using `whisper.cpp`.
- The audio pipeline shall capture at the microphone rate and downsample to the
  target rate required by transcription.

### FR-4 Routing

- The system shall support fast-path responses for common short emotional and
  social interactions.
- The system shall support direct tool routing for:
  - time
  - weather
  - news
  - system status
  - jokes
- The system shall support local LLM chat using Ollama.
- The system shall support cloud handoff for complex requests when configured.

### FR-5 Text-to-Speech

- The system shall synthesize responses locally using Piper TTS.
- The current runtime shall use non-streaming playback.
- Responses are synthesized to a temporary WAV and played back after generation.

### FR-6 Logging and Observability

- The system shall optionally log stage timings.
- When enabled, timing logs shall include at least:
  - record
  - stt
  - response
  - total interaction

### FR-7 Headless Operation

- The system shall not initialize any GUI subsystem.
- The system shall not depend on PyGame.
- The system shall not require SDL or framebuffer configuration.

---

## 6. Current Architecture

### 6.1 Runtime Pipeline

```text
Microphone
  -> WakeWordDetector
  -> AudioManager.record_until_silence()
  -> WhisperSTT
  -> Router
     -> fast-path direct response
     -> local tool path
     -> local Ollama chat
     -> cloud handoff
  -> PiperTTS
  -> AudioManager.play_wav()
  -> resume wake-word listening
```

### 6.2 Module Responsibilities

- `orchestrator.py`
  - boots the system
  - warms Ollama if enabled
  - coordinates wake word, recording, routing, and speaking
- `config.py`
  - defines runtime configuration surface
- `audio/audio_manager.py`
  - microphone recording
  - silence detection
  - muting during playback
  - WAV playback
- `audio/stt_engine.py`
  - wraps `whisper.cpp`
- `audio/tts_engine.py`
  - wraps Piper TTS
- `senses/wake_word_detector.py`
  - wraps `openWakeWord`
  - defaults to bundled `hey_jarvis`
- `brain/router.py`
  - performs fast-path routing and fallback tool detection
  - calls local Ollama when needed
- `brain/ollama_client.py`
  - wraps the Ollama HTTP API
- `brain/cloud_client.py`
  - wraps Moonshot/Kimi cloud chat
- `brain/tools/*`
  - time, weather, news, system status, joke handlers
- `tests/*`
  - component-level validation scripts

### 6.3 Removed Architecture

The following subsystem has been intentionally removed from the current product:

- `ui/`
- PyGame face rendering
- state-driven fullscreen display

This removal is intentional and required for desktop-safe headless operation.

---

## 7. Current File Structure

```text
pibot_local_agent-main/
|-- orchestrator.py
|-- config.py
|-- setup.sh
|-- README.md
|-- PRD.md
|-- .env
|-- .env.example
|-- audio/
|   |-- audio_manager.py
|   |-- stt_engine.py
|   `-- tts_engine.py
|-- brain/
|   |-- cloud_client.py
|   |-- ollama_client.py
|   |-- router.py
|   |-- tool_definitions.py
|   `-- tools/
|-- config/
|   |-- config.json
|   |-- cloud_soul.md
|-- assets/
|   `-- fillers/
|-- models/
|   `-- wake_word/
|-- senses/
|   `-- wake_word_detector.py
`-- tests/
    |-- test_audio_pipeline.py
    |-- test_router.py
    `-- test_wake_word.py
```

---

## 8. Configuration Surface

All runtime configuration is defined by `config.py` and may be overridden by
`config/config.json` and environment variables.

### 8.1 Core Runtime

| Key | Default | Purpose |
|---|---|---|
| `project_root` | auto-detected from the repository root | base project path |
| `chat_model` | `qwen2.5:1.5b` | local Ollama model |
| `ollama_timeout` | `120.0` | Ollama request timeout |
| `ollama_num_predict` | `128` | generation cap tuned for Pi 4B |
| `ollama_num_ctx` | `1024` | reduced context window |
| `ollama_temperature` | `0.5` | response temperature |
| `ollama_keep_alive` | `15m` | keep the model warm in memory |
| `warm_up_ollama` | `true` | warm the model at startup |

### 8.2 Wake Word

| Key | Default | Purpose |
|---|---|---|
| `wake_word_name` | `hey_jarvis` | bundled wake-word name |
| `wake_word_model` | empty | optional custom model path |
| `wake_word_threshold` | `0.45` | wake-word confidence threshold |

### 8.3 Audio Capture

| Key | Default | Purpose |
|---|---|---|
| `mic_sample_rate` | `48000` | microphone native sample rate |
| `mic_device_name` | `USB PnP Sound Device` | input device match string |
| `speaker_device_name` | `bcm2835 Headphones` | output device match string |
| `target_sample_rate` | `16000` | STT target sample rate |
| `listen_silence_threshold` | `0.012` | end-of-speech threshold |
| `listen_silence_duration` | `0.9` | how long quiet must last |
| `listen_max_duration` | `10.0` | hard listen cap |
| `listen_speech_start_timeout` | `2.5` | stop if user never starts speaking |
| `listen_block_size` | `2048` | input block size |

### 8.4 Paths

| Key | Default | Purpose |
|---|---|---|
| `piper_voice` | `piper/voices/en_GB-semaine-medium.onnx` | Piper voice model |
| `whisper_path` | `/usr/local/bin/whisper-cpp` | Whisper executable |
| `whisper_model` | `whisper.cpp/models/ggml-base.en-q5_0.bin` | Whisper model |
| `cloud_soul_path` | `config/cloud_soul.md` | cloud prompt file |

### 8.5 Features and Diagnostics

| Key | Default | Purpose |
|---|---|---|
| `enable_filler_audio` | `false` | filler audio before processing |
| `log_stage_timings` | `true` | timing logs for tuning |

### 8.6 Cloud/API Settings

| Key | Source | Purpose |
|---|---|---|
| `OPENWEATHER_API_KEY` | env or `.env` | weather lookups |
| `NEWSAPI_KEY` | env or `.env` | news tool |
| `MOONSHOT_API_KEY` | env or `.env` | cloud handoff |
| `local_location` | config | default weather fallback |

---

## 9. Runtime Dependencies

### 9.1 System Packages

The current project expects audio- and build-related packages, not GUI packages.

Representative setup:

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-dev \
  build-essential cmake git curl wget \
  portaudio19-dev libasound2-dev \
  alsa-utils
```

### 9.2 Python Packages

```bash
pip install \
  httpx \
  sounddevice \
  numpy \
  piper-tts \
  openwakeword \
  onnxruntime
```

### 9.3 External Runtimes

- Ollama
- `qwen2.5:1.5b`
- `whisper.cpp`
- Piper voice model

PyGame is not part of the current runtime.

---

## 10. Performance Expectations for Pi 4B

### 10.1 Optimization Goals

- common emotional/greeting queries should avoid local LLM latency
- the Ollama model should be warm after startup
- the system should stop listening soon after the user finishes speaking
- no GPU/display/UI overhead should be present

### 10.2 Practical Expectations

On Raspberry Pi 4B 8GB, local LLM performance will still be slower than on
newer and more powerful hardware. The product should therefore prioritize:

- immediate wake-word detection
- shorter speech capture window
- direct-response fast paths
- smaller local generations
- cloud handoff for heavier questions when acceptable

### 10.3 Latency Targets

These are product targets, not hard guarantees:

- wake-word response: near-immediate after detection
- end-of-speech detection: about 1 second after the user stops speaking
- fast-path emotional/greeting replies: noticeably faster than local LLM mode
- local LLM replies: acceptable for Pi 4B, but slower than fast-path/tool mode

---

## 11. Acceptance Criteria

The current project is considered aligned when all of the following are true:

- The agent starts without opening any GUI or fullscreen window.
- The agent can be stopped directly with `Ctrl+C`.
- The default wake word is `hey_jarvis`.
- Wake-word listening resumes after each interaction.
- Common emotional utterances can be answered without requiring local LLM inference.
- Weather/news/cloud behavior degrades gracefully when API keys are missing.
- Timing logs appear when `log_stage_timings` is enabled.
- The codebase contains no runtime dependency on PyGame or a `ui/` package.

---

## 12. Testing Guidance

### 12.1 Component Checks

```bash
python tests/test_audio_pipeline.py
python tests/test_wake_word.py
python tests/test_router.py
```

### 12.2 Manual Runtime Checks

1. Start the agent.
2. Confirm no UI appears.
3. Say `hey jarvis`.
4. Speak a short greeting.
5. Verify the response path is fast and audible.
6. Ask for time or a joke.
7. Stop the process with `Ctrl+C`.

### 12.3 Recommended Pi-Side Diagnostics

- inspect stage timing logs
- validate microphone device names
- validate speaker output path
- validate Ollama warm-up success
- compare fast-path queries vs local LLM queries

---

## 13. Risks and Follow-Up

### 13.1 Current Risks

- Pi 4B local LLM latency may still be too high for some queries
- microphone quality may still dominate wake-word reliability
- weather/news/cloud tools depend on network and external APIs
- device-name matching for microphone/speaker may vary across hardware

### 13.2 Current Mitigations

- bundled `hey_jarvis` wake word instead of a missing custom model
- shorter recording thresholds
- warm Ollama on startup
- reduced generation length and context
- fast-path replies for common social/emotional cases
- headless operation with no UI overhead

### 13.3 Recommended Next Steps

- add Pi-side timing benchmarks for repeated real-world testing
- expose runtime health/status through a lightweight integration API
- evaluate a smaller local model if Pi 4B latency remains unacceptable
- integrate this package into `Family_Robot_pi` as a separate service rather
  than merging all logic into a single monolithic script

---

## 14. Document Authority

This PRD is intended to describe the current implemented product direction of
`pibot_local_agent-main`.

If an older document, research note, or prototype description conflicts with
this PRD, this PRD should be treated as the source of truth for current work.
