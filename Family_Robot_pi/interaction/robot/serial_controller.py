"""
SerialRobotController — bridges Pi WebSocket commands to STM32 UART.

Physical link: Pi USB → USB-UART cable → STM32 UART1 (PA9=TX, PA10=RX, 115200 8N1)

Web commands are mapped to STM32 PID closed-loop velocity targets (V1/V2):
  forward  → V1=+speed, V2=+speed
  backward → V1=-speed, V2=-speed
  left     → V1=-turn,  V2=+turn   (differential steering)
  right    → V1=+turn,  V2=-turn
  stop     → V1=0,      V2=0

STM32 telemetry (from defaultTask, every 500 ms):
  E1=<pulses/10ms> T1=<target> | E2=<pulses/10ms> T2=<target>
"""

from __future__ import annotations

import logging
import os
import re
import sys
import threading
import time
from typing import Dict

logger = logging.getLogger("interaction.serial_controller")

# ---------------------------------------------------------------------------
# STM32 telemetry line parser
# ---------------------------------------------------------------------------
_TELEMETRY_RE = re.compile(
    r"E1=(-?\d+)\s+T1=(-?[\d.]+)\s*\|\s*E2=(-?\d+)\s+T2=(-?[\d.]+)"
)


def _auto_detect_port() -> str | None:
    """Return the first plausible USB-UART device, or None."""
    candidates = []
    if sys.platform == "linux":
        candidates = [
            "/dev/ttyUSB0", "/dev/ttyUSB1",
            "/dev/ttyACM0", "/dev/ttyACM1",
            "/dev/serial0",
        ]
    elif sys.platform == "darwin":
        import glob as _glob
        candidates = _glob.glob("/dev/tty.usbserial*") + _glob.glob("/dev/tty.usbmodem*")
    elif sys.platform == "win32":
        candidates = [f"COM{i}" for i in range(1, 17)]

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ---------------------------------------------------------------------------
# SerialRobotController
# ---------------------------------------------------------------------------

