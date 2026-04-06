# Family_Robot_pi

This module now merges both Pi-side capabilities into one clean subproject:

- Local voice assistant runtime (`pibot_local_agent-main` logic)
- Remote WebSocket control/status client (`Family_Robot_pi` original logic)

## Structure

- `main.py`: unified launcher for voice + remote modes
- `orchestrator.py`: local wake-word/STT/router/TTS voice pipeline
- `interaction/`: backend-frontend data interaction layer
- `interaction/pi_client.py`: backend WebSocket client (`register`, `command`, `status`)
- `interaction/robot/controller.py`: centralized command execution + status payload provider
- `audio/`, `brain/`, `senses/`, `assets/`, `config/`, `models/`, `tests/`: local-agent runtime modules

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Camera dependencies on Raspberry Pi OS (Bookworm or newer):

```bash
sudo apt install -y python3-picamera2
pip install Pillow
```

Unified launcher:

```bash
python main.py --mode all
```

For a backend running on another machine, pass URL once:

```bash
python main.py --mode all --ws-url ws://<BACKEND_PC_IP>:8080/ws
```

Or set backend URL once in `.env` and then simply run:

```bash
python main.py
```

Single-subsystem modes:

```bash
python main.py --mode voice
python main.py --mode remote
```

Direct voice entrypoint is still supported:

```bash
python orchestrator.py
```

## Remote Client Environment Variables

- `FAMILY_ROBOT_WS_URL` (full override, highest priority)
- `FAMILY_ROBOT_BACKEND_HOST` (default: `127.0.0.1`)
- `FAMILY_ROBOT_BACKEND_PORT` (default: `8080`)
- `FAMILY_ROBOT_BACKEND_PATH` (default: `/ws`)
- `FAMILY_ROBOT_STATUS_INTERVAL` (default: `2.0`)
- `FAMILY_ROBOT_RECONNECT_INTERVAL` (default: `3.0`)
- `FAMILY_ROBOT_WS_OPEN_TIMEOUT` (default: `8.0`)
- `FAMILY_ROBOT_FORCE_LOCAL_ON_BACKEND_DISCONNECT` (default: `true`)
- `FAMILY_ROBOT_CAMERA_ENABLED` (default: `true`)
- `FAMILY_ROBOT_CAMERA_WIDTH` (default: `640`)
- `FAMILY_ROBOT_CAMERA_HEIGHT` (default: `360`)
- `FAMILY_ROBOT_CAMERA_FPS` (default: `10`)
- `FAMILY_ROBOT_CAMERA_JPEG_QUALITY` (default: `70`)

`main.py` now bootstraps `.env` for all modes (`all` / `voice` / `remote`), so
`FAMILY_ROBOT_WS_URL` in `.env` works without exporting variables manually.

## Notes

- `interaction/pi_client.py` keeps the same message protocol expected by `Family_Robot_Back_PC`.
- `interaction/robot/controller.py` currently simulates status and command effects; replace command branches with real hardware adapters when STM32/serial control is ready.
- In `--mode all`, Pi now listens for backend `session_control` messages:
  - `remote_active=true`: pause local emotional chat (wake word + local TTS replies)
  - `remote_active=false`: resume local emotional chat
- Safety fallback: if backend disconnects unexpectedly while remote session is active,
  Pi forces local emotional chat to resume by default.
