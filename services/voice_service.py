"""
VOICE SERVICE
Speech-to-Text (Whisper) and Text-to-Speech (OpenAI TTS).
Handles voice notes and video notes (circles) in Telegram.
"""
import io
import logging
import tempfile
import os
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, TTS_VOICE, TTS_MODEL, STT_MODEL

logger = logging.getLogger(__name__)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def speech_to_text(audio_bytes: bytes, file_format: str = "ogg") -> str:
    """
    Transcribe audio to text using OpenAI Whisper.
    Supports ogg (voice messages) and mp4 (video notes / circles).
    """
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"audio.{file_format}"

        transcript = await openai_client.audio.transcriptions.create(
            model=STT_MODEL,
            file=audio_file,
            language="en",  # Expect English input
            response_format="text"
        )
        return transcript.strip()
    except Exception as e:
        logger.error(f"STT error: {e}")
        return ""


async def text_to_speech(text: str) -> bytes:
    """
    Convert text to speech audio bytes (mp3).
    """
    try:
        response = await openai_client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=text,
            response_format="mp3"
        )
        return response.content
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return b""


async def text_to_voice_note(text: str) -> bytes:
    """
    Generate audio optimized for Telegram voice messages (ogg/opus).
    Falls back to mp3 if conversion fails.
    """
    mp3_bytes = await text_to_speech(text)
    if not mp3_bytes:
        return b""

    # Try to convert to ogg/opus for better Telegram compatibility
    try:
        import subprocess
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_file:
            mp3_file.write(mp3_bytes)
            mp3_path = mp3_file.name

        ogg_path = mp3_path.replace(".mp3", ".ogg")
        result = subprocess.run(
            ["ffmpeg", "-i", mp3_path, "-c:a", "libopus", "-b:a", "64k", ogg_path, "-y", "-loglevel", "error"],
            capture_output=True
        )

        if result.returncode == 0 and os.path.exists(ogg_path):
            with open(ogg_path, "rb") as f:
                ogg_bytes = f.read()
            os.unlink(mp3_path)
            os.unlink(ogg_path)
            return ogg_bytes
        else:
            os.unlink(mp3_path)
            return mp3_bytes  # fallback to mp3

    except FileNotFoundError:
        # ffmpeg not installed - return mp3
        return mp3_bytes


async def create_video_note_audio(text: str) -> bytes:
    """
    For sending as video note (circle), we send voice instead.
    Telegram video notes require actual video - we use voice as fallback.
    Returns ogg bytes.
    """
    return await text_to_voice_note(text)
