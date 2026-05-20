# Family Robot

Family service robot graduation project with four subsystems:

- **Family_Robot_pi** — Raspberry Pi unified runtime (FastAPI backend + Jarvis voice assistant + remote control client)
- **Family_Robot_Web_PC** — Vue 3 browser control panel
- **Family_Robot_Back_PC** — Java Spring Boot data backend (auth, reminders, albums)
- **Family_Robot_STM32** — STM32F407 embedded firmware (FreeRTOS + motor/servo control)

## Architecture

```
Browser (Vue 3) ──WebSocket──▶ Python Backend (Pi:8080) ──WebSocket──▶ STM32 (UART)
                   │
                   └──HTTP──▶ Java Backend (PC:8090) ──MySQL
```

- **Real-time layer**: Python FastAPI on Pi relays commands/status/video between Web ↔ Pi ↔ STM32
- **Data layer**: Java Spring Boot on PC handles auth, reminders, albums, and persistent storage

## Quick Start

1. Start Java backend:
   ```bash
   cd Family_Robot_Back_PC
   mvn spring-boot:run
   ```

2. Start web frontend:
   ```bash
   cd Family_Robot_Web_PC
   npm run dev
   ```

3. On Raspberry Pi, start the unified runtime:
   ```bash
   cd Family_Robot_pi
   source venv/bin/activate
   python main.py --mode all
   ```

4. Open `http://<pi-ip>:5173` in browser (dev mode) or serve the built static files

## Subsystems

| Subsystem | Language | Port | Description |
|-----------|----------|------|-------------|
| Family_Robot_pi | Python 3 | 8080 | Real-time WebSocket relay + MJPEG video + voice assistant |
| Family_Robot_Web_PC | Vue 3 + TS | 5173 | Direction control, AI Chat, reminders, albums, WebRTC calls |
| Family_Robot_Back_PC | Java 21 | 8090 | JWT auth, user management, reminder scheduling, command logging |
| Family_Robot_STM32 | C | — | FreeRTOS, DC motor PWM, servo control, encoder speed measurement |

See each subsystem's README for detailed configuration.
