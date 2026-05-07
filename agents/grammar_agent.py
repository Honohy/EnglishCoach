"""
GRAMMAR AGENT
Analyzes user messages for grammar errors and provides clear explanations.
Returns structured correction data.
"""
import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

GRAMMAR_SYSTEM = """You are an expert English grammar teacher for B1-B2 level Russian speakers.
Analyze the given text for grammar errors.

Return ONLY valid JSON:
{
  "has_errors": true | false,
  "errors": [
    {
      "original": "the wrong part",
      "corrected": "the correct form",
      "explanation": "short, clear explanation in Russian",
      "type": "tense | article | preposition | word_order | subject_verb | other"
    }
  ],
  "corrected_sentence": "full corrected version of the sentence",
  "positive_note": "one sentence encouraging the user in Russian"
}

Focus on:
- Verb tenses (especially Past Simple vs Present Perfect)
- Articles (a/an/the)
- Prepositions
- Word order
- Subject-verb agreement

Keep explanations concise and practical."""


async def check_grammar(text: str) -> dict:
    """Check grammar and return structured error analysis."""
    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        system=GRAMMAR_SYSTEM,
        messages=[{"role": "user", "content": f"Check this text: {text}"}],
    )

    raw = response.content[0].text.strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"has_errors": False, "errors": [], "corrected_sentence": text, "positive_note": "Отлично!"}


def format_grammar_feedback(grammar_data: dict) -> str:
    """Format grammar check results into a readable message."""
    if not grammar_data.get("has_errors") or not grammar_data.get("errors"):
        return f"✅ {grammar_data.get('positive_note', 'Great job! No errors found.')}"

    lines = ["📝 *Grammar Check:*\n"]

    for err in grammar_data["errors"]:
        lines.append(f"❌ ~~{err['original']}~~ → ✅ `{err['corrected']}`")
        lines.append(f"   _{err['explanation']}_\n")

    if grammar_data.get("corrected_sentence"):
        lines.append(f"📖 *Full correction:* _{grammar_data['corrected_sentence']}_\n")

    lines.append(f"💪 {grammar_data.get('positive_note', '')}")

    return "\n".join(lines)
