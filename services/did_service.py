"""
D-ID Service
Generates talking face video notes using D-ID API.
"""
import asyncio
import base64
import logging
import os
import subprocess
import tempfile

import aiohttp

from config import DID_API_KEY, DID_PRESENTER_ID, DID_DRIVER_ID

logger = logging.getLogger(__name__)

DID_BASE = "https://api.d-id.com"
POLL_INTERVAL = 2
POLL_TIMEOUT = 90


def _auth_headers(with_content_type: bool = True) -> dict:
    token = base64.b64encode(f"{DID_API_KEY}:".encode()).decode()
    h = {"Authorization": f"Basic {token}"}
    if with_content_type:
        h["Content-Type"] = "application/json"
    return h


async def _create_clip(audio_bytes: bytes, audio_format: str = "mp3") -> tuple[str | None, str]:
    mime = "audio/mpeg" if audio_format == "mp3" else f"audio/{audio_format}"
    b64 = base64.b64encode(audio_bytes).decode()
    payload = {
        "presenter_id": DID_PRESENTER_ID,
        "script": {
            "type": "audio",
            "audio_base64": f"data:{mime};base64,{b64}"
        },
        "config": {"result_format": "mp4"}
    }
    if DID_DRIVER_ID:
        payload["driver_id"] = DID_DRIVER_ID

    logger.info(f"D-ID request: presenter_id={DID_PRESENTER_ID}, audio_size={len(audio_bytes)}b, format={audio_format}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{DID_BASE}/clips", json=payload, headers=_auth_headers()
            ) as resp:
                body = await resp.text()
                logger.info(f"D-ID response {resp.status}: {body}")
                if resp.status not in (200, 201):
                    return None, f"D-ID {resp.status}: {body}"
                import json as _json
                data = _json.loads(body)
                return data.get("id"), ""
        except Exception as e:
            logger.error(f"D-ID create_clip exception: {e}")
            return None, f"D-ID exception: {e}"


async def _poll_clip(clip_id: str) -> tuple[str | None, str]:
    deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT
    async with aiohttp.ClientSession() as session:
        while asyncio.get_event_loop().time() < deadline:
            try:
                async with session.get(
                    f"{DID_BASE}/clips/{clip_id}",
                    headers=_auth_headers(with_content_type=False)
                ) as resp:
                    data = await resp.json()
                    status = data.get("status")
                    if status == "done":
                        return data.get("result_url"), ""
                    if status == "error":
                        err = data.get("error", {})
                        logger.error(f"D-ID clip failed: {data}")
                        return None, f"D-ID clip error: {err}"
            except Exception as e:
                logger.error(f"D-ID poll: {e}")
                return None, f"D-ID poll: {e}"
            await asyncio.sleep(POLL_INTERVAL)
    logger.error(f"D-ID poll timeout for {clip_id}")
    return None, f"D-ID timeout after {POLL_TIMEOUT}s"


async def _download(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                return await resp.read()
        except Exception as e:
            logger.error(f"D-ID download: {e}")
            return b""


def _crop_square(video_bytes: bytes) -> bytes:
    """Crop video to 1:1 aspect ratio for Telegram video_note."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(video_bytes)
            in_path = f.name
        out_path = in_path.replace(".mp4", "_sq.mp4")
        r = subprocess.run(
            [
                "ffmpeg", "-i", in_path,
                "-vf", "crop=min(iw\\,ih):min(iw\\,ih)",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "64k",
                out_path, "-y", "-loglevel", "error"
            ],
            capture_output=True
        )
        os.unlink(in_path)
        if r.returncode == 0 and os.path.exists(out_path):
            with open(out_path, "rb") as f:
                result = f.read()
            os.unlink(out_path)
            return result
        logger.error(f"ffmpeg crop failed: {r.stderr.decode()}")
        return video_bytes
    except Exception as e:
        logger.error(f"D-ID crop_square: {e}")
        return video_bytes


async def generate_video_note(audio_bytes: bytes, audio_format: str = "mp3") -> tuple[bytes, str]:
    """Full pipeline: audio bytes → D-ID clip → square mp4. Returns (video, error_reason)."""
    if not DID_API_KEY:
        return b"", "DID_API_KEY not set"
    if not DID_PRESENTER_ID:
        return b"", "DID_PRESENTER_ID not set"

    clip_id, err = await _create_clip(audio_bytes, audio_format)
    if not clip_id:
        return b"", err

    result_url, err = await _poll_clip(clip_id)
    if not result_url:
        return b"", err

    video_bytes = await _download(result_url)
    if not video_bytes:
        return b"", "Failed to download video from D-ID"

    return _crop_square(video_bytes), ""
