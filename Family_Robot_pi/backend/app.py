import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.core.connection_manager import manager
from backend.core.rtc_service import rtc_service
from backend.core.video_stream import video_hub
from backend.models.common import BaseMessage, RegisterMessage, ErrorMessage

logger = logging.getLogger('backend')

app = FastAPI(
    title="Family Robot Backend",
    description="WebSocket routing, WebRTC signaling, and MJPEG streaming",
    version="1.0.0",
    websocket_max_message_size=5 * 1024 * 1024
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _websocket_entrypoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
        base_msg = BaseMessage(**data)

        if base_msg.type == "register":
            register_msg = RegisterMessage(**data)
            role = register_msg.role
            await websocket.send_json({"type": "register_success"})

            if role == "web":
                from backend.front.ws_front import websocket_front_endpoint
                await websocket_front_endpoint(websocket)
            elif role == "robot":
                from backend.pi.ws_pi import websocket_pi_endpoint
                await websocket_pi_endpoint(websocket)
            else:
                await websocket.send_json(
                    ErrorMessage(type="error", message="Invalid role").model_dump()
                )
                await websocket.close()
        else:
            await websocket.send_json(
                ErrorMessage(type="error", message="Please send register message first").model_dump()
            )
            await websocket.close()
    except asyncio.TimeoutError:
        await websocket.close()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket entry error: {e}")
        try:
            await websocket.send_json(
                ErrorMessage(type="error", message=f"Error: {e}").model_dump()
            )
            await websocket.close()
        except Exception:
            manager.disconnect(websocket)


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await _websocket_entrypoint(websocket)


@app.get("/video/stream")
async def video_stream():
    async def mjpeg_generator():
        last_seq = 0
        try:
            while True:
                frame_item = await video_hub.wait_next_frame(last_seq)
                if frame_item is None:
                    continue
                last_seq, jpeg_bytes = frame_item
                header = (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Cache-Control: no-cache\r\n"
                    b"Pragma: no-cache\r\n"
                    + f"Content-Length: {len(jpeg_bytes)}\r\n\r\n".encode("ascii")
                )
                yield header + jpeg_bytes + b"\r\n"
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                  "Pragma": "no-cache"},
    )


@app.get("/")
async def root():
    return {"message": "Family Robot backend running"}


@app.websocket("/ws/rtc")
async def websocket_rtc_endpoint(websocket: WebSocket):
    try:
        data = await websocket.receive_json()
        if data.get('type') == 'register':
            client_id = data.get('client_id')
            if not client_id:
                await websocket.close(code=1008, reason="Missing client_id")
                return

            await rtc_service.connect(websocket, client_id)
            await websocket.send_json({"type": "register_success", "client_id": client_id})

            while True:
                try:
                    data = await websocket.receive_json()
                    await rtc_service.handle_signaling(client_id, data)
                except WebSocketDisconnect:
                    rtc_service.disconnect(client_id)
                    break
                except Exception as e:
                    logger.error(f"RTC message error: {e}")
                    try:
                        await websocket.send_json({
                            "type": "error", "message": f"Message handling failed: {e}"
                        })
                    except Exception:
                        rtc_service.disconnect(client_id)
                        break
        else:
            await websocket.close(code=1008, reason="Missing register message")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"RTC connection error: {e}")
