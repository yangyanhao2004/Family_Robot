"""
Pi-side WebRTC audio bridge for browser <-> Raspberry Pi voice calls.

Signaling is relayed via existing backend WebSocket messages:
  {"type":"webrtc_signaling","data":{...}}
"""

from __future__ import annotations

import asyncio
import logging
import os
import queue
import re
import subprocess
import threading
import time
from typing import Awaitable, Callable, Dict, Iterable, Optional

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaPlayer, MediaRecorder
    from aiortc.mediastreams import AudioFrame, MediaStreamTrack
    from aiortc.sdp import candidate_from_sdp

    AIORTC_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    RTCPeerConnection = None  # type: ignore
    RTCSessionDescription = None  # type: ignore
    MediaPlayer = None  # type: ignore
    MediaRecorder = None  # type: ignore
    MediaStreamTrack = None  # type: ignore
    AudioFrame = None  # type: ignore
    candidate_from_sdp = None  # type: ignore
    AIORTC_AVAILABLE = False

try:
    import numpy as np
    import sounddevice as sd

    SOUNDDEVICE_AVAILABLE = True
except Exception:  # pragma: no cover
    np = None  # type: ignore
    sd = None  # type: ignore
    SOUNDDEVICE_AVAILABLE = False


logger = logging.getLogger("interaction.webrtc_call")

SendJson = Callable[[Dict], Awaitable[None]]

DEFAULT_WEBRTC_MIC_DEVICE_NAME = "USB PnP Sound Device"
DEFAULT_WEBRTC_SPK_DEVICE_NAME = "bcm2835 Headphones"
_ALSA_CARD_DEVICE_RE = re.compile(
    r"^card\s+(\d+):.*?,\s*device\s+(\d+):",
    re.IGNORECASE,
)


def _dedupe(values: Iterable[str]):
    seen = set()
    for value in values:
        normalized = (value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        yield normalized


def _run_command_lines(command: list[str]):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return []
    return result.stdout.splitlines()


def _find_alsa_card_device(command: list[str], name_substring: str) -> Optional[str]:
    target = (name_substring or "").strip().lower()
    if not target:
        return None

    for line in _run_command_lines(command):
        line_lower = line.lower()
        if not line_lower.startswith("card "):
            continue
        if target not in line_lower:
            continue

        match = _ALSA_CARD_DEVICE_RE.search(line)
        if match:
            return "plughw:{},{}".format(match.group(1), match.group(2))

        card_part = line.split(":", 1)[0].replace("card", "").strip()
        if card_part.isdigit():
            return "plughw:{},0".format(card_part)

    return None


if AIORTC_AVAILABLE:

    class SDAudioStreamTrack(MediaStreamTrack):
        """Audio stream track backed by sounddevice (PortAudio).

        Audio data crosses from the PortAudio C callback thread into the
        asyncio event loop via a thread-safe ``queue.Queue`` and
        ``loop.run_in_executor``, avoiding the edge cases of cross-thread
        ``asyncio.Queue.put_nowait``.
        """

        kind = "audio"

        def __init__(
            self,
            device: Optional[int],
            sample_rate: int = 48000,
            channels: int = 1,
            blocksize: int = 960,
        ):
            super().__init__()
            self._device = device
            self._sample_rate = sample_rate
            self._channels = channels
            self._blocksize = blocksize
            self._queue: queue.Queue = queue.Queue(maxsize=4)
            self._stream: Optional[sd.InputStream] = None
            self._samples_elapsed = 0
            self._stopped = threading.Event()
            self._recv_count = 0

        def _callback(self, indata, frames, time_info, status):
            if status:
                logger.warning("SDAudioStreamTrack status flag: %s", status)
                return
            if self._stopped.is_set():
                return
            try:
                self._queue.put_nowait(bytes(indata[:frames]))
            except queue.Full:
                pass

        def start(self) -> None:
            self._stopped.clear()
            self._recv_count = 0
            self._stream = sd.RawInputStream(
                device=self._device,
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="int16",
                blocksize=self._blocksize,
                callback=self._callback,
                latency="low",
            )
            self._stream.start()

        def stop(self) -> None:
            self._stopped.set()
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            # Unblock any pending queue.get() in recv()
            try:
                self._queue.put_nowait(b"")
            except queue.Full:
                pass

        async def recv(self):
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, self._queue.get)
            if self._stopped.is_set() or not data:
                if not data:
                    raise RuntimeError("SDAudioStreamTrack stopped")
            self._samples_elapsed += len(data) // 2
            pts = self._samples_elapsed

            # PyAV 12+: build AudioFrame from numpy array
            arr = np.frombuffer(data, dtype=np.int16).copy()
            frame = AudioFrame.from_ndarray(
                arr.reshape(1, -1),
                format="s16",
                layout="mono",
            )
            frame.sample_rate = self._sample_rate
            frame.pts = pts

            # Log first frames for diagnostics
            self._recv_count += 1
            if self._recv_count <= 3:
                peak = np.max(np.abs(arr))
                logger.info(
                    "SDAudioStreamTrack frame #%d: %d samples, peak=%d, pts=%d",
                    self._recv_count,
                    len(arr),
                    peak,
                    pts,
                )

            return frame

