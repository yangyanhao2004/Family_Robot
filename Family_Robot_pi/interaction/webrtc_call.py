"""
Pi-side WebRTC audio bridge for browser <-> Raspberry Pi voice calls.

Signaling is relayed via existing backend WebSocket messages:
  {"type":"webrtc_signaling","data":{...}}
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
from typing import Awaitable, Callable, Dict, Iterable, Optional

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaPlayer, MediaRecorder
    from aiortc.sdp import candidate_from_sdp

    AIORTC_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    RTCPeerConnection = None  # type: ignore
    RTCSessionDescription = None  # type: ignore
    MediaPlayer = None  # type: ignore
    MediaRecorder = None  # type: ignore
    candidate_from_sdp = None  # type: ignore
    AIORTC_AVAILABLE = False


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


class PiWebRTCCallBridge:
    """Handle one active WebRTC call session on Raspberry Pi."""

    _cached_mic_source: Optional[str] = None
    _cached_spk_target: Optional[str] = None

    def __init__(self):
        self._pc = None
        self._mic_player = None
        self._speaker_recorder = None
        self._lock = asyncio.Lock()
        self._availability_warned = False

    async def close(self):
        async with self._lock:
            await self._close_locked()

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

        self._mic_player = self._create_mic_player()
        if self._mic_player is not None and self._mic_player.audio is not None:
            pc.addTrack(self._mic_player.audio)
        else:
            logger.warning("No microphone track available for Pi WebRTC upload")

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

    def _create_mic_player(self):
        if not AIORTC_AVAILABLE:
            return None

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
        candidates = list(
            _dedupe(
                ordered
                + [
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
