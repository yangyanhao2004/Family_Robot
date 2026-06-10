import asyncio
import json
import logging
import os
from typing import Callable, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from .robot import SUPPORTED_COMMANDS, RobotController, SerialRobotController
from .webrtc_call import PiWebRTCCallBridge
from senses.camera_streamer import CameraStreamer
from brain.voice_commands import drain_voice_commands


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
        wake_word_control_handler: Optional[Callable[[bool], None]] = None,
        voice_reminder_handler: Optional[Callable[[str], None]] = None,
        force_local_on_backend_disconnect: bool = True,
        ws_open_timeout: float = 8.0,
    ):
        self.ws_url = ws_url or _build_ws_url()
        self.reconnect_interval = reconnect_interval
        self.status_interval = status_interval

        # Prefer real STM32 serial link; fall back to software simulator.
        if controller is not None:
            self.controller = controller
        else:
            serial_ctrl = SerialRobotController(
                forward_speed=_env_float("FAMILY_ROBOT_FORWARD_SPEED", 30.0),
                turn_speed=_env_float("FAMILY_ROBOT_TURN_SPEED", 18.0),
            )
            if serial_ctrl.open():
                self.controller = serial_ctrl
                logger.info("Using SerialRobotController (STM32 hardware)")
            else:
                self.controller = RobotController()
                logger.info("Using RobotController (software simulator)")

        self._running = True

        self.camera_enabled = camera_enabled
        self.camera_fps = max(1, int(camera_fps))
        self._camera_send_interval = 1.0 / float(self.camera_fps)
        self.camera_streamer = camera_streamer
        self._camera_started = False
        self._remote_session_active = False
        self._session_control_handler = session_control_handler
        self._wake_word_control_handler = wake_word_control_handler
        self._voice_reminder_handler = voice_reminder_handler
        self.force_local_on_backend_disconnect = force_local_on_backend_disconnect
        self.ws_open_timeout = max(2.0, float(ws_open_timeout))

        # Mic ownership coordination: WebRTC call takes mic from wake word,
        # returns it when the call ends.
        async def _on_mic_ownership(acquire: bool):
            handler = self._wake_word_control_handler
            if handler is None:
                return
            if acquire:
                logger.info("Mic ownership: WebRTC acquiring mic from wake word")
                handler(True)
            else:
                logger.info("Mic ownership: WebRTC releasing mic back to wake word")
                handler(False)

        self._webrtc_call_bridge = PiWebRTCCallBridge(
            mic_ownership_handler=_on_mic_ownership,
        )

        if self.camera_enabled and self.camera_streamer is None:
            self.camera_streamer = CameraStreamer(
                width=camera_width,
                height=camera_height,
                fps=self.camera_fps,
                jpeg_quality=camera_jpeg_quality,
            )

    def stop(self):
        self._running = False
        if hasattr(self.controller, "close"):
            self.controller.close()
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

    async def handle_message(self, websocket, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.error("Invalid message format: %s", message)
            return

        message_type = data.get("type")
        if message_type == "command":
            payload = data.get("payload") or {}
            command = payload.get("command")
            angle = payload.get("angle", 90.0)
            if self.controller.execute_command(command, float(angle)):
                logger.info("Executed command: %s (angle=%.1f)", command, float(angle))
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
        elif message_type == "webrtc_signaling":
            signaling_data = data.get("data") or {}
            await self._webrtc_call_bridge.handle_signaling(
                signaling_data=signaling_data,
                send_json=lambda payload: self._send_json(websocket, payload),
            )
        elif message_type == "voice_reminder":
            payload = data.get("payload") or {}
            text = payload.get("text", "")
            logger.info("Voice reminder received: %s", text)
            if self._voice_reminder_handler and text:
                self._voice_reminder_handler(text)
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

        if not remote_active:
            # Frontend disconnected — tear down any active WebRTC call so
            # the mic is released promptly.  Otherwise wake word resume would
            # race with the ICE timeout (which can take 30+ seconds).
            asyncio.create_task(self._webrtc_call_bridge.close())

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

    async def _voice_cmd_poller(self):
        """Poll for voice commands from the orchestrator thread."""
        while self._running:
            try:
                cmds = drain_voice_commands()
                for cmd in cmds:
                    command = cmd.get("command", "stop")
                    angle = cmd.get("angle", 90.0)
                    duration = cmd.get("duration")
                    logger.info(f"Voice command: {command} (angle={angle}, duration={duration})")
                    if command == "stop" or command.startswith("speed_"):
                        self.controller.execute_command(command, float(angle))
                    else:
                        self.controller.execute_command(command, float(angle))
                        if duration and isinstance(duration, (int, float)) and duration > 0:
                            await asyncio.sleep(float(duration))
                            self.controller.execute_command("stop", 90.0)
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Voice command poller error: {e}")
                await asyncio.sleep(1.0)

    async def _send_json(self, websocket, payload: dict):
        await websocket.send(json.dumps(payload))

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
            voice_cmd_task = asyncio.create_task(self._voice_cmd_poller())
            try:
                async for message in websocket:
                    if not self._running:
                        break
                    await self.handle_message(websocket, message)
            finally:
                status_task.cancel()
                if camera_task:
                    camera_task.cancel()
                voice_cmd_task.cancel()
                try:
                    await status_task
                except asyncio.CancelledError:
                    pass
                if camera_task:
                    try:
                        await camera_task
                    except asyncio.CancelledError:
                        pass
                await self._webrtc_call_bridge.close()
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
