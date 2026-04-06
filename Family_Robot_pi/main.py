#!/usr/bin/env python3
"""
Unified launcher for Family_Robot_pi.

Modes:
- all: run voice agent + WebSocket remote client
- voice: run voice agent only
- remote: run WebSocket remote client only
"""

import argparse
import asyncio
import logging
from threading import Lock, Thread
from typing import Optional

logger = logging.getLogger("family_robot_pi.main")


def _bootstrap_runtime_env(config_path: Optional[str]):
    """
    Load .env/config variables once before launching any mode.

    This guarantees remote-only mode can also read FAMILY_ROBOT_* variables
    from `.env`, so users can run `python main.py` without extra CLI flags.
    """
    try:
        from config import Config

        # Side effect: Config.load() reads .env into process environment.
        Config.load(config_path)
    except Exception as exc:
        logger.warning("Env bootstrap skipped: %s", exc)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Family Robot Pi launcher")
    parser.add_argument(
        "--mode",
        choices=("all", "voice", "remote"),
        default="all",
        help="Run both voice and remote control, or only one subsystem",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional path to Pi voice-agent config JSON",
    )
    parser.add_argument(
        "--ws-url",
        default=None,
        help="Optional backend WebSocket URL override for remote mode",
    )
    parser.add_argument(
        "--status-interval",
        type=float,
        default=2.0,
        help="Seconds between status pushes in remote mode",
    )
    parser.add_argument(
        "--reconnect-interval",
        type=float,
        default=3.0,
        help="Seconds to wait before remote reconnection attempts",
    )
    return parser


def _create_orchestrator(config_path: Optional[str]):
    from config import Config
    from orchestrator import Orchestrator

    config = Config.load(config_path)
    return Orchestrator(config)


def _run_voice_only(config_path: Optional[str]):
    orchestrator = _create_orchestrator(config_path)
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

    shared = {
        "orchestrator": None,
        "pending_remote_active": None,
    }
    shared_lock = Lock()

    def on_remote_session_change(remote_active: bool):
        with shared_lock:
            orchestrator = shared.get("orchestrator")
            if orchestrator is None:
                shared["pending_remote_active"] = remote_active
                logger.info(
                    "Queued remote session state before voice startup: active=%s",
                    remote_active,
                )
                return

        orchestrator.set_remote_session_active(remote_active)

    def voice_runner():
        try:
            orchestrator = _create_orchestrator(args.config)
            with shared_lock:
                shared["orchestrator"] = orchestrator
                pending_remote_active = shared.get("pending_remote_active")
            if pending_remote_active is not None:
                orchestrator.set_remote_session_active(bool(pending_remote_active))
            orchestrator.start(install_signal_handlers=False, force_exit=False)
        except Exception as exc:
            logger.exception("Voice agent terminated with error: %s", exc)

    voice_thread = Thread(target=voice_runner, name="voice-agent", daemon=True)
    voice_thread.start()

    remote = PiWebSocketClient(
        ws_url=args.ws_url,
        reconnect_interval=args.reconnect_interval,
        status_interval=args.status_interval,
        session_control_handler=on_remote_session_change,
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

    if args.mode == "voice":
        _run_voice_only(args.config)
        return

    if args.mode == "remote":
        _run_remote_only(args)
        return

    _run_all(args)


if __name__ == "__main__":
    main()
