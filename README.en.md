# Family Robot

Family service robot graduation project with four subsystems: Raspberry Pi real-time backend + Vue 3 control panel + Java data backend + STM32 embedded firmware.

---

## System Architecture

```
Browser (Vue 3) ──WebSocket──▶ Python Backend (Pi :8080) ──WebSocket──▶ STM32 (UART)
    │                              │
    └──HTTP REST──▶ Java Backend (PC :8090) ──MySQL
```

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Real-time** | Python FastAPI + WebSocket | Relays commands/status/video between Web ↔ Pi ↔ STM32 |
| **Data** | Java Spring Boot + JPA | Auth, reminder scheduling, album storage, command logging |

---

## Subsystem Overview

| Subsystem | Language | Port | Directory |
|-----------|----------|------|-----------|
| Family_Robot_pi | Python 3 | 8080 | Real-time WS relay + MJPEG video + Jarvis voice assistant |
| Family_Robot_Web_PC | Vue 3 + TS | 5173 | Direction control, AI Chat, reminders, albums, WebRTC calls |
| Family_Robot_Back_PC | Java 21 | 8090 | JWT auth, user management, reminder CRUD + scheduling, command stats |
| Family_Robot_STM32 | C | — | FreeRTOS, DC motor PWM, servo control, encoder speed measurement |

---

## Prerequisites

| Component | Requirement |
|-----------|-------------|
| Java | JDK 21+ |
| Maven | 3.6+ |
| Node.js | 18+ |
| Python | 3.10+ |
| MySQL | 8.0+ |
| Raspberry Pi | Pi 4B / 5 (for voice + camera + STM32 serial) |

---

## Step-by-Step Startup

### Step 1: Database

1. Install MySQL 8.0+ and start the service
2. Create the database:
   ```sql
   CREATE DATABASE IF NOT EXISTS family_robot DEFAULT CHARACTER SET utf8mb4;
   ```
3. Default credentials: `root / 123456`, database `family_robot` (tables are auto-created by JPA)

### Step 2: Java Backend (PC, Port 8090)

```bash
cd Family_Robot_Back_PC
mvn spring-boot:run
```

**Configurable environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_URL` | `jdbc:mysql://localhost:3306/family_robot?...` | Database connection URL |
| `DB_USERNAME` | `root` | Database username |
| `DB_PASSWORD` | `123456` | Database password |
| `SERVER_PORT` | `8090` | Server port |
| `JWT_SECRET` | Built-in default | JWT signing key (change in production) |
| `AES_SECRET` | Built-in default | Password encryption key (change in production) |
| `PYTHON_BACKEND_URL` | `http://192.168.137.90:8080` | Python backend address (for VOICE reminders) |

**On first startup**, an admin account is auto-created via `data.sql`:
- Email: `admin@familybot.com`
- Password: `admin123`

### Step 3: Web Frontend (PC, Port 5173)

```bash
cd Family_Robot_Web_PC
npm install
npm run dev
```

**Configuration file** `Family_Robot_Web_PC/.env.local`:

```env
# Python FastAPI backend (Raspberry Pi IP + port 8080)
VITE_BACKEND_HTTP_URL=http://192.168.137.90:8080

# Java Spring Boot backend (local machine + port 8090)
VITE_JAVA_API_URL=http://localhost:8090
```

> **Note**: `VITE_BACKEND_HTTP_URL` must point to the Raspberry Pi's actual IP address. `localhost` only works if the Python backend runs on the same machine as the frontend.

### Step 4: Python Runtime (Raspberry Pi)

See `Family_Robot_pi/README.md` for detailed setup.

**One-time setup:**
```bash
cd Family_Robot_pi
chmod +x setup.sh && ./setup.sh
```

**Daily startup:**
```bash
cd Family_Robot_pi
source venv/bin/activate
python main.py --mode all
```

**Startup modes:**

| Command | Description |
|---------|-------------|
| `python main.py --mode all` | Full mode (backend + voice + remote control) |
| `python main.py --mode voice` | Voice assistant only (local voice interaction) |
| `python main.py --mode remote` | Remote control only (backend + WS client) |

> **Note**: If the Python backend is NOT on the Raspberry Pi, set `FAMILY_ROBOT_WS_URL` in `.env` to the actual address.

---

## Startup Order

```
1. MySQL service
2. Java backend (PC, port 8090)
3. Web frontend (PC, port 5173)
4. Python runtime (Pi, port 8080)  ← Start last, depends on other services
```

---

## Ports & Network Configuration

### Port Assignment

