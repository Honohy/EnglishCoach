from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime

engine = create_async_engine("sqlite+aiosqlite:///english_bot.db", echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class UserProfile(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    level = Column(String, default="B1")
    total_messages = Column(Integer, default=0)
    total_voice = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_active = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversationHistory(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, index=True)
    role = Column(String)          # "user" or "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class GrammarError(Base):
    __tablename__ = "grammar_errors"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, index=True)
    original = Column(Text)
    corrected = Column(Text)
    explanation = Column(Text)
    error_type = Column(String)    # tense, article, preposition, etc.
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