else:
    SDAudioStreamTrack = None  # type: ignore


class _MicSource:
    """Unified wrapper for mic capture backends."""

    def __init__(self, audio, stop_fn):
        self.audio = audio
        self._stop_fn = stop_fn

    def stop(self):
        self._stop_fn()


MicOwnershipHandler = Callable[[bool], Awaitable[None]]


class PiWebRTCCallBridge:
    """Handle one active WebRTC call session on Raspberry Pi.

    Mic ownership model:
    - Default: wake word detector owns the mic
    - WebRTC call starts: mic transferred to WebRTC (wake word paused)
    - WebRTC call ends: mic returned to wake word detector
    Ownership is coordinated via the ``mic_ownership_handler`` callback.
    """

    _cached_mic_source: Optional[str] = None
    _cached_spk_target: Optional[str] = None

    def __init__(
        self,
        mic_ownership_handler: Optional[MicOwnershipHandler] = None,
    ):
        self._pc = None
        self._mic_player = None
        self._speaker_recorder = None
        self._lock = asyncio.Lock()
        self._availability_warned = False
        self._mic_ownership_handler = mic_ownership_handler
        self._mic_owned = False

    async def close(self):
        async with self._lock:
            await self._close_locked()
            await self._release_mic_locked()

    async def handle_signaling(self, signaling_data: Dict, send_json: SendJson):
        if not AIORTC_AVAILABLE:
            if not self._availability_warned:
                logger.warning(
                    "aiortc is not installed; two-way voice call is unavailable on Pi"
                )
                self._availability_warned = True
                await send_json(
                    {
                        "type": "error",
                        "message": "Pi missing aiortc dependency, call unavailable",
                    }
                )
            return

        signal_type = (signaling_data or {}).get("type")
        if not signal_type:
            return

        async with self._lock:
            if signal_type == "offer":
                await self._handle_offer_locked(signaling_data, send_json)
            elif signal_type == "candidate":
                await self._handle_candidate_locked(signaling_data)
            elif signal_type == "answer":
                # Pi is answerer in current flow.
                pass
            else:
                logger.warning("Unknown WebRTC signal type from backend: %s", signal_type)

    async def _handle_offer_locked(self, signaling_data: Dict, send_json: SendJson):
        offer = (signaling_data or {}).get("offer")
        if not offer or "sdp" not in offer or "type" not in offer:
            logger.warning("Invalid WebRTC offer payload from backend")
            return

        await self._close_locked()
        pc = RTCPeerConnection()
        self._pc = pc

        @pc.on("track")
        async def on_track(track):
            if track.kind != "audio":
                return
            self._speaker_recorder = self._create_speaker_recorder()
            if self._speaker_recorder is None:
                logger.warning("No speaker recorder available for remote audio playback")
                return
            self._speaker_recorder.addTrack(track)
            await self._speaker_recorder.start()

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            state = pc.connectionState
            logger.info("Pi WebRTC connection state: %s", state)
            if state in {"failed", "closed", "disconnected"}:
                await self.close()

        # Acquire mic ownership from wake word detector before capture
        await self._acquire_mic_locked()

        self._mic_player = self._create_mic_player()
        if self._mic_player is not None and self._mic_player.audio is not None:
            pc.addTrack(self._mic_player.audio)
        else:
            logger.warning("No microphone track available for Pi WebRTC upload")
            await self._release_mic_locked()

        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        )

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await self._wait_for_ice_gathering_complete(pc, timeout=0.3)

        local = pc.localDescription
        await send_json(
            {
                "type": "webrtc_signaling",
                "data": {
                    "type": "answer",
                    "answer": {
                        "type": local.type,
                        "sdp": local.sdp,
                    },
                },
            }
        )

    async def _handle_candidate_locked(self, signaling_data: Dict):
        if self._pc is None:
            return

        candidate = (signaling_data or {}).get("candidate")
        if not candidate:
            return

        candidate_line = candidate.get("candidate")
        if not candidate_line:
            return

        try:
            if candidate_line.startswith("candidate:"):
                candidate_line = candidate_line[len("candidate:") :]

            parsed = candidate_from_sdp(candidate_line)
            parsed.sdpMid = candidate.get("sdpMid")
            parsed.sdpMLineIndex = candidate.get("sdpMLineIndex")
            await self._pc.addIceCandidate(parsed)
        except Exception as exc:
            logger.warning("Failed to add remote ICE candidate: %s", exc)

    async def _wait_for_ice_gathering_complete(self, pc, timeout: float):
        if pc.iceGatheringState == "complete":
            return

        done = asyncio.Event()

        @pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            if pc.iceGatheringState == "complete":
                done.set()

        try:
            await asyncio.wait_for(done.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

    async def _close_locked(self):
        if self._speaker_recorder is not None:
            try:
                await self._speaker_recorder.stop()
            except Exception:
                pass
            self._speaker_recorder = None

        if self._mic_player is not None:
            try:
                stop_fn = getattr(self._mic_player, "stop", None)
                if callable(stop_fn):
                    stop_fn()
            except Exception:
                pass
            self._mic_player = None

        if self._pc is not None:
            try:
                await self._pc.close()
            except Exception:
                pass
            self._pc = None

    async def _acquire_mic_locked(self):
        """Request mic ownership from the wake word detector."""
        if self._mic_owned:
            return
        if self._mic_ownership_handler is not None:
            logger.info("Mic ownership: requesting transfer from wake word to WebRTC")
            await self._mic_ownership_handler(True)
            # Wait for wake word detector's PortAudio stream to fully close
            # before opening a new one for WebRTC, avoiding EBUSY on ALSA.
            await asyncio.sleep(0.5)
        self._mic_owned = True

    async def _release_mic_locked(self):
        """Return mic ownership to the wake word detector."""
        if not self._mic_owned:
            return
        if self._mic_ownership_handler is not None:
            logger.info("Mic ownership: returning from WebRTC to wake word")
            await self._mic_ownership_handler(False)
        self._mic_owned = False

    def _create_mic_player(self):
        """Create a microphone source for WebRTC upload.

        Tries the following backends in order:
        1. sounddevice (PortAudio) — proven on Pi, shares with wake word detector
        2. MediaPlayer (ffmpeg ALSA) — fallback for non-Pi environments
        """
        if not AIORTC_AVAILABLE:
            return None

        # --- Primary: sounddevice-based capture ---
        if SOUNDDEVICE_AVAILABLE:
            track = self._create_sd_mic_track()
            if track is not None:
                logger.info("Using Pi WebRTC microphone source: sounddevice")
                return _MicSource(track, track.stop)

        # --- Fallback: MediaPlayer (ffmpeg ALSA) ---
        return self._create_alsa_mic_player()

    def _find_sd_mic_device(self) -> Optional[int]:
        """Find the sounddevice input device index by name."""
        device_name = os.getenv(
            "FAMILY_ROBOT_WEBRTC_MIC_DEVICE_NAME",
            DEFAULT_WEBRTC_MIC_DEVICE_NAME,
        )
        if not device_name:
            return None

        try:
            for idx, dev in enumerate(sd.query_devices()):
                if (
                    device_name.lower() in dev["name"].lower()
                    and dev["max_input_channels"] > 0
                ):
                    return idx
        except Exception:
            pass
        return None

    def _create_sd_mic_track(self) -> Optional["SDAudioStreamTrack"]:
        if not SOUNDDEVICE_AVAILABLE or SDAudioStreamTrack is None:
            return None

        try:
            device = self._find_sd_mic_device()
            sample_rate = int(
                os.getenv("FAMILY_ROBOT_WEBRTC_MIC_SAMPLE_RATE", "48000")
            )
            channels = int(os.getenv("FAMILY_ROBOT_WEBRTC_MIC_CHANNELS", "1"))
            blocksize = sample_rate // 100  # 10ms frames for low latency

            track = SDAudioStreamTrack(
                device=device,
                sample_rate=sample_rate,
                channels=channels,
                blocksize=blocksize,
            )
            track.start()
            return track
        except Exception as exc:
            logger.warning("Failed to create sounddevice mic track: %s", exc)
            return None

    def _create_alsa_mic_player(self):

        explicit_source = os.getenv("FAMILY_ROBOT_WEBRTC_MIC_SOURCE", "")
        device_name = os.getenv(
            "FAMILY_ROBOT_WEBRTC_MIC_DEVICE_NAME",
            DEFAULT_WEBRTC_MIC_DEVICE_NAME,
        )
        auto_source = _find_alsa_card_device(["arecord", "-l"], device_name)

        fmt = os.getenv("FAMILY_ROBOT_WEBRTC_MIC_FORMAT", "alsa")
        options = {
            "channels": os.getenv("FAMILY_ROBOT_WEBRTC_MIC_CHANNELS", "1"),
            "sample_rate": os.getenv("FAMILY_ROBOT_WEBRTC_MIC_SAMPLE_RATE", "48000"),
        }
        prefer_explicit = explicit_source.strip().lower() not in {"", "default", "auto"}
        ordered = (
            [explicit_source, auto_source or ""]
            if prefer_explicit
            else [auto_source or "", explicit_source]
        )
        # Build dsnoop candidates for mic sharing (ALSA allows concurrent access)
        dsnoop_candidates = []
        if auto_source:
            card_info = _ALSA_CARD_DEVICE_RE.search(auto_source or "")
            if not card_info:
                card_info = _ALSA_CARD_DEVICE_RE.search(explicit_source or "")
            if card_info:
                dsnoop_candidates.extend(
                    [
                        "dsnoop:{},{}".format(card_info.group(1), card_info.group(2)),
                        "dsnoop:CARD={},DEV={}".format(
                            card_info.group(1), card_info.group(2)
                        ),
                    ]
                )

        candidates = list(
            _dedupe(
                ordered
                + dsnoop_candidates
                + [
                    "dsnoop:1,0",
                    "plughw:1,0",
                    "hw:1,0",
                    "default",
                ]
            )
        )

        if PiWebRTCCallBridge._cached_mic_source is not None:
            candidates.insert(0, PiWebRTCCallBridge._cached_mic_source)

        for source in candidates:
            try:
                player = MediaPlayer(source, format=fmt, options=options)
                PiWebRTCCallBridge._cached_mic_source = source
                logger.info("Using Pi WebRTC microphone source: %s", source)
                return player
            except Exception as exc:
                logger.warning(
                    "Failed to create Pi WebRTC microphone input source=%s: %s",
                    source,
                    exc,
                )

        return None

    def _create_speaker_recorder(self):
        if not AIORTC_AVAILABLE:
            return None

        explicit_target = os.getenv("FAMILY_ROBOT_WEBRTC_SPK_TARGET", "")
        device_name = os.getenv(
            "FAMILY_ROBOT_WEBRTC_SPK_DEVICE_NAME",
            DEFAULT_WEBRTC_SPK_DEVICE_NAME,
        )
        auto_target = _find_alsa_card_device(["aplay", "-l"], device_name)

        fmt = os.getenv("FAMILY_ROBOT_WEBRTC_SPK_FORMAT", "alsa")
        options = {
            "channels": os.getenv("FAMILY_ROBOT_WEBRTC_SPK_CHANNELS", "1"),
            "sample_rate": os.getenv("FAMILY_ROBOT_WEBRTC_SPK_SAMPLE_RATE", "48000"),
        }
        prefer_explicit = explicit_target.strip().lower() not in {"", "default", "auto"}
        ordered = (
            [explicit_target, auto_target or ""]
            if prefer_explicit
            else [auto_target or "", explicit_target]
        )
        candidates = list(
            _dedupe(
                ordered
                + [
                    "plughw:0,0",
                    "hw:0,0",
                    "default",
                ]
            )
        )

        if PiWebRTCCallBridge._cached_spk_target is not None:
            candidates.insert(0, PiWebRTCCallBridge._cached_spk_target)

        for target in candidates:
            try:
                recorder = MediaRecorder(target, format=fmt, options=options)
                PiWebRTCCallBridge._cached_spk_target = target
                logger.info("Using Pi WebRTC speaker target: %s", target)
                return recorder
            except Exception as exc:
                logger.warning(
                    "Failed to create Pi WebRTC speaker output target=%s: %s",
                    target,
                    exc,
                )

        return None
