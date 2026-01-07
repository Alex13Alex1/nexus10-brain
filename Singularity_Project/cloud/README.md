# ☁️ Singularity Cloud v2.0

Автономный AI-рой с интеграцией CrewAI и Telegram ботом для деплоя на Railway.

## 🚀 Быстрый деплой на Railway

### 1. Подготовка

Убедитесь, что у вас есть:
- Аккаунт на [Railway](https://railway.app)
- OpenAI API Key
- Telegram Bot Token (от [@BotFather](https://t.me/BotFather))

### 2. Деплой

1. **Создайте новый проект** на Railway
2. **Подключите GitHub** репозиторий или загрузите папку `cloud/`
3. **Установите Environment Variables:**

```
OPENAI_API_KEY=sk-your-key-here
TELEGRAM_BOT_TOKEN=your-telegram-token-here
```

4. Railway автоматически:
   - Обнаружит Python и установит зависимости из `requirements.txt`
   - Запустит `python main.py` через `Procfile`
   - Выделит порт через переменную `PORT`

### 3. Проверка

После деплоя:
- Откройте URL проекта — увидите красивую страницу статуса
- Откройте `/health` — должен вернуть `{"status": "healthy"}`
- Напишите боту в Telegram — должен ответить

## 📁 Структура файлов

```
cloud/
├── main.py           # Главный файл (FastAPI + Telegram бот)
├── requirements.txt  # Зависимости Python
├── Procfile         # Команда запуска для Railway
├── railway.toml     # Конфигурация Railway
├── env-example.txt  # Пример переменных окружения
└── README.md        # Этот файл
```

## ⚙️ Архитектура

```
┌────────────────────────────────────────────┐
│           Railway Container                │
│                                            │
│  ┌─────────────┐    ┌─────────────────┐   │
│  │   FastAPI   │    │  Telegram Bot   │   │
│  │  (порт :$PORT)│    │   (threading)   │   │
│  └──────┬──────┘    └────────┬────────┘   │
│         │                    │            │
│         └──────────┬─────────┘            │
│                    │                      │
│           ┌────────▼────────┐             │
│           │     CrewAI      │             │
│           │   (AI Agents)   │             │
│           └─────────────────┘             │
└────────────────────────────────────────────┘
```

## 🔧 API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/` | GET | Главная страница со статусом |
| `/health` | GET | Health check для Railway |
| `/status` | GET | JSON статус системы |
| `/launch` | POST | Запуск AI-миссии |
| `/docs` | GET | Swagger документация |

### Пример запроса `/launch`:

```bash
curl -X POST https://your-app.railway.app/launch \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Найди тренды AI в 2026"}'
```

## 🤖 Telegram команды

- `/start` — Приветствие
- `/status` — Статус системы
- `/help` — Помощь

Любое текстовое сообщение запустит AI-анализ.

## 🔐 Environment Variables

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `OPENAI_API_KEY` | ✅ | Ключ OpenAI для CrewAI |
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен бота от BotFather |
| `PORT` | ❌ | Railway устанавливает автоматически |

## ❓ Troubleshooting

### "Application failed to respond"
- Проверьте, что `PORT` используется из `os.environ.get("PORT", 8080)`
- Проверьте логи Railway на наличие ошибок импорта

### Бот не отвечает
- Проверьте `TELEGRAM_BOT_TOKEN` в переменных Railway
- Убедитесь, что нет другого экземпляра бота с тем же токеном

### CrewAI не работает
- Проверьте `OPENAI_API_KEY`
- Проверьте лимиты OpenAI аккаунта

## 📝 Локальный запуск

```bash
cd cloud
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
# Создайте .env файл с переменными
python main.py
```

---

*Singularity v2.0 — Автономный AI-рой в облаке* 🚀
