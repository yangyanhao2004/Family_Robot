import asyncio
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.core.connection_manager import manager
from backend.core.video_stream import video_hub
from backend.internal.voice_reminder import router as internal_router
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


@app.get("/video/frame")
async def video_frame():
    """返回最新的单帧 JPEG 快照，供鸿蒙等不支持 MJPEG 流的客户端轮询"""
    jpeg_bytes = video_hub.latest_frame
    if jpeg_bytes is None:
        return Response(content=b"", media_type="image/jpeg", status_code=204)
    return Response(content=jpeg_bytes, media_type="image/jpeg",
                    headers={"Cache-Control": "no-cache", "Pragma": "no-cache"})


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


PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)
app.mount("/photos", StaticFiles(directory=PHOTOS_DIR), name="photos")


@app.get("/api/photos")
async def list_photos():
    items = []
    if os.path.isdir(PHOTOS_DIR):
        for fname in sorted(os.listdir(PHOTOS_DIR), reverse=True):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                fpath = os.path.join(PHOTOS_DIR, fname)
                mtime = os.path.getmtime(fpath)
                from datetime import datetime, timezone, timedelta
                tz = timezone(timedelta(hours=8))
                date_str = datetime.fromtimestamp(mtime, tz).strftime("%Y-%m-%d")
                items.append({
                    "id": fname,
                    "url": f"/photos/{fname}",
                    "date": date_str,
                })
    return items


app.include_router(internal_router)


@app.get("/")
async def root():
    return {"message": "Family Robot backend running"}



