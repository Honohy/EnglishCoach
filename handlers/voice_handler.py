"""
VOICE HANDLER
Handles voice messages and video notes (circles) from Telegram.
Flow: receive audio → STT → process with agents → TTS → send voice back
"""
import logging
from aiogram import Router, Bot
from aiogram.types import Message, BufferedInputFile

from services.voice_service import speech_to_text, text_to_voice_note
from services.session_service import get_history, add_voice_message, save_grammar_error, get_or_create_user
from agents.orchestrator import orchestrate
from agents.conversation_agent import get_conversation_response
from agents.grammar_agent import check_grammar, format_grammar_feedback

logger = logging.getLogger(__name__)
router = Router()


async def process_audio_message(message: Message, bot: Bot, file_format: str = "ogg"):
    """Common handler for voice and video notes."""
    user_id = message.from_user.id
    await get_or_create_user(user_id, message.from_user.username)

    # Show typing indicator
    await bot.send_chat_action(message.chat.id, "record_voice")

    # Download audio file
    if message.voice:
        file = await bot.get_file(message.voice.file_id)
    else:
        file = await bot.get_file(message.video_note.file_id)
        file_format = "mp4"

    file_bytes = await bot.download_file(file.file_path)
    audio_bytes = file_bytes.read()

    # Speech to Text
    transcribed_text = await speech_to_text(audio_bytes, file_format)

    if not transcribed_text:
        await message.answer(
            "🤔 Sorry, I couldn't hear that clearly. Could you try again?",
        )
        return

    # Show what was understood
    await message.answer(f"🎙 *I heard:* _{transcribed_text}_", parse_mode="Markdown")

    # Save user message to history
    await add_voice_message(user_id, "user", transcribed_text)
    history = await get_history(user_id)

    # Orchestrate: decide what to do
    intent_data = await orchestrate(transcribed_text, history[:-1], prefer_voice=True)

    # Get conversational response
    await bot.send_chat_action(message.chat.id, "record_voice")
    response_text = await get_conversation_response(
        user_message=transcribed_text,
        history=history[:-1],
        topic=intent_data.get("topic", "general")
    )

    # Save assistant response
    await add_voice_message(user_id, "assistant", response_text)

    # Send voice response
    await bot.send_chat_action(message.chat.id, "upload_voice")
    audio_response = await text_to_voice_note(response_text)

    if audio_response:
        audio_input = BufferedInputFile(audio_response, filename="response.ogg")
        await message.answer_voice(audio_input, caption=f"_{response_text}_", parse_mode="Markdown")
    else:
        # Fallback to text if TTS fails
        await message.answer(f"🗣 {response_text}")

    # Background grammar check (send as separate message if errors found)
    if intent_data.get("needs_correction"):
        grammar_data = await check_grammar(transcribed_text)
        if grammar_data.get("has_errors"):
            feedback = format_grammar_feedback(grammar_data)
            await message.answer(feedback, parse_mode="Markdown")

            # Save errors to DB for progress tracking
            for err in grammar_data.get("errors", []):
                await save_grammar_error(
                    telegram_id=user_id,
                    original=err["original"],
                    corrected=err["corrected"],
                    explanation=err["explanation"],
                    error_type=err["type"]
                )


@router.message(lambda m: m.voice is not None)
async def handle_voice(message: Message, bot: Bot):
    await process_audio_message(message, bot, file_format="ogg")


@router.message(lambda m: m.video_note is not None)
async def handle_video_note(message: Message, bot: Bot):
    await process_audio_message(message, bot, file_format="mp4")
