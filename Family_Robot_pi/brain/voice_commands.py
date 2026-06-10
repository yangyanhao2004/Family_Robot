"""
Thread-safe bridge: voice agent → robot commands.
Orchestrator (thread) enqueues; pi_client (async main loop) drains.
"""
import queue

_voice_cmd_queue: queue.Queue = queue.Queue()


def enqueue_voice_command(command: str, angle: float = 90.0, duration: float | None = None):
    """Called from orchestrator thread to request a robot command."""
    _voice_cmd_queue.put({
        "command": command,
        "angle": angle,
        "duration": duration
    })
    print(f"[VoiceCmd] Enqueued: {command}")


def drain_voice_commands() -> list[dict]:
    """Called from pi_client's async loop. Returns list of pending commands."""
    commands = []
    while True:
        try:
            cmd = _voice_cmd_queue.get_nowait()
            commands.append(cmd)
        except queue.Empty:
            break
    return commands
