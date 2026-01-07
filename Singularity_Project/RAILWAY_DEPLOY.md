# NEXUS 10 AI AGENCY - Railway Deployment Guide

## Quick Deploy

1. **Connect Repository**
   - Go to [railway.app](https://railway.app)
   - New Project → Deploy from GitHub
   - Select your `Singularity_Project` repository

2. **Set Environment Variables**
   Railway Dashboard → Variables → Add:

## Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather | ✅ YES |
| `OPENAI_API_KEY` | OpenAI API key (sk-proj-...) | ✅ YES |
| `POLYGONSCAN_API_KEY` | Polygonscan API key for crypto monitoring | ✅ YES |
| `MY_CRYPTO_WALLET` | Your Polygon wallet address | ✅ YES |

## Payment Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `STRIPE_PAYMENT_LINK` | Stripe payment link URL | `https://buy.stripe.com/...` |
| `STRIPE_SECRET_KEY` | Stripe secret key (for webhooks) | `sk_live_...` |
| `WISE_TAG` | Wise.com payment tag | `advancedmedicinalconsultingltd` |

## Bank Transfer Details

| Variable | Value |
|----------|-------|
| `BANK_NAME` | `Wise` |
| `BANK_HOLDER` | `Advanced Medicinal Consulting Ltd` |
| `BANK_IBAN` | `BE29 9055 1684 1164` |
| `BANK_SWIFT` | `TRWIBEB1XXX` |
| `BANK_ADDRESS` | `Rue du Trône 100, 3rd floor, Brussels, 1050, Belgium` |

## Optional (Backup)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY_BACKUP` | Backup OpenAI key |
| `SERPER_API_KEY` | Google search API (for Hunter) |
| `ADMIN_CHAT_ID` | Your Telegram chat ID for notifications |

## Copy-Paste Template

```env
# === REQUIRED ===
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=sk-proj-your_key_here
POLYGONSCAN_API_KEY=your_polygonscan_key
MY_CRYPTO_WALLET=0xf244499abff0e7c6939f470de0914fc1c848f308

# === PAYMENTS ===
STRIPE_PAYMENT_LINK=https://buy.stripe.com/your_link
WISE_TAG=advancedmedicinalconsultingltd

# === BANK DETAILS ===
BANK_NAME=Wise
BANK_HOLDER=Advanced Medicinal Consulting Ltd
BANK_IBAN=BE29 9055 1684 1164
BANK_SWIFT=TRWIBEB1XXX
BANK_ADDRESS=Rue du Trône 100, 3rd floor, Brussels, 1050, Belgium

# === OPTIONAL ===
ADMIN_CHAT_ID=
SERPER_API_KEY=
```

## Deployment Checklist

- [ ] Repository connected to Railway
- [ ] All required environment variables set
- [ ] `Procfile` exists: `web: python bot.py`
- [ ] `runtime.txt` exists: `python-3.11.6`
- [ ] `requirements.txt` up to date

## Post-Deploy Verification

After deployment:

1. Open Telegram
2. Send `/start` to your bot
3. Send `/health` to check system status
4. Send `/profitreport` to verify database connection

## Monitoring

Railway provides:
- Automatic restarts on crash
- Logs in dashboard
- Resource monitoring

## Telegram Commands After Deploy

| Command | Description |
|---------|-------------|
| `/start` | Main menu |
| `/health` | System status |
| `/profitreport` | Profit metrics |
| `/pipeline` | Active projects |
| `/start_monitor` | Start blockchain watch |

## Important Notes

1. **Single Instance**: Railway runs one instance. The bot handles conflicts automatically.

2. **Database**: SQLite database (`nexus_business.db`) persists in Railway volume.

3. **Crypto Monitoring**: `blockchain_eye.py` checks every 5 minutes automatically.

4. **Legal Documents**: Generated in `/legal_documents/` directory.

5. **Invoices**: Generated in `/invoices/` directory.

---

**System Version:** Nexus 10 AI Agency v10.0
**Autonomy Score:** 10/10
**Status:** Production Ready







