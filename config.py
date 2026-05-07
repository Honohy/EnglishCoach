import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # for Whisper STT + TTS

# Voice settings
TTS_VOICE = "nova"          # OpenAI TTS voice: alloy, echo, fable, onyx, nova, shimmer
TTS_MODEL = "tts-1"
STT_MODEL = "whisper-1"

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# User level (B1-B2 focused)
DEFAULT_LEVEL = "B1"
