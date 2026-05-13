#!/usr/bin/env python3
"""
Unified launcher for Family Robot Pi.

Starts the FastAPI backend + voice agent + remote WebSocket client
all from a single command on Raspberry Pi.

Modes:
  --mode all     Backend + voice agent + remote client (default)
  --mode voice   Voice agent only, no backend
  --mode remote  Backend + remote client only, no voice agent
"""

import argparse
import asyncio
import logging
import time
import urllib.request
from threading import Lock, Thread
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("family_robot.main")


def _bootstrap_runtime_env(config_path: Optional[str]):
    """Load .env/config before launching any mode."""
    try:
        from config import Config
        Config.load(config_path)
    except Exception as exc:
        logger.warning("Env bootstrap skipped: %s", exc)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Family Robot Pi unified launcher")
    parser.add_argument(
        "--mode", choices=("all", "voice", "remote"), default="all",
        help="Run mode (default: all)",
    )
    parser.add_argument("--config", default=None, help="Path to voice-agent config JSON")
    parser.add_argument("--ws-url", default=None, help="Backend WebSocket URL (default: ws://127.0.0.1:8080/ws)")
    parser.add_argument("--status-interval", type=float, default=2.0, help="Status push interval (s)")
    parser.add_argument("--reconnect-interval", type=float, default=3.0, help="Reconnect delay (s)")
    parser.add_argument("--backend-port", type=int, default=8080, help="Backend listen port")
    parser.add_argument("--no-backend", action="store_true", help="Don't auto-start backend")
    return parser


def _start_backend(port: int):
    """Start FastAPI backend in the current thread (blocking)."""
    import uvicorn
    from backend.app import app

    # Suppress uvicorn access logs unless FAMILY_ROBOT_VERBOSE is set
    import os
    log_level = "info" if os.getenv("FAMILY_ROBOT_VERBOSE") else "warning"

    uvicorn.run(app, host="0.0.0.0", port=port, log_level=log_level)


def _wait_for_backend(port: int, timeout: float = 15.0):
    """Poll the backend health endpoint until it responds."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1.0)
            if resp.status == 200:
                logger.info("Backend is ready on port %s", port)
                return True
        except Exception:
            pass
        time.sleep(0.3)
    logger.error("Backend did not become ready within %.0f seconds", timeout)
    return False


def _run_voice_only(config_path: Optional[str]):
    from orchestrator import Orchestrator
    from config import Config

    config = Config.load(config_path)
    orchestrator = Orchestrator(config)
    orchestrator.start(install_signal_handlers=True, force_exit=False)


def _run_remote_only(args: argparse.Namespace):
    from interaction.pi_client import PiWebSocketClient

    remote = PiWebSocketClient(
        ws_url=args.ws_url,
        reconnect_interval=args.reconnect_interval,
        status_interval=args.status_interval,
    )
    try:
        asyncio.run(remote.run_forever())
    except KeyboardInterrupt:
        logger.info("Remote mode interrupted")
    finally:
        remote.stop()


def _run_all(args: argparse.Namespace):
    from interaction.pi_client import PiWebSocketClient

    shared = {"orchestrator": None, "pending_remote_active": None}
    shared_lock = Lock()

    def on_remote_session_change(remote_active: bool):
        with shared_lock:
            orchestrator = shared.get("orchestrator")
            if orchestrator is None:
                shared["pending_remote_active"] = remote_active
                return
        orchestrator.set_remote_session_active(remote_active)

    def on_wake_word_control(pause: bool):
        with shared_lock:
            orchestrator = shared.get("orchestrator")
        if orchestrator is None:
            return
        if pause:
            orchestrator.pause_wake_word_detector()
        else:
            orchestrator.resume_wake_word_detector()

    def voice_runner():
        try:
            from orchestrator import Orchestrator
            from config import Config

            config = Config.load(args.config)
            orchestrator = Orchestrator(config)
            with shared_lock:
                shared["orchestrator"] = orchestrator
                pending = shared.get("pending_remote_active")
            if pending is not None:
                orchestrator.set_remote_session_active(bool(pending))
            orchestrator.start(install_signal_handlers=False, force_exit=False)
        except Exception as exc:
            logger.exception("Voice agent error: %s", exc)

    voice_thread = Thread(target=voice_runner, name="voice-agent", daemon=True)
    voice_thread.start()

    remote = PiWebSocketClient(
        ws_url=args.ws_url,
        reconnect_interval=args.reconnect_interval,
        status_interval=args.status_interval,
        session_control_handler=on_remote_session_change,
        wake_word_control_handler=on_wake_word_control,
    )

    try:
        asyncio.run(remote.run_forever())
    except KeyboardInterrupt:
        logger.info("Combined mode interrupted")
    finally:
        remote.stop()
        with shared_lock:
            orchestrator = shared.get("orchestrator")
        if orchestrator is not None:
            orchestrator.stop()
        voice_thread.join(timeout=5.0)


def main():
    args = _build_parser().parse_args()
    _bootstrap_runtime_env(args.config)

    need_backend = args.mode in ("all", "remote") and not args.no_backend

    if need_backend:
        logger.info("Starting backend server on port %s...", args.backend_port)
        backend_thread = Thread(
            target=_start_backend, args=(args.backend_port,),
            name="backend", daemon=True,
        )
        backend_thread.start()

        if not _wait_for_backend(args.backend_port):
            logger.error("Backend failed to start, aborting")
            return

    if args.mode == "voice":
        _run_voice_only(args.config)
        return

    if args.mode == "remote":
        _run_remote_only(args)
        return

    _run_all(args)


if __name__ == "__main__":
    main()