class SerialRobotController:
    """Command executor that sends movement commands to STM32 over UART.

    A background reader thread continuously parses STM32 telemetry lines so
    that ``status_payload()`` always returns the latest encoder/Target values
    without blocking the asyncio event loop.
    """

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = 115200,
        forward_speed: float = 50.0,
        turn_speed: float = 30.0,
        timeout: float = 0.1,
    ):
        self._port = port or os.getenv("FAMILY_ROBOT_SERIAL_PORT") or _auto_detect_port()
        self._baudrate = baudrate
        self._forward_speed = forward_speed
        self._turn_speed = turn_speed
        self._timeout = timeout

        self._serial: "serial.Serial | None" = None  # type: ignore[name-defined]
        self._lock = threading.Lock()
        self._running = False
        self._reader_thread: threading.Thread | None = None

        # --- cached telemetry (updated by the reader thread) ---
        self._encoder1: int = 0
        self._encoder2: int = 0
        self._target1: float = 0.0
        self._target2: float = 0.0
        self._last_telemetry_at: float = 0.0

        # --- command tracking ---
        self._last_command: str = "stop"
        self._is_moving: bool = False

        # --- simulated battery / temperature (STM32 does not report these) ---
        self._battery: int = 95
        self._temperature: float = 34.0
        self._signal_strength: int = 4
        self._last_status_update: float = time.monotonic()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self) -> bool:
        """Open the serial port and start the telemetry reader thread.

        Returns True on success, False when no port is available.
        """
        if self._port is None:
            logger.warning("Serial port not configured and auto-detection failed; "
                           "running in software-only mode")
            return False

        try:
            import serial
        except ImportError:
            logger.warning("pyserial not installed; running in software-only mode. "
                           "Install it with: pip install pyserial")
            return False

        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self._timeout,
            )
        except Exception as exc:
            logger.warning("Cannot open serial port %s: %s", self._port, exc)
            self._serial = None
            return False

        self._running = True
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()
        logger.info("SerialRobotController connected on %s @ %d baud", self._port, self._baudrate)
        return True

    def close(self):
        """Stop the reader thread and close the serial port."""
        self._running = False
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=1.0)
            self._reader_thread = None
        if self._serial is not None and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None
        logger.info("SerialRobotController closed")

    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    # ------------------------------------------------------------------
    # Command execution  (called from asyncio event loop — keep it fast)
    # ------------------------------------------------------------------

    def execute_command(self, command: str) -> bool:
        """Map a high-level command to STM32 UART protocol and send it."""
        if command == "stop":
            self._send_uart("V1=0\r\nV2=0\r\n")
            self._is_moving = False
        elif command == "forward":
            s = self._forward_speed
            self._send_uart(f"V1={s:.1f}\r\nV2={s:.1f}\r\n")
            self._is_moving = True
        elif command == "backward":
            s = -self._forward_speed
            self._send_uart(f"V1={s:.1f}\r\nV2={s:.1f}\r\n")
            self._is_moving = True
        elif command == "left":
            s1, s2 = -self._turn_speed, self._turn_speed
            self._send_uart(f"V1={s1:.1f}\r\nV2={s2:.1f}\r\n")
            self._is_moving = True
        elif command == "right":
            s1, s2 = self._turn_speed, -self._turn_speed
            self._send_uart(f"V1={s1:.1f}\r\nV2={s2:.1f}\r\n")
            self._is_moving = True
        else:
            return False

        self._last_command = command
        return True

    def _send_uart(self, data: str):
        """Thread-safe serial write."""
        ser = self._serial
        if ser is None or not ser.is_open:
            logger.debug("Serial not connected; dropping command")
            return
        try:
            with self._lock:
                ser.write(data.encode("utf-8"))
        except Exception as exc:
            logger.error("Serial write failed: %s", exc)

    # ------------------------------------------------------------------
    # Telemetry reader  (background thread)
    # ------------------------------------------------------------------

    def _read_loop(self):
        """Continuously read lines from the STM32 and parse telemetry."""
        buf = b""
        while self._running:
            ser = self._serial
            if ser is None or not ser.is_open:
                time.sleep(0.5)
                continue
            try:
                chunk = ser.read(128)
            except Exception:
                time.sleep(0.5)
                continue

            if not chunk:
                continue

            buf += chunk
            # Extract complete lines (terminated by \r or \n)
            while True:
                idx = buf.find(b"\r")
                if idx == -1:
                    idx = buf.find(b"\n")
                if idx == -1:
                    break

                line = buf[:idx].decode("utf-8", errors="replace").strip()
                buf = buf[idx + 1:]
                if line:
                    self._parse_line(line)

    def _parse_line(self, line: str):
        """Try to parse a STM32 telemetry line.

        Expected format (from defaultTask every 500 ms):
          E1=<encoder1_speed> T1=<pid1.target> | E2=<encoder2_speed> T2=<pid2.target>
        """
        m = _TELEMETRY_RE.search(line)
        if m:
            self._encoder1 = int(m.group(1))
            self._target1 = float(m.group(2))
            self._encoder2 = int(m.group(3))
            self._target2 = float(m.group(4))
            self._last_telemetry_at = time.monotonic()
            logger.debug("Telemetry: E1=%d T1=%.1f E2=%d T2=%.1f",
                         self._encoder1, self._target1,
                         self._encoder2, self._target2)
            return

        # Other STM32 output (command echoes, etc.) — just log at debug level
        logger.debug("STM32: %s", line[:120])

    # ------------------------------------------------------------------
    # Status  (called from asyncio event loop — keep it fast)
    # ------------------------------------------------------------------

    def status_payload(self) -> Dict[str, float]:
        """Return the backend-compatible status payload.

        Includes real encoder speeds from STM32 telemetry when available,
        plus simulated battery / temperature / signal strength.
        """
        self._evolve_status()

        return {
            "battery": self._battery,
            "isRunning": self._is_moving,
            "temperature": round(self._temperature, 1),
            "signalStrength": self._signal_strength,
            # Extended fields — the frontend can use these for diagnostics
            "encoder1": self._encoder1,
            "encoder2": self._encoder2,
            "target1": self._target1,
            "target2": self._target2,
            "serialConnected": self.is_connected(),
        }

    def _evolve_status(self):
        """Simulate battery drain and temperature changes over time."""
        import random
        now = time.monotonic()
        elapsed = max(0.0, now - self._last_status_update)
        self._last_status_update = now

        if self._is_moving:
            self._battery = max(5, self._battery - int(elapsed * 0.20))
        else:
            if random.random() < min(0.2, elapsed / 12.0):
                self._battery = min(100, self._battery + 1)

        target_temp = 39.0 if self._is_moving else 33.0
        delta = (target_temp - self._temperature) * min(0.35, max(0.05, elapsed))
        jitter = random.uniform(-0.2, 0.2)
        self._temperature = max(28.0, min(62.0, self._temperature + delta + jitter))

        if random.random() < min(0.45, elapsed / 4.0):
            self._signal_strength = max(1, min(5, self._signal_strength + random.choice([-1, 0, 1])))
