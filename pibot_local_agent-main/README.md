# pibot_local_agent-main

Headless local-first voice agent for Raspberry Pi 4B 8GB.

For the current Raspberry Pi 4B startup path, prefer
[`DEVELOPER_STARTUP.md`](./DEVELOPER_STARTUP.md).

This project is the edge-side emotional-companionship module of the larger
Family Robot system. It listens for a wake word, records speech, transcribes it
locally, routes the request, and speaks a response back.

The current default wake word is `hey_jarvis`.

## Current Status

This repository is aligned to the current codebase, not to the older prototype.

Current behavior:

- runs on Raspberry Pi 4B 8GB
- runs headless, with no fullscreen UI
- uses bundled `openWakeWord` `hey_jarvis` by default
- uses local `whisper.cpp` for STT
- uses local Piper for TTS
- uses Ollama for local chat and tool routing
- supports cloud handoff for complex requests when configured
- includes Pi 4B-oriented latency optimizations

Removed from the current runtime:

- PyGame face UI
- fullscreen display behavior
- mandatory custom wake-word training

## Architecture

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

## Main Features

- Wake word: built-in `hey_jarvis`
- Fast-path replies for greetings and common emotional interaction
- Local chat through `qwen2.5:1.5b`
- Time, weather, news, system-status, and joke tools
- Optional cloud handoff through Moonshot/Kimi
- Timing logs for performance tuning

## Hardware Requirements

- Raspberry Pi 4B, 8GB RAM recommended
- 64-bit Raspberry Pi OS
- USB microphone
- USB speaker or 3.5mm speaker output
- microSD card or other supported storage

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd pibot_local_agent-main
```

### 2. Run the install script

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Add optional API keys

```bash
cp .env.example .env
nano .env
```

Optional keys:

- `OPENWEATHER_API_KEY`
- `NEWSAPI_KEY`
- `MOONSHOT_API_KEY`

### 4. Start the agent

```bash
source venv313/bin/activate
python orchestrator.py
```

Then say `hey jarvis`.

## Manual Installation

### 1. System packages

```bash
sudo apt update && sudo apt install -y \
  python3 python3-venv python3-dev \
  build-essential cmake git curl wget \
  portaudio19-dev libasound2-dev \
  alsa-utils
```

### 2. Python environment

```bash
python3 -m venv venv313
source venv313/bin/activate
pip install --upgrade pip
```

### 3. Python dependencies

```bash
pip install \
  httpx \
  sounddevice \
  numpy \
  piper-tts \
  openwakeword \
  onnxruntime
```

### 4. Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b
```

### 5. Whisper.cpp

```bash
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
cmake -B build
cmake --build build --config Release
sudo cp build/bin/whisper-cli /usr/local/bin/whisper-cpp
bash models/download-ggml-model.sh base.en
./build/bin/quantize models/ggml-base.en.bin models/ggml-base.en-q5_0.bin q5_0
cd ..
```

### 6. Piper voice

```bash
mkdir -p piper/voices
wget -O piper/voices/en_GB-semaine-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx
wget -O piper/voices/en_GB-semaine-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx.json
```

## Wake Word

The current default configuration uses the bundled `openWakeWord` model name
`hey_jarvis`.

You do not need a custom wake-word model to run the current project.

If you want to experiment with a custom model later, you can still provide a
path through `wake_word_model`, but that is optional.

## Project Structure

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

## Important Configuration

Runtime settings are defined in `config.py` and overridden by
`config/config.json`.

Key values:

| Setting | Default | Meaning |
|---|---|---|
| `chat_model` | `qwen2.5:1.5b` | local Ollama model |
| `wake_word_name` | `hey_jarvis` | bundled wake word |
| `wake_word_threshold` | `0.45` | wake-word threshold |
| `mic_device_name` | `USB PnP Sound Device` | input device match string |
| `speaker_device_name` | `bcm2835 Headphones` | output device match string |
| `ollama_num_predict` | `128` | shorter local generations |
| `ollama_num_ctx` | `1024` | reduced local context |
| `warm_up_ollama` | `true` | warm model at startup |
| `listen_silence_duration` | `0.9` | speech-end silence window |
| `listen_max_duration` | `10.0` | max capture duration |
| `enable_filler_audio` | `false` | filler audio before processing |
| `log_stage_timings` | `true` | timing logs |

## Pi 4B Optimizations Already Applied

The current branch includes these optimizations for Raspberry Pi 4B:

- headless runtime with no UI overhead
- bundled `hey_jarvis` wake word
- configurable mic and speaker device names
- Ollama warm-up on startup
- lower `num_predict`
- lower context size
- shorter silence detection
- speech-start timeout
- fast-path emotional and greeting replies
- filler audio disabled by default

## Testing

```bash
source venv313/bin/activate
python tests/test_audio_pipeline.py
python tests/test_wake_word.py
python tests/test_router.py
```

## Troubleshooting

| Problem | What to check |
|---|---|
| Wake word is unreliable | check microphone quality, device name matching, and `wake_word_threshold` |
| No audio input | run `arecord -l` and verify the mic name in `audio/audio_manager.py` and `senses/wake_word_detector.py` |
| No audio output | run `aplay -l` and verify the speaker name in `audio/audio_manager.py` |
| `whisper-cpp` not found | confirm `whisper_path` in `config/config.json` |
| Ollama is slow on Pi 4B | inspect timing logs and consider an even smaller local model |
| Cloud tools say not configured | add the matching key in `.env` |

## Notes

- This README is intended to match the current codebase.
- The source-of-truth product description is in `PRD.md`.
- If older notes or prototype descriptions conflict with this README, prefer
  the current `README.md` and `PRD.md`.
