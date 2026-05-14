import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # for Whisper STT + TTS
DID_API_KEY = os.getenv("DID_API_KEY", "")
DID_AVATAR_URL = os.getenv("DID_AVATAR_URL", "")  # public image URL for /talks
DID_PRESENTER_ID = os.getenv("DID_PRESENTER_ID", "")  # for /clips (unused now)
DID_DRIVER_ID = os.getenv("DID_DRIVER_ID", "")  # optional

# Voice settings
TTS_VOICE = "nova"          # OpenAI TTS voice: alloy, echo, fable, onyx, nova, shimmer
TTS_MODEL = "tts-1"
STT_MODEL = "whisper-1"

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# User level (B1-B2 focused)
DEFAULT_LEVEL = "B1"
