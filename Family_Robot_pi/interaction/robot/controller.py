"""
Robot command execution and status simulation layer.

The current implementation keeps a software state model so the Pi-side
WebSocket client can behave consistently even before hardware adapters are
wired to STM32/serial GPIO drivers.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Iterable


SUPPORTED_COMMANDS = (
    "forward",
    "backward",
    "left",
    "right",
    "stop",
    "servo1",
    "servo2",
    "speed_low",
    "speed_medium",
    "speed_high",
)

_MOTION_COMMANDS = {"forward", "backward", "left", "right"}
_STOP_COMMAND = "stop"


@dataclass
class _RobotState:
    battery: int = 95
    is_running: bool = False
    temperature: float = 34.0
    signal_strength: int = 4
    last_command: str = _STOP_COMMAND
    last_update_monotonic: float = field(default_factory=time.monotonic)


class RobotController:
    """
    Command executor plus status provider.

    Replace the command branch bodies in `execute_command` when real hardware
    interfaces are ready.
    """

    def __init__(self, supported_commands: Iterable[str] = SUPPORTED_COMMANDS):
        self._supported_commands = set(supported_commands)
        self._state = _RobotState()
        self._lock = Lock()

    def execute_command(self, command: str, angle: float = 0.0) -> bool:
        """
        Execute one remote command.

        Returns True when the command is accepted, False if unknown.
        """
        if command not in self._supported_commands:
            return False

        with self._lock:
            self._advance_state_locked()
            self._state.last_command = command

            if command in _MOTION_COMMANDS:
                self._state.is_running = True
            elif command == _STOP_COMMAND:
                self._state.is_running = False

        return True

    def status_payload(self) -> Dict[str, float]:
        """
        Return the backend-compatible status payload.
        """
        with self._lock:
            self._advance_state_locked()
            return {
                "battery": self._state.battery,
                "isRunning": self._state.is_running,
                "temperature": round(self._state.temperature, 1),
                "signalStrength": self._state.signal_strength,
            }

    def _advance_state_locked(self):
        """
        Evolve status over time to avoid static values in the dashboard.
        """
        now = time.monotonic()
        elapsed = max(0.0, now - self._state.last_update_monotonic)
        self._state.last_update_monotonic = now

        if self._state.is_running:
            drain = int(elapsed * 0.20)
            self._state.battery = max(5, self._state.battery - drain)
        else:
            if random.random() < min(0.2, elapsed / 12.0):
                self._state.battery = min(100, self._state.battery + 1)

        target_temp = 39.0 if self._state.is_running else 33.0
        delta = (target_temp - self._state.temperature) * min(0.35, max(0.05, elapsed))
        jitter = random.uniform(-0.2, 0.2)
        self._state.temperature = max(28.0, min(62.0, self._state.temperature + delta + jitter))

        if random.random() < min(0.45, elapsed / 4.0):
            self._state.signal_strength = max(
                1,
                min(5, self._state.signal_strength + random.choice([-1, 0, 1])),
            )
