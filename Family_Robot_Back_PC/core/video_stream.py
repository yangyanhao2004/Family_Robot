import asyncio
import logging
import threading
import time
from typing import Optional, Tuple


logger = logging.getLogger("backend.video")


class VideoStreamHub:
    """In-memory latest-frame hub for backend MJPEG streaming."""

    def __init__(self, max_frame_bytes: int = 2_000_000):
        self.max_frame_bytes = max_frame_bytes
        self._lock = threading.Lock()
        self._latest_seq = 0
        self._latest_frame: Optional[bytes] = None

    async def publish_frame(self, frame_bytes: bytes):
        if not frame_bytes:
            return

        if len(frame_bytes) > self.max_frame_bytes:
            logger.warning(
                "Drop oversized camera frame: %s bytes (max=%s)",
                len(frame_bytes),
                self.max_frame_bytes,
            )
            return

        with self._lock:
            self._latest_frame = frame_bytes
            self._latest_seq += 1

    async def wait_next_frame(
        self,
        last_seq: int,
        timeout_seconds: float = 20.0,
    ) -> Optional[Tuple[int, bytes]]:
        # Poll with a short sleep to avoid loop-bound primitives that may break
        # when uvicorn serves requests on a different event loop instance.
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            with self._lock:
                if self._latest_frame is not None and self._latest_seq > last_seq:
                    return self._latest_seq, self._latest_frame
            await asyncio.sleep(0.03)
        return None


video_hub = VideoStreamHub()
