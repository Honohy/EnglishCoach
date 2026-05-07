from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from services.session_service import get_or_create_user, get_user_stats, clear_history
from agents.feedback_agent import get_session_feedback
from services.session_service import get_history, get_recent_error_types

router = Router()

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🗣 Practice English"), KeyboardButton(text="📊 My Progress")],
        [KeyboardButton(text="🔄 New Topic"), KeyboardButton(text="❓ Help")],
    ],
    resize_keyboard=True
)


@router.message(Command("start"))
async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)

    await message.answer(
        f"👋 Hey! I'm *Alex*, your English conversation partner!\n\n"
        f"I'm here to help you practice English at *B1-B2 level*.\n\n"
        f"Here's what I can do:\n"
        f"🎤 *Voice & Circle messages* — just send me a voice note!\n"
        f"💬 *Text chat* — type anything in English\n"
        f"📝 *Grammar tips* — I'll gently correct your mistakes\n"
        f"📊 *Progress tracking* — see how you're improving\n\n"
        f"*Ready? Say something in English!* 🚀",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD
    )


@router.message(Command("help"))
@router.message(lambda m: m.text == "❓ Help")
async def cmd_help(message: Message):
    await message.answer(
        "📖 *How to use me:*\n\n"
        "🎤 Send a *voice message* — I'll reply with voice too!\n"
        "⭕ Send a *video note (circle)* — same thing!\n"
        "💬 *Type* anything in English and I'll respond\n\n"
        "*Commands:*\n"
        "/start — restart the bot\n"
        "/progress — see your stats & feedback\n"
        "/new — start a new topic\n"
        "/check [text] — check grammar explicitly\n\n"
        "💡 *Tip:* I'll naturally correct your grammar without interrupting the flow!",
        parse_mode="Markdown"
    )


@router.message(Command("new"))
@router.message(lambda m: m.text == "🔄 New Topic")
async def cmd_new_topic(message: Message):
    await clear_history(message.from_user.id)
    topics = [
        "your favorite travel destination 🌍",
        "a movie you watched recently 🎬",
        "your typical morning routine ☀️",
        "something you want to learn 📚",
        "your favorite food 🍕",
        "technology and gadgets 💻",
        "your weekend plans 🎉"
    ]
    import random
    topic = random.choice(topics)
    await message.answer(
        f"🔄 *Fresh start!* Let's talk about *{topic}*\n\n"
        f"Tell me — what's your take on it?",
        parse_mode="Markdown"
    )


@router.message(Command("progress"))
@router.message(lambda m: m.text == "📊 My Progress")
async def cmd_progress(message: Message):
    await message.answer("📊 Analyzing your session... one sec!")

    history = await get_history(message.from_user.id)
    error_types = await get_recent_error_types(message.from_user.id)
    stats = await get_user_stats(message.from_user.id)

    if not history or len(history) < 2:
        await message.answer(
            "💬 We haven't talked much yet!\n"
            "Send me a few messages in English first, then I'll give you detailed feedback.",
            parse_mode="Markdown"
        )
        return

    feedback = await get_session_feedback(
        history=history,
        error_types=error_types,
        total_messages=stats.get("total_messages", 0),
        total_voice=stats.get("total_voice", 0)
    )

    stats_text = (
        f"📈 *Your Stats:*\n"
        f"• Messages: {stats.get('total_messages', 0)}\n"
        f"• Voice messages: {stats.get('total_voice', 0)}\n"
        f"• Level: {stats.get('level', 'B1')}\n\n"
    )

    await message.answer(stats_text + feedback, parse_mode="Markdown")


@router.message(Command("check"))
async def cmd_check_grammar(message: Message):
    text_to_check = message.text.replace("/check", "").strip()
    if not text_to_check:
        await message.answer("Usage: `/check Your sentence here`", parse_mode="Markdown")
        return

    from agents.grammar_agent import check_grammar, format_grammar_feedback
    grammar_data = await check_grammar(text_to_check)
    feedback = format_grammar_feedback(grammar_data)
    await message.answer(feedback, parse_mode="Markdown")
