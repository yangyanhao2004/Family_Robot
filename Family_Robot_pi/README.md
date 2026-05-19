# Family_Robot_pi

Unified Pi runtime — FastAPI backend + voice assistant + remote WebSocket client.

## Structure

```
Family_Robot_pi/
├── main.py                  # Unified launcher (--mode all|voice|remote)
├── orchestrator.py          # Voice pipeline: wake-word → STT → router → TTS
├── config.py                # Config dataclass (file + env loading)
├── config/                  # Static config files (config.json, cloud_soul.md)
│
├── backend/                 # FastAPI real-time relay (port 8080)
│   ├── app.py               # FastAPI app: /ws, /ws/rtc, /video/stream
│   ├── core/                # ConnectionManager, MessageRouter, RTCService, VideoStreamHub
│   ├── front/               # Web frontend WS handler (ai_chat, commands, WebRTC signaling)
│   ├── pi/                  # Pi WS handler (status, camera frames, session sync)
│   ├── internal/            # Internal HTTP endpoints (voice reminders)
│   └── models/              # Pydantic message models
│
├── audio/                   # AudioManager, PiperTTS, WhisperSTT
├── brain/                   # Router, OllamaClient, tools, cloud_client, web_ai_client
├── senses/                  # WakeWordDetector, camera_streamer
├── interaction/             # Pi WebSocket client + robot controllers
│   ├── pi_client.py         # Backend WS client (register, command, status)
│   ├── webrtc_call.py       # aiortc WebRTC peer connection
│   └── robot/               # SerialController (STM32 UART) + software simulator
│
├── assets/fillers/          # Pre-generated filler WAVs
├── models/wake_word/        # Custom wake word models (optional)
├── piper/voices/            # Piper TTS ONNX voice models
├── whisper.cpp/             # whisper.cpp build + GGML models
└── tests/                   # Unit tests
```

## Prerequisites

### System packages (Raspberry Pi OS)

```bash
sudo apt install -y python3 python3-venv python3-dev \
  build-essential cmake git curl wget \
  python3-picamera2 portaudio19-dev libasound2-dev alsa-utils
```

### whisper.cpp (compiled native binary, required for STT)

The voice pipeline uses whisper.cpp CLI binary — no Python binding needed.

```bash
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
cmake -B build
cmake --build build --config Release -j$(nproc)
sudo cp build/bin/whisper-cli /usr/local/bin/whisper-cpp
bash models/download-ggml-model.sh tiny.en
cd ..
```

### Piper TTS voice model (ONNX, required for TTS)

```bash
mkdir -p piper/voices
wget -O piper/voices/en_GB-semaine-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx
wget -O piper/voices/en_GB-semaine-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx.json
```

### Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

Unified launcher (starts backend + voice + remote):

```bash
python main.py --mode all
```

Single-subsystem modes:

```bash
python main.py --mode voice     # Voice assistant only
python main.py --mode remote    # Backend + remote WS client only
```

For a backend on another machine:

```bash
python main.py --mode all --ws-url ws://<BACKEND_PC_IP>:8080/ws
```

Or set `FAMILY_ROBOT_WS_URL` in `.env` and simply run `python main.py`.

After startup, access the web control panel at `http://<pi-ip>:5173` (dev) or serve the built frontend.

## Environment Variables

Copy `.env.example` to `.env` and configure as needed.

### API keys (optional — cloud features disabled without them)

| Variable | Feature |
|---|---|
| `MOONSHOT_API_KEY` | Cloud AI (Kimi K2.5 for web chat + Kimi moonshot-v1-8k for voice) |
| `OPENWEATHER_API_KEY` | Live weather lookups |
| `NEWSAPI_KEY` | Top news headlines |

### Backend connection

| Variable | Default | Description |
|---|---|---|
| `FAMILY_ROBOT_WS_URL` | — | Full override URL (highest priority) |
| `FAMILY_ROBOT_BACKEND_HOST` | `127.0.0.1` | Backend host |
| `FAMILY_ROBOT_BACKEND_PORT` | `8080` | Backend port |
| `FAMILY_ROBOT_BACKEND_PATH` | `/ws` | WebSocket path |

### STM32 UART

| Variable | Default | Description |
|---|---|---|
| `FAMILY_ROBOT_SERIAL_PORT` | auto-detect | Serial port for USB-UART cable |
| `FAMILY_ROBOT_FORWARD_SPEED` | `50.0` | Forward motor speed (encoder pulses/10ms) |
| `FAMILY_ROBOT_TURN_SPEED` | `30.0` | Turn motor speed |

### WebRTC audio

| Variable | Default |
|---|---|
| `FAMILY_ROBOT_WEBRTC_MIC_DEVICE_NAME` | `USB PnP Sound Device` |
| `FAMILY_ROBOT_WEBRTC_SPK_DEVICE_NAME` | `bcm2835 Headphones` |
| `FAMILY_ROBOT_WEBRTC_MIC_SAMPLE_RATE` | `48000` |
| `FAMILY_ROBOT_WEBRTC_SPK_SAMPLE_RATE` | `48000` |

Pi auto-resolves ALSA devices from `arecord -l` / `aplay -l` using `*_DEVICE_NAME` first, falling back to `plughw:*` and `default`.

### Camera

| Variable | Default |
|---|---|
| `FAMILY_ROBOT_CAMERA_ENABLED` | `true` |
| `FAMILY_ROBOT_CAMERA_WIDTH` | `640` |
| `FAMILY_ROBOT_CAMERA_HEIGHT` | `360` |
| `FAMILY_ROBOT_CAMERA_FPS` | `10` |
| `FAMILY_ROBOT_CAMERA_JPEG_QUALITY` | `70` |

### Other

| Variable | Default | Description |
|---|---|---|
| `JAVA_BACKEND_URL` | `http://localhost:8090` | Java backend for persistent data |
| `FAMILY_ROBOT_STATUS_INTERVAL` | `2.0` | Status push interval (seconds) |
| `FAMILY_ROBOT_RECONNECT_INTERVAL` | `3.0` | Reconnect interval (seconds) |
| `FAMILY_ROBOT_WS_OPEN_TIMEOUT` | `8.0` | WebSocket open timeout (seconds) |
| `FAMILY_ROBOT_FORCE_LOCAL_ON_BACKEND_DISCONNECT` | `true` | Resume local voice on disconnect |
| `FAMILY_ROBOT_SESSION_RELEASE_DELAY` | `1.5` | Delay before session release (seconds) |
| `FAMILY_ROBOT_VERBOSE` | — | Enable verbose logging |

## Architecture Notes

### Two Kimi clients

| Client | File | Model | Used for |
|---|---|---|---|
| `KimiK25Client` | `brain/web_ai_client.py` | `kimi-k2.5` | Web AI Chat — function calling (robot control, reminders) |
| `KimiClient` | `brain/cloud_client.py` | `moonshot-v1-8k` | Voice pipeline cloud fallback — free-form dialogue |

Both use `MOONSHOT_API_KEY`. The web client supports structured tool calls; the voice client is conversation-only.

### Session control

In `--mode all`, the backend sends `session_control` messages to the Pi:
- `remote_active=true`: pauses wake word detection + local TTS (web user is controlling)
- `remote_active=false`: resumes local voice assistant

On unexpected backend disconnect, local voice resumes automatically (safety fallback).

### Robot controllers

- `SerialRobotController` (`serial_controller.py`): STM32 UART bridge at 115200 baud, auto-detects port
- `RobotController` (`controller.py`): Software simulator fallback when no serial hardware

The serial controller uses `pyserial` (soft dependency — degrades gracefully if missing).
