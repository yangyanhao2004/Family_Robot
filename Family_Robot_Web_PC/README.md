# Family_Robot_Web_PC

Web control panel for robot driving, status, voice call, and live camera preview.

## Run

```bash
npm install
npm run dev
```

## Backend URL

Create `.env` (or `.env.local`) if backend is not on localhost:

```bash
VITE_BACKEND_HTTP_URL=http://<backend-ip>:8080
```

The MJPEG live stream is loaded from `${VITE_BACKEND_HTTP_URL}/video/stream`.
