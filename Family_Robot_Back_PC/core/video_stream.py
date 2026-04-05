import asyncio
import logging
from typing import Optional, Tuple


logger = logging.getLogger("backend.video")


class VideoStreamHub:
    """In-memory latest-frame hub for backend MJPEG streaming."""

    def __init__(self, max_frame_bytes: int = 2_000_000):
        self.max_frame_bytes = max_frame_bytes
        self._condition = asyncio.Condition()
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

        async with self._condition:
            self._latest_frame = frame_bytes
            self._latest_seq += 1
            self._condition.notify_all()

    async def wait_next_frame(
        self,
        last_seq: int,
        timeout_seconds: float = 20.0,
    ) -> Optional[Tuple[int, bytes]]:
        try:
            async with self._condition:
                await asyncio.wait_for(
                    self._condition.wait_for(
                        lambda: self._latest_frame is not None and self._latest_seq > last_seq
                    ),
                    timeout=timeout_seconds,
                )
                return self._latest_seq, self._latest_frame
        except asyncio.TimeoutError:
            return None


video_hub = VideoStreamHub()
