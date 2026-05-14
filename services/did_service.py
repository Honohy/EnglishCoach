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

from config import DID_API_KEY, DID_PRESENTER_ID, DID_DRIVER_ID, DID_AVATAR_URL

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


async def _upload_audio(audio_bytes: bytes, audio_format: str = "mp3") -> tuple[str, str]:
    """Upload audio to D-ID, returns (audio_url, error)."""
    mime = "audio/mpeg" if audio_format == "mp3" else f"audio/{audio_format}"
    form = aiohttp.FormData()
    form.add_field("audio", audio_bytes, filename=f"audio.{audio_format}", content_type=mime)
    headers = _auth_headers(with_content_type=False)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{DID_BASE}/audios", data=form, headers=headers) as resp:
                body = await resp.text()
                logger.info(f"D-ID /audios upload {resp.status}: {body}")
                if resp.status not in (200, 201):
                    return "", f"D-ID audio upload {resp.status}: {body}"
                import json as _json
                return _json.loads(body).get("url", ""), ""
        except Exception as e:
            logger.error(f"D-ID upload_audio: {e}")
            return "", f"D-ID upload_audio: {e}"


async def _create_talk(audio_url: str) -> tuple[str | None, str]:
    source_url = DID_AVATAR_URL or "https://clips-presenters.d-id.com/v2/amber/Y5K02DLS4m/9o3E6z8MPD/image.png"
    payload = {
        "source_url": source_url,
        "script": {"type": "audio", "audio_url": audio_url},
        "config": {"result_format": "mp4"}
    }
    logger.info(f"D-ID /talks request: source_url={source_url}, audio_url={audio_url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{DID_BASE}/talks", json=payload, headers=_auth_headers()
            ) as resp:
                body = await resp.text()
                logger.info(f"D-ID /talks response {resp.status}: {body}")
                if resp.status not in (200, 201):
                    return None, f"D-ID {resp.status}: {body}"
                import json as _json
                return _json.loads(body).get("id"), ""
        except Exception as e:
            logger.error(f"D-ID create_talk: {e}")
            return None, f"D-ID create_talk: {e}"


async def _poll_talk(talk_id: str) -> tuple[str | None, str]:
    deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT
    async with aiohttp.ClientSession() as session:
        while asyncio.get_event_loop().time() < deadline:
            try:
                async with session.get(
                    f"{DID_BASE}/talks/{talk_id}",
                    headers=_auth_headers(with_content_type=False)
                ) as resp:
                    body = await resp.text()
                    import json as _json
                    data = _json.loads(body)
                    status = data.get("status")
                    if status == "done":
                        return data.get("result_url"), ""
                    if status == "error":
                        logger.error(f"D-ID talk failed: {data}")
                        return None, f"D-ID talk error: {data.get('error', data)}"
                    logger.info(f"D-ID poll status: {status}")
            except Exception as e:
                logger.error(f"D-ID poll: {e}")
                return None, f"D-ID poll: {e}"
            await asyncio.sleep(POLL_INTERVAL)
    logger.error(f"D-ID poll timeout for {talk_id}")
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
    """Full pipeline: audio bytes → D-ID /talks → square mp4. Returns (video, error_reason)."""
    if not DID_API_KEY:
        return b"", "DID_API_KEY not set"

    audio_url, err = await _upload_audio(audio_bytes, audio_format)
    if not audio_url:
        return b"", err

    talk_id, err = await _create_talk(audio_url)
    if not talk_id:
        return b"", err

    result_url, err = await _poll_talk(talk_id)
    if not result_url:
        return b"", err

    video_bytes = await _download(result_url)
    if not video_bytes:
        return b"", "Failed to download video from D-ID"

    return _crop_square(video_bytes), ""