| Port | Machine | Service | Protocol |
|------|---------|---------|----------|
| **8080** | Raspberry Pi | Python FastAPI backend | HTTP + WebSocket |
| **8090** | PC | Java Spring Boot backend | HTTP REST |
| **5173** | PC | Vue 3 dev server | HTTP |
| **3306** | PC / Server | MySQL database | TCP |
| **11434** | Raspberry Pi | Ollama local LLM (optional) | HTTP |

### Deployment Scenarios & IP Configuration

The default setup assumes the **PC and Raspberry Pi are on the same LAN** (Wi-Fi hotspot or router).

**Typical topology:**

```
PC (192.168.137.1) ←──Wi-Fi──→ Raspberry Pi (192.168.137.90)
    │                                │
    ├─ Java backend :8090            ├─ Python backend :8080
    ├─ Vue frontend :5173            ├─ Jarvis voice assistant
    └─ MySQL :3306                   └─ STM32 (USB-UART)
```

**4 places where IP addresses need to be configured:**

| Location | Config Key | Value |
|----------|-----------|-------|
| `Family_Robot_Web_PC/.env.local` | `VITE_BACKEND_HTTP_URL` | **Pi IP** — browser connects to Python backend |
| `Family_Robot_Web_PC/.env.local` | `VITE_JAVA_API_URL` | **PC IP** — browser connects to Java backend |
| `Family_Robot_Back_PC/application.yml` | `PYTHON_BACKEND_URL` | **Pi IP** — Java calls Python for VOICE reminders |
| `Family_Robot_pi/.env` | `JAVA_BACKEND_URL` | **PC IP** — Pi calls Java to store reminders |

### Scenario A: All on one PC (no Raspberry Pi)

If the Python backend also runs on the PC (no camera/voice hardware):

```
VITE_BACKEND_HTTP_URL=http://localhost:8080
VITE_JAVA_API_URL=http://localhost:8090
PYTHON_BACKEND_URL=http://localhost:8080
JAVA_BACKEND_URL=http://localhost:8090
```

Set all IPs to `localhost`.

### Scenario B: PC + Pi Separate (standard setup)

PC (192.168.137.1) runs Java + frontend, Pi (192.168.137.90) runs Python:

```
VITE_BACKEND_HTTP_URL=http://192.168.137.90:8080   # browser → Pi
VITE_JAVA_API_URL=http://192.168.137.1:8090         # browser → local Java
PYTHON_BACKEND_URL=http://192.168.137.90:8080       # Java → Pi
JAVA_BACKEND_URL=http://192.168.137.1:8090          # Pi → PC
```

> **Critical**: `VITE_BACKEND_HTTP_URL` runs in the user's browser, so it MUST use the LAN IP (e.g. `192.168.x.x`). `localhost` in the browser refers to the user's own machine, not the Pi.

### Finding the Pi's IP

On the Pi terminal:
```bash
hostname -I
```
or
```bash
ip addr show wlan0 | grep "inet "
```

### Firewall

- Pi port **8080** must allow inbound connections from the PC
- PC port **8090** must allow inbound connections from the Pi (for VOICE reminder callbacks)
- PC port **5173** is dev-only; production builds generate static files
- Windows Firewall will prompt on first run — click "Allow access"

### Port Conflict Check

Check for port conflicts before starting:

```bash
# On Raspberry Pi
lsof -i :8080

# On Windows PC
netstat -ano | findstr "8090"
netstat -ano | findstr "5173"
```

---

## FAQ

### 1. No video / robot control in the browser

- Verify `VITE_BACKEND_HTTP_URL` points to the Pi's actual IP
- Verify `python main.py --mode all` is running on the Pi
- Check browser Console (F12) for WebSocket connection status

### 2. User registration fails

- Verify the Java backend is running (`http://localhost:8090` reachable)
- Verify the MySQL database exists
- Check the verification email (QQ SMTP)

### 3. Voice assistant doesn't respond on the Pi

- Verify microphone and speaker are connected
- Verify whisper.cpp is compiled (`which whisper-cpp`)
- Verify the Piper TTS voice model is downloaded (`piper/voices/en_GB-semaine-medium.onnx`)
- Wake word is "Hey Jarvis"

### 4. AI Chat not working

- Verify `MOONSHOT_API_KEY` is set in `.env`
- Verify network access to `api.moonshot.cn`

### 5. WebRTC call has no audio

- Verify `aiortc` is installed
- Verify USB microphone and headphones are connected to the Pi
- Check Python logs for audio device auto-detection results
