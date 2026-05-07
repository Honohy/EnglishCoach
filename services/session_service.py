"""
USER SESSION SERVICE
Manages conversation history, user profiles, and grammar error tracking.
"""
import logging
from datetime import datetime
from sqlalchemy import select, desc
from models.database import AsyncSessionLocal, UserProfile, ConversationHistory, GrammarError

logger = logging.getLogger(__name__)

# In-memory cache for active conversations (last N messages per user)
_conversation_cache: dict[int, list[dict]] = {}
MAX_HISTORY = 20


async def get_or_create_user(telegram_id: int, username: str = None) -> UserProfile:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = UserProfile(
                telegram_id=telegram_id,
                username=username,
                level="B1"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"New user created: {telegram_id}")

        return user


async def add_message(telegram_id: int, role: str, content: str):
    """Add message to history (DB + in-memory cache)."""
    # Update in-memory cache
    if telegram_id not in _conversation_cache:
        _conversation_cache[telegram_id] = []

    _conversation_cache[telegram_id].append({"role": role, "content": content})

    # Keep only last MAX_HISTORY messages in memory
    if len(_conversation_cache[telegram_id]) > MAX_HISTORY:
        _conversation_cache[telegram_id] = _conversation_cache[telegram_id][-MAX_HISTORY:]

    # Persist to DB
    async with AsyncSessionLocal() as session:
        msg = ConversationHistory(
            telegram_id=telegram_id,
            role=role,
            content=content
        )
        session.add(msg)

        # Update user stats
        if role == "user":
            result = await session.execute(
                select(UserProfile).where(UserProfile.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.total_messages += 1
                user.last_active = datetime.utcnow()

        await session.commit()


async def add_voice_message(telegram_id: int, role: str, content: str):
    """Same as add_message but increments voice counter."""
    await add_message(telegram_id, role, content)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user and role == "user":
            user.total_voice += 1
            await session.commit()


async def get_history(telegram_id: int) -> list[dict]:
    """Get conversation history (from cache or DB)."""
    if telegram_id in _conversation_cache:
        return _conversation_cache[telegram_id]

    # Load from DB if not in cache
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ConversationHistory)
            .where(ConversationHistory.telegram_id == telegram_id)
            .order_by(desc(ConversationHistory.created_at))
            .limit(MAX_HISTORY)
        )
        messages = result.scalars().all()
        history = [{"role": m.role, "content": m.content} for m in reversed(messages)]
        _conversation_cache[telegram_id] = history
        return history


async def save_grammar_error(telegram_id: int, original: str, corrected: str,
                              explanation: str, error_type: str):
    async with AsyncSessionLocal() as session:
        error = GrammarError(
            telegram_id=telegram_id,
            original=original,
            corrected=corrected,
            explanation=explanation,
            error_type=error_type
        )
        session.add(error)
        await session.commit()


async def get_recent_error_types(telegram_id: int, limit: int = 10) -> list[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GrammarError.error_type)
            .where(GrammarError.telegram_id == telegram_id)
            .order_by(desc(GrammarError.created_at))
            .limit(limit)
        )
        return [row[0] for row in result.all()]


async def get_user_stats(telegram_id: int) -> dict:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return {}
        return {
            "total_messages": user.total_messages,
            "total_voice": user.total_voice,
            "level": user.level,
            "streak_days": user.streak_days,
        }


async def clear_history(telegram_id: int):
    """Clear conversation history for a fresh start."""
    _conversation_cache[telegram_id] = []
