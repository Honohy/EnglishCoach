"""
MESSAGE HANDLER
Handles regular text messages.
Routes through orchestrator → appropriate agent → responds.
"""
import logging
from aiogram import Router
from aiogram.types import Message

from services.session_service import get_history, add_message, save_grammar_error, get_or_create_user
from agents.orchestrator import orchestrate
from agents.conversation_agent import get_conversation_response
from agents.grammar_agent import check_grammar, format_grammar_feedback

logger = logging.getLogger(__name__)
router = Router()

# Skip keyboard button texts that are handled by command_handler
SKIP_TEXTS = {"🗣 practice english", "📊 my progress", "🔄 new topic", "❓ help"}


@router.message(lambda m: m.text and m.text.lower() not in SKIP_TEXTS and not m.text.startswith("/"))
async def handle_text_message(message: Message):
    user_id = message.from_user.id
    user_text = message.text.strip()

    await get_or_create_user(user_id, message.from_user.username)

    # Show typing
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Save user message
    await add_message(user_id, "user", user_text)
    history = await get_history(user_id)

    # Orchestrate intent
    intent_data = await orchestrate(user_text, history[:-1], prefer_voice=False)
    intent = intent_data.get("intent", "conversation")

    if intent == "grammar_check":
        # Explicit grammar check requested
        grammar_data = await check_grammar(user_text)
        feedback = format_grammar_feedback(grammar_data)
        await message.answer(feedback, parse_mode="Markdown")

        if grammar_data.get("has_errors"):
            for err in grammar_data.get("errors", []):
                await save_grammar_error(
                    telegram_id=user_id,
                    original=err["original"],
                    corrected=err["corrected"],
                    explanation=err["explanation"],
                    error_type=err["type"]
                )

        # Still continue conversation
        response = await get_conversation_response(
            user_message=user_text,
            history=history[:-1],
            topic=intent_data.get("topic", "general")
        )
        await add_message(user_id, "assistant", response)
        await message.answer(f"💬 {response}")

    else:
        # Default: conversation
        response = await get_conversation_response(
            user_message=user_text,
            history=history[:-1],
            topic=intent_data.get("topic", "general")
        )
        await add_message(user_id, "assistant", response)
        await message.answer(response)

        # Subtle background grammar check (only if errors likely)
        if intent_data.get("needs_correction"):
            grammar_data = await check_grammar(user_text)
            if grammar_data.get("has_errors") and grammar_data.get("errors"):
                # Only show if there are real errors
                await message.answer(
                    format_grammar_feedback(grammar_data),
                    parse_mode="Markdown"
                )
                for err in grammar_data.get("errors", []):
                    await save_grammar_error(
                        telegram_id=user_id,
                        original=err["original"],
                        corrected=err["corrected"],
                        explanation=err["explanation"],
                        error_type=err["type"]
                    )
