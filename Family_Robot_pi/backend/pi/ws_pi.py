import asyncio
import base64
import binascii
import logging

from fastapi import WebSocket, WebSocketDisconnect

from backend.core.connection_manager import manager
from backend.core.message_router import router
from backend.core.video_stream import video_hub
from backend.models.common import ErrorMessage, RegisterMessage
from backend.pi.handlers import handle_status_message, handle_webrtc_signaling_message

logger = logging.getLogger("backend.pi")


async def websocket_pi_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info("Pi client registered: %s:%s", client_ip, client_port)
    manager.register_pi(websocket)
    await _sync_remote_session_state_to_pi()

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                message_type = data.get("type")
                if not message_type:
                    raise ValueError("Missing message type")

                if message_type == "register":
                    RegisterMessage(**data)
                    await websocket.send_json({"type": "register_success"})
                elif message_type == "status":
                    await handle_status_message(data)
                    await router.route_message("robot", data)
                elif message_type == "camera_frame":
                    await _handle_camera_frame(data)
                elif message_type == "webrtc_signaling":
                    await handle_webrtc_signaling_message(data)
                    await router.route_message("robot", data)
                else:
                    logger.warning("Unknown Pi message: %s", message_type)
            except WebSocketDisconnect:
                raise
            except asyncio.TimeoutError:
                continue
            except Exception as exc:
                logger.error("Pi message error: %s", exc)
                try:
                    await manager.send_to_pi(
                        ErrorMessage(type="error", message=f"Invalid message: {exc}").model_dump()
                    )
                except WebSocketDisconnect:
                    raise
    except WebSocketDisconnect:
        logger.info("Pi disconnected: %s:%s", client_ip, client_port)
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("Pi connection error %s:%s: %s", client_ip, client_port, exc)
        try:
            await manager.send_to_pi(
                ErrorMessage(type="error", message=f"Connection error: {exc}").model_dump()
            )
        except Exception:
            pass
        finally:
            manager.disconnect(websocket)


async def _handle_camera_frame(data: dict):
    payload = data.get("payload") or {}
    frame_b64 = payload.get("data")
    if not frame_b64:
        return
    try:
        frame_bytes = base64.b64decode(frame_b64, validate=True)
    except (binascii.Error, ValueError):
        logger.warning("Invalid base64 camera frame")
        return
    await video_hub.publish_frame(frame_bytes)


async def _sync_remote_session_state_to_pi():
    await manager.send_to_pi({
        "type": "session_control",
        "payload": {"remote_active": manager.is_web_connected()},
    })
