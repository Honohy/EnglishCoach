"""
ORCHESTRATOR AGENT
Analyzes user intent and routes to the appropriate specialized agent.
"""
import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

ORCHESTRATOR_SYSTEM = """You are an orchestrator for an English learning bot.
Analyze the user's message and conversation history, then decide which agent should handle it.

Return ONLY valid JSON with this structure:
{
  "intent": "conversation" | "grammar_check" | "vocabulary" | "feedback",
  "topic": "brief topic description",
  "needs_correction": true | false,
  "response_format": "voice" | "text"
}

Rules:
- "conversation": user wants to chat / practice speaking
- "grammar_check": user explicitly asks to check grammar
- "vocabulary": user asks about word meaning / usage
- "feedback": user asks for progress / session summary
- needs_correction: true if the message has obvious grammar errors
- response_format: "voice" for casual conversation, "text" for explanations"""


async def orchestrate(user_message: str, history: list[dict], prefer_voice: bool = False) -> dict:
    """Analyze intent and route to correct agent."""
    messages = history[-6:] + [{"role": "user", "content": user_message}]

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=200,
        system=ORCHESTRATOR_SYSTEM,
        messages=messages,
    )

    raw = response.content[0].text.strip()
    try:
        result = json.loads(raw)
    except Exception:
        result = {
            "intent": "conversation",
            "topic": "general",
            "needs_correction": False,
            "response_format": "voice" if prefer_voice else "text"
        }

    if prefer_voice:
        result["response_format"] = "voice"

    return result
