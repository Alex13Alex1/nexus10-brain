# 🧠 NEXUS 10 AI AGENCY

**Autonomous AI Development System**

A multi-agent AI system for autonomous software development and business operations.

---

## 📁 Project Structure

```
brain/
├── main.py                    # 🏭 AI Software Factory (9+ agents)
├── nexus_core/               # 🔧 Core business components
│   ├── pipeline.py           # Business flow orchestration
│   ├── gatekeeper.py         # Profitability analysis
│   ├── blockchain.py         # Crypto payment monitoring
│   ├── invoices.py           # PDF invoice generation
│   ├── notify.py             # Telegram notifications
│   └── database.py           # Unified SQLite operations
│
├── Singularity_Project/      # 🤖 Autonomous Business Bot
│   ├── bot.py                # Telegram bot interface
│   ├── agents.py             # 6 elite AI agents
│   ├── core_engine.py        # Singularity Core v5.5
│   └── ...                   # See Singularity_Project/README
│
├── projects/                 # 📂 Generated project outputs
├── tools.py                  # Custom CrewAI tools
└── requirements.txt          # Dependencies
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/brain.git
cd brain

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in root:

```env
# Required
OPENAI_API_KEY=sk-proj-your-key-here

# Optional - for Singularity Bot
TELEGRAM_BOT_TOKEN=your-telegram-token
POLYGONSCAN_API_KEY=your-polygonscan-key
MY_CRYPTO_WALLET=0x...

# Optional - for payments
STRIPE_PAYMENT_LINK=https://buy.stripe.com/...
BANK_IBAN=BE29 9055 1684 1164
BANK_SWIFT=TRWIBEB1XXX
```

### 3. Run

**Option A: AI Software Factory**
```bash
python main.py
```
→ Generates complete projects with 9 AI agents

**Option B: Singularity Business Bot**
```bash
cd Singularity_Project
python bot.py
```
→ Telegram bot for autonomous freelance business

---

## 🤖 AI Agents

### Main System (`main.py`) - 9 Agents:

| Agent | Role | Model |
|-------|------|-------|
| 👁️ Vision Analyst | Image analysis | GPT-4o |
| 💰 Cost Optimizer | Budget planning | GPT-4o-mini |
| 🔍 Tech Researcher | Best practices | GPT-4o-mini |
| 🏗️ Architect | System design | GPT-4o |
| 🎨 Visualizer | Mermaid diagrams | GPT-4o |
| 🔧 Engineer | Tech stack | GPT-4o |
| 👨‍💻 Developer | Code generation | GPT-4o |
| 🔍 QA Engineer | Testing | GPT-4o-mini |
| 🐳 DevOps | Docker/CI-CD | GPT-4o |
| 🏥 SRE Observer | Monitoring | GPT-4o |

### Singularity (`Singularity_Project/`) - 6 Agents:

| Agent | Role |
|-------|------|
| 🎯 Hunter | Find $500+ contracts |
| 🧠 Architect | Technical planning |
| 💻 Doer | Code implementation |
| ✅ QA Critic | Quality validation |
| 💰 Collector | Invoicing & payments |
| 📈 Strategist | Process optimization |

---

## 📦 NEXUS Core Module

Reusable business components in `nexus_core/`:

```python
# Profitability check
from nexus_core import get_gatekeeper
gk = get_gatekeeper()
result = gk.evaluate(budget=200, complexity="MEDIUM")
print(f"Verdict: {result.verdict.value}, Margin: {result.margin_percent}%")

# Invoice generation
from nexus_core import get_invoice_generator
gen = get_invoice_generator()
pdf = gen.create_pdf("Telegram Bot", 250, client_name="John")

# Blockchain monitoring
from nexus_core import get_blockchain_monitor
eye = get_blockchain_monitor()
eye.start_monitoring()

# Pipeline
from nexus_core import get_pipeline
pipeline = get_pipeline()
project = pipeline.intake("API Development", "REST API", 300)
pipeline.vet(project)
```

---

## 💳 Payment Integration

Supports multiple payment methods:

| Method | Integration |
|--------|-------------|
| 💳 Stripe | Payment links, webhooks |
| 🏦 Bank Transfer | Wise SEPA/SWIFT |
| 🔗 Crypto | USDT/USDC on Polygon |

Auto-monitoring for crypto payments with `blockchain.py`.

---

## 🚂 Deployment

### Railway (Singularity Bot)

See `Singularity_Project/RAILWAY_DEPLOY.md` for full guide.

```bash
# Procfile
web: python bot.py
```

### Docker

```bash
# Build
docker build -t nexus10 .

# Run
docker run -d --env-file .env nexus10
```

---

## 📊 Features

- ✅ **Multi-Agent AI** - CrewAI orchestration
- ✅ **Self-Healing** - Auto-fix code errors
- ✅ **Vision Input** - Analyze screenshots/wireframes
- ✅ **Profit Pipeline** - Lead → Payment → Delivery
- ✅ **Gatekeeper** - 20% minimum margin filter
- ✅ **Blockchain Eye** - Crypto payment detection
- ✅ **PDF Invoices** - Professional invoice generation
- ✅ **Telegram Bot** - Full business interface

---

## 📄 License

MIT License - Use freely for personal and commercial projects.

---

## 🔗 Links

- **Author:** NEXUS 10 AI Agency
- **Version:** 10.0
- **Python:** 3.11+

---

*Built with ❤️ and AI*

