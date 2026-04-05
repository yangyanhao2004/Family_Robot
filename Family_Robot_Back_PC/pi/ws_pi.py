import asyncio
import base64
import binascii
import logging

from fastapi import WebSocket, WebSocketDisconnect

from core.connection_manager import manager
from core.message_router import router
from core.video_stream import video_hub
from models.common import ErrorMessage, RegisterMessage
from pi.handlers import handle_status_message, handle_webrtc_signaling_message


logger = logging.getLogger("backend.pi")


async def websocket_pi_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info("Pi client registered: %s:%s", client_ip, client_port)
    manager.register_pi(websocket)

    try:
        logger.info("Start handling Pi messages from %s:%s", client_ip, client_port)
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                logger.debug("Message from Pi %s:%s -> %s", client_ip, client_port, data.get("type"))

                try:
                    message_type = data.get("type")
                    if not message_type:
                        raise ValueError("Missing message type")

                    if message_type == "register":
                        RegisterMessage(**data)
                        await websocket.send_json({"type": "register_success"})
                        logger.info("Register success sent to Pi %s:%s", client_ip, client_port)
                    elif message_type == "status":
                        await handle_status_message(data)
                        await router.route_message("robot", data)
                    elif message_type == "camera_frame":
                        await _handle_camera_frame(data, client_ip, client_port)
                    elif message_type == "webrtc_signaling":
                        await handle_webrtc_signaling_message(data)
                        await router.route_message("robot", data)
                    else:
                        logger.warning(
                            "Unknown Pi message type from %s:%s -> %s",
                            client_ip,
                            client_port,
                            message_type,
                        )
                except Exception as exc:
                    logger.error("Pi message handling error from %s:%s: %s", client_ip, client_port, exc)
                    await manager.send_to_pi(
                        ErrorMessage(type="error", message=f"Invalid message: {exc}").model_dump()
                    )
            except asyncio.TimeoutError:
                logger.debug("Pi receive timeout for %s:%s, keep alive", client_ip, client_port)
                continue
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


async def _handle_camera_frame(data: dict, client_ip: str, client_port: int):
    payload = data.get("payload") or {}
    frame_b64 = payload.get("data")
    if not frame_b64:
        logger.debug("Empty camera frame payload from %s:%s", client_ip, client_port)
        return

    try:
        frame_bytes = base64.b64decode(frame_b64, validate=True)
    except (binascii.Error, ValueError):
        logger.warning("Invalid base64 camera frame from %s:%s", client_ip, client_port)
        return

    await video_hub.publish_frame(frame_bytes)
