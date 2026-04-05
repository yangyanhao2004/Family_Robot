"""
Pi camera capture and frame buffering for low-latency remote preview.

This module is intentionally dependency-tolerant:
- If Picamera2 or Pillow is unavailable, it will fail gracefully.
- The latest frame is always overwritten so stale frames are dropped.
"""

from __future__ import annotations

import base64
import io
import logging
import threading
import time
from typing import Dict, Optional

try:
    from picamera2 import Picamera2  # type: ignore
except Exception:  # pragma: no cover - depends on Pi runtime
    Picamera2 = None  # type: ignore

try:
    from PIL import Image
except Exception:  # pragma: no cover - depends on runtime deps
    Image = None  # type: ignore


logger = logging.getLogger("senses.camera_streamer")


class CameraStreamer:
    """Background camera reader that keeps only the newest JPEG frame."""

    def __init__(
        self,
        width: int = 640,
        height: int = 360,
        fps: int = 10,
        jpeg_quality: int = 70,
    ):
        self.width = max(160, int(width))
        self.height = max(120, int(height))
        self.fps = max(1, int(fps))
        self.jpeg_quality = max(30, min(95, int(jpeg_quality)))

        self._frame_interval = 1.0 / float(self.fps)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._camera = None

        self._lock = threading.Lock()
        self._latest_payload: Optional[Dict[str, object]] = None
        self._seq = 0
        self._last_error_log_monotonic = 0.0

    def start(self) -> bool:
        if self._running:
            return True

        if Picamera2 is None:
            logger.warning("Picamera2 is not available. Camera stream disabled.")
            return False

        if Image is None:
            logger.warning("Pillow is not available. Camera stream disabled.")
            return False

        try:
            self._camera = Picamera2()
            video_config = self._camera.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls={"FrameRate": float(self.fps)},
            )
            self._camera.configure(video_config)
            self._camera.start()
            time.sleep(0.15)
        except Exception as exc:
            logger.exception("Failed to initialize Picamera2: %s", exc)
            self._safe_close_camera()
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="camera-streamer",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Camera streamer started (%sx%s @ %sfps, quality=%s)",
            self.width,
            self.height,
            self.fps,
            self.jpeg_quality,
        )
        return True

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._safe_close_camera()
        logger.info("Camera streamer stopped")

    def latest_payload_since(self, last_seq: int) -> Optional[Dict[str, object]]:
        """Return the latest frame payload only if it is newer than `last_seq`."""
        with self._lock:
            if not self._latest_payload:
                return None
            payload_seq = int(self._latest_payload.get("seq", -1))
            if payload_seq <= last_seq:
                return None
            return self._latest_payload

    def _capture_loop(self):
        while self._running:
            loop_start = time.monotonic()

            try:
                frame = self._camera.capture_array("main")
                if frame is None:
                    self._sleep_remaining(loop_start)
                    continue

                if frame.ndim == 3 and frame.shape[2] == 4:
                    frame = frame[:, :, :3]

                image = Image.fromarray(frame)
                with io.BytesIO() as buffer:
                    image.save(buffer, format="JPEG", quality=self.jpeg_quality, optimize=False)
                    jpeg_bytes = buffer.getvalue()

                payload = {
                    "format": "jpeg",
                    "encoding": "base64",
                    "data": base64.b64encode(jpeg_bytes).decode("ascii"),
                    "width": self.width,
                    "height": self.height,
                    "timestampMs": int(time.time() * 1000),
                    "seq": self._seq,
                }

                with self._lock:
                    self._latest_payload = payload
                    self._seq += 1
            except Exception as exc:
                now = time.monotonic()
                if now - self._last_error_log_monotonic > 2.0:
                    logger.warning("Camera capture/encode error: %s", exc)
                    self._last_error_log_monotonic = now

            self._sleep_remaining(loop_start)

    def _sleep_remaining(self, loop_start_monotonic: float):
        elapsed = time.monotonic() - loop_start_monotonic
        delay = self._frame_interval - elapsed
        if delay > 0:
            time.sleep(delay)

    def _safe_close_camera(self):
        if self._camera is None:
            return

        try:
            self._camera.stop()
        except Exception:
            pass

        try:
            self._camera.close()
        except Exception:
            pass

        self._camera = None
