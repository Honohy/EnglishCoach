"""
CONVERSATION AGENT
Handles natural English conversation practice for B1-B2 level users.
Speaks naturally, keeps the dialogue flowing, subtly corrects errors.
"""
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

CONVERSATION_SYSTEM = """You are Alex, a friendly American English conversation partner helping a Russian-speaking student at B1-B2 level practice English.

Your personality:
- Warm, encouraging, patient
- Use natural conversational English (contractions, phrasal verbs)
- Ask follow-up questions to keep conversation going
- Match the user's energy and topic interest

Language rules:
- Always respond in English
- Keep responses 2-4 sentences for voice messages, up to 6 for text
- If the user makes a grammar mistake, naturally model the correct form in your reply WITHOUT explicitly pointing it out
  Example: User says "I goed to shop" → You reply: "Oh nice, you went shopping! What did you buy?"
- Occasionally introduce B1-B2 vocabulary in context
- End with a question to encourage response

Topics you love: travel, food, movies, daily life, work, hobbies, technology, culture."""


async def get_conversation_response(
    user_message: str,
    history: list[dict],
    topic: str = "general"
) -> str:
    """Generate a natural conversational response."""

    messages = history[-10:] + [{"role": "user", "content": user_message}]

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=300,
        system=CONVERSATION_SYSTEM,
        messages=messages,
    )

    return response.content[0].text.strip()
