# Family Robot - Graduation Project

## Project Overview
Four-subsystem family service robot: remote control + AI voice assistant + embedded motion control.

## Subsystems

### 1. Family_Robot_pi — Unified Pi Runtime (Backend + Voice + Remote)
The backend has been merged into the Pi project under `backend/`.

**Unified launcher**: `python main.py --mode all|voice|remote`
- Starts FastAPI backend in daemon thread (port 8080)
- Then launches Pi logic: voice agent (daemon thread) + remote WebSocket client (asyncio main thread)
- Pi remote client connects to `127.0.0.1:8080` by default (backend on same machine)

**Backend (`backend/`)** — merged from Family_Robot_Back_PC:
- `backend/app.py` — FastAPI app with 3 endpoints: `/ws`, `/ws/rtc`, `/video/stream`, `GET /`
- `backend/core/` — ConnectionManager (single web + single Pi connection), MessageRouter, RTCService (room-based signaling), VideoStreamHub (in-memory latest-frame MJPEG)
- `backend/front/` — Web frontend WS handler, validates commands/WebRTC, manages session_control (pause Pi voice when web connected)
- `backend/pi/` — Pi WS handler, decodes camera frames → VideoStreamHub, syncs session state on reconnect
- `backend/models/` — Pydantic models: command (7 commands), status, webrtc

**Voice Agent**:
- WakeWordDetector (openWakeWord) → AudioManager.record_until_silence → WhisperSTT (whisper.cpp CLI) → Router (multi-layer) → tools/Ollama/Kimi → PiperTTS → aplay
- Router layers: (1) exact regex direct responses, (2) keyword tool detection, (3) local Ollama LLM with tool calling (disabled by default for Pi 4B), (4) Kimi K2 cloud fallback
- 6 tools: time, weather (OpenWeatherMap), news (NewsAPI), system_status (/proc+/sys), joke (API), cloud_handoff (Kimi)

**Remote Client**:
- `interaction/pi_client.py` (PiWebSocketClient) — sends status/camera, receives commands/webrtc
- `interaction/webrtc_call.py` (aiortc) — auto-detects ALSA devices by name
- `interaction/robot/controller.py` — software simulator (replace with real STM32 UART driver for hardware)
- `senses/camera_streamer.py` — Picamera2 → Pillow JPEG → base64

### 2. Family_Robot_Web_PC (Vue 3 + TypeScript + Vite + Pinia)
- Browser control panel: video preview, directional pad (press-and-hold continuous send), light toggle, WebRTC voice call
- Key services: `src/services/websocket.ts` (auto-reconnect, 30s heartbeat), `src/services/webrtc.ts` (STUN via Google, audio-only)
- Store: `src/store/robotStore.ts` (connection, status, settings)
- Backend URL set via `VITE_BACKEND_HTTP_URL` in `.env.local` — point to Pi's IP:8080
- Run: `npm run dev` (Vite dev server)

### 3. Family_Robot_Back_PC (Legacy, now merged into Family_Robot_pi/backend/)
- Original standalone backend. Kept for reference. All functionality now lives in `Family_Robot_pi/backend/`.

### 4. Family_Robot_STM32 (C + FreeRTOS on STM32F407)
- `Family_Bot_STM32/FreeRTOS/Src/main.c` — all custom logic is in USER CODE blocks
- SysClk 168MHz (HSE + PLL), APB1=42MHz, APB2=84MHz
- TIM1: 4-ch PWM for 2 DC motors (100Hz, H-bridge), PE9/PE11/PE13/PE14
- TIM13: software PWM for 2 servos (10μs ISR, 20ms period, 50Hz), PA11/PA12
- TIM2/TIM5: encoder mode (TI12, Period=60000)
- TIM7: 10ms speed measurement ISR
- USART1: 115200 baud, command protocol `S1=90` / `M1=500` / `M2=-300`
- Tasks: defaultTask (prints encoder speeds every 2s), LED_Task (blink PE10)

## Data Flow
- Web → Backend → Pi: command + webrtc_signaling messages
- Pi → Backend → Web: status + camera_frame + webrtc_signaling messages
- Pi camera → base64 JPEG → Backend VideoStreamHub → HTTP MJPEG → Browser
- WebRTC audio: Browser ↔ (signaling via Backend) ↔ Pi (aiortc)

## Startup (Unified, on Pi)
```bash
cd Family_Robot_pi
source venv313/bin/activate
python main.py --mode all    # backend + voice + remote
```
Then access web panel at `http://<pi-ip>:5173` (dev) or build and serve `Family_Robot_Web_PC/dist/`.

## Key Conventions
- Pi RobotController is a simulator; STM32 integration planned via UART
- Ollama configured for qwen2.5:1.5b, local LLM routing disabled on Pi 4B due to performance
- Session control suspends voice agent when remote web client is active
- Audio devices auto-detected by name substring matching (USB mic, bcm2835 headphones)
- All path resolution uses multi-candidate fallback chains for robustness
- Backend imports use `backend.xxx` absolute paths (Pi project root = sys.path[0])
