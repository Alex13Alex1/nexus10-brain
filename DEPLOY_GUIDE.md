# 🚀 NEXUS 10 AI AGENCY - ПОЛНОЕ РУКОВОДСТВО ПО ДЕПЛОЮ

## 📋 СОСТАВ СИСТЕМЫ

| Компонент | Описание | Деплой |
|-----------|----------|--------|
| **Telegram Bot** | Основной бот агентства | Railway ✅ |
| **Streamlit UI** | Mobile Command Center | Railway (новый сервис) |
| **React Frontend** | Web Dashboard | Vercel |
| **Backend API** | FastAPI сервер | Railway (опционально) |

---

## 🔧 ЧАСТЬ 1: ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ RAILWAY

### Добавьте в Railway → Variables:

```env
# === CORE ===
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# === PAYMENTS: CRYPTO ===
POLYGONSCAN_API_KEY=YOUR_POLYGONSCAN_KEY
MY_CRYPTO_WALLET=0xYOUR_WALLET_ADDRESS

# === PAYMENTS: FIAT ===
STRIPE_PAYMENT_LINK=https://buy.stripe.com/YOUR_LINK
WISE_TAG=your_wise_username

# === BANK (SEPA/SWIFT) ===
BANK_NAME=Wise
BANK_IBAN=YOUR_IBAN
BANK_SWIFT=YOUR_SWIFT
BANK_HOLDER=Your Company Name
BANK_ADDRESS=Your Address

# === ECONOMICS ===
MIN_ORDER_AMOUNT=50
MIN_MARGIN_PERCENT=20
```

---

## 📱 ЧАСТЬ 2: ДЕПЛОЙ STREAMLIT UI НА RAILWAY

### Шаг 1: Создайте новый сервис
1. Откройте https://railway.com
2. В проекте `agile-magic` нажмите **"+ New"** → **"GitHub Repo"**
3. Выберите репозиторий `singularity-core`
4. В настройках укажите:
   - **Root Directory:** `streamlit_app`
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.headless=true`

### Шаг 2: Переменные
Добавьте те же переменные что и для основного бота (OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, etc.)

### Шаг 3: Дождитесь деплоя
После успешного деплоя вы получите URL типа:
`https://streamlit-production-xxxx.up.railway.app`

---

## 🌐 ЧАСТЬ 3: ДЕПЛОЙ REACT FRONTEND НА VERCEL

### Шаг 1: Установите Vercel CLI
```bash
npm install -g vercel
```

### Шаг 2: Деплой
```bash
cd Singularity_Project/frontend
vercel
```

### Шаг 3: Настройте переменные
В Vercel Dashboard добавьте:
```
VITE_API_URL=https://your-railway-api.up.railway.app
```

### Альтернатива: Через GitHub
1. Откройте https://vercel.com
2. **"Add New" → "Project"**
3. Выберите репозиторий
4. **Root Directory:** `Singularity_Project/frontend`
5. **Framework Preset:** Vite
6. Deploy!

---

## 🔌 ЧАСТЬ 4: ПОЛУЧЕНИЕ API КЛЮЧЕЙ

### OpenAI API Key
1. Перейдите на https://platform.openai.com
2. Settings → API Keys → Create new secret key

### Telegram Bot Token
1. Откройте @BotFather в Telegram
2. `/newbot` или `/mybots` → выберите бота → API Token

### Polygonscan API Key
1. https://polygonscan.com → Sign up
2. API Keys → Add → Copy

### Stripe Payment Link
1. https://dashboard.stripe.com
2. Products → Payment Links → Create

### Wise Tag
1. Откройте Wise
2. Profile → @username (из pay.me ссылки)

---

## ✅ ЧЕКЛИСТ ДЕПЛОЯ

- [ ] Telegram Bot на Railway работает
- [ ] Все переменные добавлены в Railway
- [ ] Streamlit UI развёрнут
- [ ] React Frontend на Vercel
- [ ] Платёжные системы настроены
- [ ] Тест бота через Telegram
- [ ] Тест UI через браузер

---

## 🎯 БЫСТРЫЙ СТАРТ

### Локальный запуск
```bash
# Telegram Bot
cd Singularity_Project
python bot.py

# Streamlit UI
cd streamlit_app
streamlit run app.py

# React Frontend
cd Singularity_Project/frontend
npm install
npm run dev
```

### Продакшен URLs
- **Bot:** Telegram @your_bot_name
- **UI:** https://streamlit-xxx.railway.app
- **Web:** https://nexus10.vercel.app

---

## 🆘 TROUBLESHOOTING

### Bot 401 Unauthorized
- Проверьте токен в @BotFather
- Пересоздайте токен если нужно
- Обновите TELEGRAM_BOT_TOKEN в Railway

### Streamlit не запускается
- Проверьте Procfile
- Убедитесь что PORT используется из окружения

### React build fails
- `npm install` перед билдом
- Проверьте node version (18+)

---

**NEXUS 10 AI AGENCY** | Full Deployment Guide v1.0

