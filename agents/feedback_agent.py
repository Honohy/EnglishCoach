"""
FEEDBACK AGENT
Analyzes session history, tracks progress, gives motivational summary.
"""
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

FEEDBACK_SYSTEM = """You are a supportive English learning coach.
Analyze the provided conversation history and grammar error data.
Give a brief, motivational session summary in Russian with English examples.

Structure your response:
1. 🎯 What went well (2-3 specific observations)
2. 📈 One key area to improve (be specific, give example)
3. 💡 One tip or mini-lesson for next time
4. 🔥 Encouraging closing line

Keep it under 200 words. Use emojis. Be warm and specific, not generic."""


async def get_session_feedback(
    history: list[dict],
    error_types: list[str],
    total_messages: int,
    total_voice: int
) -> str:
    """Generate personalized session feedback."""

    context = f"""
Session stats:
- Messages exchanged: {total_messages}
- Voice messages: {total_voice}
- Common error types: {', '.join(error_types) if error_types else 'none detected'}

Conversation history (last 10 messages):
{_format_history(history[-10:])}
"""

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        system=FEEDBACK_SYSTEM,
        messages=[{"role": "user", "content": context}],
    )

    return response.content[0].text.strip()


def _format_history(history: list[dict]) -> str:
    lines = []
    for msg in history:
        role = "User" if msg["role"] == "user" else "Bot"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)
