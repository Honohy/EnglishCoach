# 🤖 English Practice Bot

Telegram-бот для практики английского (B1-B2) с системой ИИ-агентов.

## 🏗 Архитектура агентов

```
User (text/voice/circle)
         │
         ▼
┌─────────────────┐
│  ORCHESTRATOR   │  ← определяет намерение пользователя
└────────┬────────┘
         │
    ┌────┴────────────────┐
    │                     │
┌───▼──────┐    ┌─────────▼──────┐
│ CONV.    │    │ GRAMMAR AGENT  │
│ AGENT    │    │ (ошибки)       │
│ (диалог) │    └────────────────┘
└───┬──────┘
    │
┌───▼──────────────┐
│ FEEDBACK AGENT   │
│ (прогресс/stats) │
└──────────────────┘
```

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных
```bash
cp .env.example .env
# Откройте .env и заполните токены
```

**Нужные API ключи:**
- `BOT_TOKEN` — от [@BotFather](https://t.me/BotFather) в Telegram
- `ANTHROPIC_API_KEY` — с [console.anthropic.com](https://console.anthropic.com)
- `OPENAI_API_KEY` — с [platform.openai.com](https://platform.openai.com) (для Whisper + TTS)

### 3. Запуск
```bash
python bot.py
```

### 4. Деплой на Railway (рекомендую)
```bash
# Установите Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
# Добавьте переменные через railway variables
```

## 📁 Структура проекта
```
english_bot/
├── bot.py                    # Точка входа
├── config.py                 # Конфигурация
├── requirements.txt
├── .env.example
├── agents/
│   ├── orchestrator.py       # 🧠 Главный агент-маршрутизатор
│   ├── conversation_agent.py # 💬 Агент разговорной практики
│   ├── grammar_agent.py      # 📝 Агент проверки грамматики
│   └── feedback_agent.py     # 📊 Агент обратной связи
├── handlers/
│   ├── command_handler.py    # /start, /help, /progress
│   ├── voice_handler.py      # Голос + кружочки
│   └── message_handler.py   # Текстовые сообщения
├── services/
│   ├── voice_service.py      # STT (Whisper) + TTS (OpenAI)
│   └── session_service.py    # История + профиль пользователя
└── models/
    └── database.py           # SQLite модели
```

## 🎯 Функции бота

| Функция | Описание |
|---|---|
| 🎤 Голосовые сообщения | Whisper транскрибирует → Claude отвечает → TTS озвучивает |
| ⭕ Кружочки (video note) | Аналогично голосовым |
| 💬 Текстовый чат | Разговорная практика с агентом Alex |
| 📝 Коррекция грамматики | Фоновая проверка без прерывания диалога |
| 📊 Прогресс | `/progress` — анализ сессии и советы |
| 🔄 Новая тема | Случайная тема для разговора |

## ⚙️ Настройка голоса TTS

В `config.py` можно сменить голос:
```python
TTS_VOICE = "nova"    # nova, alloy, echo, fable, onyx, shimmer
```

## 💰 Примерные расходы (на 1000 сообщений/день)
- Claude Sonnet: ~$2-4/день
- OpenAI Whisper: ~$0.5/день  
- OpenAI TTS: ~$1-2/день
- **Итого: ~$3-7/день**
