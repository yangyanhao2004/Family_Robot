import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from core.connection_manager import manager
from core.message_router import router
from front.handlers import handle_command_message, handle_webrtc_signaling_message
from models.common import ErrorMessage, RegisterMessage


logger = logging.getLogger("backend.front")


async def websocket_front_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info("Frontend client registered: %s:%s", client_ip, client_port)
    manager.register_web(websocket)
    await _notify_remote_session_active(True)

    try:
        logger.info("Start handling frontend messages from %s:%s", client_ip, client_port)
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                logger.debug(
                    "Message from frontend %s:%s -> %s",
                    client_ip,
                    client_port,
                    data.get("type"),
                )

                try:
                    message_type = data.get("type")
                    if not message_type:
                        raise ValueError("Missing message type")

                    if message_type == "register":
                        RegisterMessage(**data)
                        await websocket.send_json({"type": "register_success"})
                        logger.info("Register success sent to frontend %s:%s", client_ip, client_port)
                    elif message_type == "command":
                        await handle_command_message(data)
                        await router.route_message("web", data)
                    elif message_type == "webrtc_signaling":
                        await handle_webrtc_signaling_message(data)
                        await router.route_message("web", data)
                    elif message_type == "heartbeat":
                        # Keepalive only.
                        pass
                    else:
                        logger.warning(
                            "Unknown frontend message type from %s:%s -> %s",
                            client_ip,
                            client_port,
                            message_type,
                        )
                except Exception as exc:
                    logger.error("Frontend message handling error from %s:%s: %s", client_ip, client_port, exc)
                    await manager.send_to_web(
                        ErrorMessage(type="error", message=f"Invalid message: {exc}").model_dump()
                    )
            except asyncio.TimeoutError:
                logger.debug("Frontend receive timeout for %s:%s, keep alive", client_ip, client_port)
                continue
    except WebSocketDisconnect:
        logger.info("Frontend disconnected: %s:%s", client_ip, client_port)
        if manager.web_connection is websocket:
            await _notify_remote_session_active(False)
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("Frontend connection error %s:%s: %s", client_ip, client_port, exc)
        try:
            await manager.send_to_web(
                ErrorMessage(type="error", message=f"Connection error: {exc}").model_dump()
            )
        except Exception:
            pass
        finally:
            if manager.web_connection is websocket:
                await _notify_remote_session_active(False)
            manager.disconnect(websocket)


async def _notify_remote_session_active(active: bool):
    """Tell Pi whether a remote frontend session is active."""
    message = {
        "type": "session_control",
        "payload": {"remote_active": active},
    }
    await manager.send_to_pi(message)
    logger.info("Sent session_control to Pi: remote_active=%s", active)
