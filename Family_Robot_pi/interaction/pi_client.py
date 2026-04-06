import asyncio
import json
import logging
import os
from typing import Callable, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from .robot import SUPPORTED_COMMANDS, RobotController
from senses.camera_streamer import CameraStreamer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("interaction.pi_client")


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _build_ws_url() -> str:
    explicit_url = os.getenv("FAMILY_ROBOT_WS_URL")
    if explicit_url:
        return explicit_url

    backend_host = os.getenv("FAMILY_ROBOT_BACKEND_HOST", "127.0.0.1")
    backend_port = _env_int("FAMILY_ROBOT_BACKEND_PORT", 8080)
    backend_path = os.getenv("FAMILY_ROBOT_BACKEND_PATH", "/ws")
    if not backend_path.startswith("/"):
        backend_path = "/" + backend_path
    return f"ws://{backend_host}:{backend_port}{backend_path}"


class PiWebSocketClient:
    """Family Robot Pi-side remote control/status WebSocket client."""

    def __init__(
        self,
        ws_url: Optional[str] = None,
        reconnect_interval: float = 3.0,
        status_interval: float = 2.0,
        controller: Optional[RobotController] = None,
        camera_enabled: bool = True,
        camera_width: int = 640,
        camera_height: int = 360,
        camera_fps: int = 10,
        camera_jpeg_quality: int = 70,
        camera_streamer: Optional[CameraStreamer] = None,
        session_control_handler: Optional[Callable[[bool], None]] = None,
        force_local_on_backend_disconnect: bool = True,
        ws_open_timeout: float = 8.0,
    ):
        self.ws_url = ws_url or _build_ws_url()
        self.reconnect_interval = reconnect_interval
        self.status_interval = status_interval
        self.controller = controller or RobotController()
        self._running = True

        self.camera_enabled = camera_enabled
        self.camera_fps = max(1, int(camera_fps))
        self._camera_send_interval = 1.0 / float(self.camera_fps)
        self.camera_streamer = camera_streamer
        self._camera_started = False
        self._remote_session_active = False
        self._session_control_handler = session_control_handler
        self.force_local_on_backend_disconnect = force_local_on_backend_disconnect
        self.ws_open_timeout = max(2.0, float(ws_open_timeout))

        if self.camera_enabled and self.camera_streamer is None:
            self.camera_streamer = CameraStreamer(
                width=camera_width,
                height=camera_height,
                fps=self.camera_fps,
                jpeg_quality=camera_jpeg_quality,
            )

    def stop(self):
        self._running = False
        if self.camera_streamer is not None:
            self.camera_streamer.stop()

    async def send_register_message(self, websocket):
        register_message = {"type": "register", "role": "robot"}
        await websocket.send(json.dumps(register_message))
        logger.info("Sent register message")

    async def send_status_message(self, websocket):
        status_message = {
            "type": "status",
            "payload": self.controller.status_payload(),
        }
        await websocket.send(json.dumps(status_message))
        logger.debug("Sent status message: %s", status_message)

    async def handle_message(self, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.error("Invalid message format: %s", message)
            return

        message_type = data.get("type")
        if message_type == "command":
            payload = data.get("payload") or {}
            command = payload.get("command")
            if self.controller.execute_command(command):
                logger.info("Executed command: %s", command)
            else:
                logger.warning(
                    "Unknown command: %s (supported: %s)",
                    command,
                    ",".join(SUPPORTED_COMMANDS),
                )
        elif message_type == "register_success":
            logger.info("Register acknowledged by backend")
        elif message_type == "session_control":
            payload = data.get("payload") or {}
            self._set_remote_session_active(
                bool(payload.get("remote_active", False)),
                source="backend",
            )
        elif message_type == "error":
            logger.error("Backend error: %s", data.get("message", "Unknown error"))
        else:
            logger.debug("Received message type: %s", message_type)

    def _notify_session_control(self, remote_active: bool):
        if self._session_control_handler is None:
            return
        try:
            self._session_control_handler(remote_active)
        except Exception as exc:
            logger.error("Session control handler failed: %s", exc)

    def _set_remote_session_active(self, remote_active: bool, source: str):
        remote_active = bool(remote_active)
        if remote_active == self._remote_session_active:
            return

        self._remote_session_active = remote_active
        logger.info(
            "Remote session state updated: active=%s (source=%s)",
            remote_active,
            source,
        )
        self._notify_session_control(remote_active)

    def _handle_backend_disconnected(self):
        if not self.force_local_on_backend_disconnect:
            return

        if self._remote_session_active:
            logger.warning(
                "Backend disconnected while remote session was active; forcing local mode fallback"
            )
            self._set_remote_session_active(False, source="backend_disconnect_fallback")

    async def _status_sender(self, websocket):
        while self._running:
            try:
                await self.send_status_message(websocket)
                await asyncio.sleep(self.status_interval)
            except ConnectionClosed:
                return
            except Exception as exc:
                logger.error("Status send failed: %s", exc)
                await asyncio.sleep(self.status_interval)

    async def _camera_sender(self, websocket):
        if not self.camera_enabled or self.camera_streamer is None:
            return

        last_sent_seq = -1
        while self._running:
            try:
                payload = self.camera_streamer.latest_payload_since(last_sent_seq)
                if payload is not None:
                    last_sent_seq = int(payload.get("seq", last_sent_seq))
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "camera_frame",
                                "payload": payload,
                            }
                        )
                    )

                await asyncio.sleep(self._camera_send_interval)
            except ConnectionClosed:
                return
            except Exception as exc:
                logger.error("Camera frame send failed: %s", exc)
                await asyncio.sleep(self._camera_send_interval)

    def _ensure_camera_started(self):
        if not self.camera_enabled or self._camera_started:
            return
        if self.camera_streamer is None:
            return

        self._camera_started = self.camera_streamer.start()
        if self._camera_started:
            logger.info("Camera streaming enabled")
        else:
            logger.warning("Camera streaming unavailable")

    async def _run_once(self):
        logger.info("Connecting to backend: %s", self.ws_url)
        async with websockets.connect(
            self.ws_url,
            open_timeout=self.ws_open_timeout,
            ping_interval=20,
            ping_timeout=20,
        ) as websocket:
            logger.info("Backend connection established")
            await self.send_register_message(websocket)
            status_task = asyncio.create_task(self._status_sender(websocket))
            camera_task = None
            if self._camera_started:
                camera_task = asyncio.create_task(self._camera_sender(websocket))
            try:
                async for message in websocket:
                    if not self._running:
                        break
                    await self.handle_message(message)
            finally:
                status_task.cancel()
                if camera_task:
                    camera_task.cancel()
                try:
                    await status_task
                except asyncio.CancelledError:
                    pass
                if camera_task:
                    try:
                        await camera_task
                    except asyncio.CancelledError:
                        pass
                self._handle_backend_disconnected()

    async def run_forever(self):
        while self._running:
            self._ensure_camera_started()
            try:
                await self._run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Connection failure: %s", exc)

            if not self._running:
                break

            logger.info("Retrying in %.1f seconds...", self.reconnect_interval)
            await asyncio.sleep(self.reconnect_interval)


async def _async_main():
    client = PiWebSocketClient(
        reconnect_interval=_env_float("FAMILY_ROBOT_RECONNECT_INTERVAL", 3.0),
        status_interval=_env_float("FAMILY_ROBOT_STATUS_INTERVAL", 2.0),
        camera_enabled=_env_bool("FAMILY_ROBOT_CAMERA_ENABLED", True),
        camera_width=_env_int("FAMILY_ROBOT_CAMERA_WIDTH", 640),
        camera_height=_env_int("FAMILY_ROBOT_CAMERA_HEIGHT", 360),
        camera_fps=_env_int("FAMILY_ROBOT_CAMERA_FPS", 10),
        camera_jpeg_quality=_env_int("FAMILY_ROBOT_CAMERA_JPEG_QUALITY", 70),
        force_local_on_backend_disconnect=_env_bool(
            "FAMILY_ROBOT_FORCE_LOCAL_ON_BACKEND_DISCONNECT", True
        ),
        ws_open_timeout=_env_float("FAMILY_ROBOT_WS_OPEN_TIMEOUT", 8.0),
    )
    await client.run_forever()


def main():
    logger.info("Pi remote client startup")
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        logger.info("Pi remote client stopped by user")


if __name__ == "__main__":
    main()
