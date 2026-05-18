import asyncio
import logging
import os
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from backend.core.connection_manager import manager
from backend.core.message_router import router
from backend.front.ai_chat import handle_ai_chat, handle_ai_session_end, cleanup_session_for_disconnect
from backend.front.handlers import handle_command_message, handle_webrtc_signaling_message
from backend.models.common import ErrorMessage, RegisterMessage

logger = logging.getLogger("backend.front")

_pending_remote_inactive_task: Optional[asyncio.Task] = None
_ws_user_map: Dict[int, int] = {}


def _session_release_delay_seconds() -> float:
    raw = os.getenv("FAMILY_ROBOT_SESSION_RELEASE_DELAY", "1.5")
    try:
        value = float(raw)
    except ValueError:
        value = 1.5
    return max(0.0, value)


async def websocket_front_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info("Frontend client registered: %s:%s", client_ip, client_port)
    manager.register_web(websocket)
    await _cancel_pending_remote_inactive_task()
    await _notify_remote_session_active(True)

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                message_type = data.get("type")
                if not message_type:
                    raise ValueError("Missing message type")

                if message_type == "register":
                    reg = RegisterMessage(**data)
                    if reg.user_id is not None:
                        _ws_user_map[id(websocket)] = reg.user_id
                    await websocket.send_json({"type": "register_success"})
                elif message_type == "command":
                    should_forward = await handle_command_message(data)
                    if should_forward:
                        await router.route_message("web", data)
                elif message_type == "webrtc_signaling":
                    await handle_webrtc_signaling_message(data)
                    await router.route_message("web", data)
                elif message_type == "ai_chat":
                    await handle_ai_chat(data)
                elif message_type == "ai_session_end":
                    user_id = data.get("payload", {}).get("user_id")
                    if user_id is not None:
                        await handle_ai_session_end(int(user_id))
                elif message_type == "heartbeat":
                    pass
                else:
                    logger.warning("Unknown frontend message: %s", message_type)
            except WebSocketDisconnect:
                raise
            except asyncio.TimeoutError:
                continue
            except Exception as exc:
                logger.error("Frontend message error: %s", exc)
                try:
                    await manager.send_to_web(
                        ErrorMessage(type="error", message=f"Invalid message: {exc}").model_dump()
                    )
                except WebSocketDisconnect:
                    raise
    except WebSocketDisconnect:
        logger.info("Frontend disconnected: %s:%s", client_ip, client_port)
        should_release = manager.web_connection is websocket
        manager.disconnect(websocket)
        cleaned_user = await cleanup_session_for_disconnect(id(websocket), _ws_user_map)
        if cleaned_user is not None:
            logger.info("AI session destroyed for user %s on disconnect", cleaned_user)
        if should_release:
            await _schedule_remote_inactive_notification()
    except Exception as exc:
        logger.error("Frontend connection error %s:%s: %s", client_ip, client_port, exc)
        try:
            await manager.send_to_web(
                ErrorMessage(type="error", message=f"Connection error: {exc}").model_dump()
            )
        except Exception:
            pass
        finally:
            should_release = manager.web_connection is websocket
            manager.disconnect(websocket)
            cleaned_user = await cleanup_session_for_disconnect(id(websocket), _ws_user_map)
            if cleaned_user is not None:
                logger.info("AI session destroyed for user %s on error disconnect", cleaned_user)
            if should_release:
                await _schedule_remote_inactive_notification()


async def _notify_remote_session_active(active: bool):
    message = {"type": "session_control", "payload": {"remote_active": active}}
    await manager.send_to_pi(message)
    logger.info("Sent session_control to Pi: remote_active=%s", active)


async def _schedule_remote_inactive_notification():
    await _cancel_pending_remote_inactive_task()

    async def _delayed_inactive():
        try:
            delay = _session_release_delay_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
            if not manager.is_web_connected():
                await _notify_remote_session_active(False)
        except asyncio.CancelledError:
            return

    global _pending_remote_inactive_task
    _pending_remote_inactive_task = asyncio.create_task(_delayed_inactive())


async def _cancel_pending_remote_inactive_task():
    global _pending_remote_inactive_task
    if _pending_remote_inactive_task is None:
        return
    if _pending_remote_inactive_task.done():
        _pending_remote_inactive_task = None
        return
    _pending_remote_inactive_task.cancel()
    try:
        await _pending_remote_inactive_task
    except asyncio.CancelledError:
        pass
    _pending_remote_inactive_task = None
