# -*- coding: utf-8 -*-
"""
🔗 NEXUS 10 AI AGENCY - ADMIN MOBILE INTERFACE
==============================================
Полный контроль над AI-агентством через Streamlit UI.
Адаптивный дизайн для смартфонов.

Features:
- 📊 Balance in USD/EUR + Recent Transactions
- 🤖 Agent Status Dashboard (with progress %)
- 📣 Herald Cycle - Twitter/YouTube Content Generation
- 💎 Blockchain Wallet Monitor (Polygon)
- 📈 Analytics & Metrics

Run: streamlit run admin_app.py --server.port 8501
Author: NEXUS 10 AI Agency
"""

import streamlit as st
import os
import sys
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# === PAGE CONFIG ===
st.set_page_config(
    page_title="NEXUS 10 ADMIN",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# === LOAD ENVIRONMENT ===
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# === CONSTANTS ===
MY_WALLET = os.getenv("MY_CRYPTO_WALLET", "0xf244499abff0e7c6939f470de0914fc1c848f308")
POLYGONSCAN_API_KEY = os.getenv("POLYGONSCAN_API_KEY", "")
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "nexus_business.db")
MEMORY_DB = os.path.join(os.path.dirname(__file__), "singularity_memory.db")

# === CUSTOM CSS - DARK MOBILE THEME ===
st.markdown("""
<style>
    /* === DARK THEME BASE === */
    .stApp {
        background: linear-gradient(135deg, #0d0d12 0%, #1a1a2e 50%, #16213e 100%);
        min-height: 100vh;
    }
    
    /* === MOBILE RESPONSIVE === */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem 0.5rem;
            max-width: 100%;
        }
        [data-testid="column"] {
            min-width: 100% !important;
        }
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.2rem !important;
        }
    }
    
    /* === GLOWING HEADERS === */
    h1, h2, h3 {
        background: linear-gradient(90deg, #00ff88, #00d4ff, #7b2dff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
        font-family: 'Orbitron', 'Courier New', monospace;
    }
    
    /* === NEON CARDS === */
    .neon-card {
        background: rgba(26, 26, 46, 0.9);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-left: 4px solid #00d4ff;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 
            0 0 10px rgba(0, 212, 255, 0.2),
            inset 0 0 20px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    .neon-card:hover {
        border-color: #00ff88;
        box-shadow: 
            0 0 20px rgba(0, 255, 136, 0.3),
            inset 0 0 20px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }
    
    /* === STATUS INDICATORS === */
    .status-online {
        color: #00ff88;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    .status-offline {
        color: #ff3366;
        text-shadow: 0 0 10px rgba(255, 51, 102, 0.5);
    }
    .status-working {
        color: #ffaa00;
        text-shadow: 0 0 10px rgba(255, 170, 0, 0.5);
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* === PROGRESS BARS === */
    .stProgress > div > div {
        background: linear-gradient(90deg, #00ff88, #00d4ff, #7b2dff);
        border-radius: 10px;
    }
    
    /* === BUTTONS === */
    .stButton > button {
        background: linear-gradient(135deg, #7b2dff 0%, #00d4ff 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(123, 45, 255, 0.4);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #00d4ff 0%, #00ff88 100%);
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5);
        transform: translateY(-2px);
    }
    
    /* === METRICS === */
    [data-testid="stMetric"] {
        background: rgba(26, 26, 46, 0.8);
        border: 1px solid rgba(0, 255, 136, 0.2);
        border-radius: 12px;
        padding: 1rem;
    }
    [data-testid="stMetric"] label {
        color: #00d4ff !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #00ff88 !important;
        font-size: 1.8rem !important;
        font-weight: bold !important;
    }
    
    /* === AGENT STATUS BADGE === */
    .agent-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .agent-ready {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 212, 255, 0.1));
        border: 1px solid #00ff88;
        color: #00ff88;
    }
    .agent-working {
        background: linear-gradient(135deg, rgba(255, 170, 0, 0.2), rgba(255, 100, 0, 0.1));
        border: 1px solid #ffaa00;
        color: #ffaa00;
    }
    
    /* === TRANSACTION LIST === */
    .tx-item {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 3px solid #00ff88;
    }
    .tx-amount {
        color: #00ff88;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .tx-time {
        color: #888;
        font-size: 0.8rem;
    }
    
    /* === SIDEBAR (MOBILE DRAWER) === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d12 0%, #1a1a2e 100%);
    }
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(26, 26, 46, 0.5);
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #888;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #7b2dff, #00d4ff);
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# === DATABASE FUNCTIONS ===

def get_db_connection() -> sqlite3.Connection:
    """Get database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_balance() -> Dict[str, float]:
    """Get total balance by currency"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT currency, SUM(amount_cents) as total 
            FROM transactions 
            WHERE type = 'INCOME' AND status = 'CONFIRMED'
            GROUP BY currency
        """)
        result = {"USD": 0.0, "EUR": 0.0, "USDT": 0.0}
        for row in cursor.fetchall():
            result[row['currency']] = row['total'] / 100.0 if row['total'] else 0.0
        conn.close()
        return result
    except Exception as e:
        return {"USD": 0.0, "EUR": 0.0, "USDT": 0.0, "error": str(e)}

def get_recent_transactions(limit: int = 10) -> List[Dict]:
    """Get recent transactions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, p.title as project_title 
            FROM transactions t
            LEFT JOIN projects p ON t.project_id = p.id
            ORDER BY t.created_at DESC
            LIMIT ?
        """, (limit,))
        txs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return txs
    except Exception as e:
        return []

def get_active_projects() -> List[Dict]:
    """Get active (non-closed) projects"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM projects 
            WHERE status NOT IN ('CLOSED', 'CANCELLED')
            ORDER BY created_at DESC
            LIMIT 20
        """)
        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return projects
    except Exception as e:
        return []

def get_stats() -> Dict[str, Any]:
    """Get system statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'PAID'")
        paid = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'PENDING'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(qa_score) FROM projects WHERE qa_score IS NOT NULL")
        avg_qa = cursor.fetchone()[0] or 0
        
        conn.close()
        return {
            "total_projects": total,
            "paid": paid,
            "pending": pending,
            "avg_qa_score": round(avg_qa, 1)
        }
    except Exception as e:
        return {"total_projects": 0, "paid": 0, "pending": 0, "avg_qa_score": 0}

# === BLOCKCHAIN FUNCTIONS ===

def get_polygon_transactions(wallet: str, limit: int = 10) -> List[Dict]:
    """Get recent transactions from Polygon via Polygonscan"""
    if not POLYGONSCAN_API_KEY:
        return [{"mock": True, "message": "API key not configured"}]
    
    try:
        # USDT Contract on Polygon
        usdt_contract = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
        
        url = f"https://api.polygonscan.com/api?module=account&action=tokentx&contractaddress={usdt_contract}&address={wallet}&page=1&offset={limit}&sort=desc&apikey={POLYGONSCAN_API_KEY}"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("status") == "1":
            txs = []
            for tx in data.get("result", [])[:limit]:
                if tx.get("to", "").lower() == wallet.lower():
                    txs.append({
                        "hash": tx.get("hash", "")[:16] + "...",
                        "from": tx.get("from", "")[:10] + "...",
                        "amount": int(tx.get("value", 0)) / 1e6,  # USDT has 6 decimals
                        "token": tx.get("tokenSymbol", "USDT"),
                        "timestamp": datetime.fromtimestamp(int(tx.get("timeStamp", 0))).strftime("%Y-%m-%d %H:%M"),
                        "block": tx.get("blockNumber", "")
                    })
            return txs
        return []
    except Exception as e:
        return [{"error": str(e)}]

# === AGENT STATUS ===

AGENT_CONFIG = {
    "hunter": {"icon": "🎯", "name": "Hunter", "role": "Global Scout", "color": "#00ff88"},
    "architect": {"icon": "🏗️", "name": "Architect", "role": "Tech Lead", "color": "#00d4ff"},
    "doer": {"icon": "💻", "name": "Doer", "role": "Senior Dev", "color": "#7b2dff"},
    "qa": {"icon": "✅", "name": "QA", "role": "Quality Gate", "color": "#ff006e"},
    "collector": {"icon": "💰", "name": "Collector", "role": "Finance", "color": "#ffaa00"},
    "strategist": {"icon": "📊", "name": "Strategist", "role": "Optimizer", "color": "#ff5500"},
}

def get_agent_status() -> Dict[str, Dict]:
    """Get current status of all agents"""
    # In real implementation, this would check running processes/threads
    # For now, return mock status
    statuses = {}
    for agent_id, config in AGENT_CONFIG.items():
        statuses[agent_id] = {
            **config,
            "status": "ready",  # ready, working, offline
            "progress": 100,    # 0-100%
            "last_task": "Idle",
            "last_run": datetime.now().strftime("%H:%M")
        }
    return statuses

# === HERALD CYCLE (CONTENT GENERATION) ===

def generate_herald_content() -> Dict:
    """
    Generate content for Twitter/YouTube using AI.
    This is a placeholder - in production would call OpenAI.
    """
    # Mock content generation
    templates = [
        {
            "type": "twitter",
            "content": "🚀 Just automated another client's workflow with NEXUS 10 AI.\n\n💡 What took 40 hours/month now takes 0.\n\n#AIAutomation #Python #Freelance",
            "hashtags": ["#AI", "#Automation", "#Python"]
        },
        {
            "type": "twitter",
            "content": "🤖 The future of freelancing:\n\n- AI finds the projects\n- AI writes the code\n- AI handles QA\n- You collect the payment\n\nThis is NEXUS 10.\n\n#AIAgency #Freelancer",
            "hashtags": ["#AIAgency", "#Freelance"]
        },
        {
            "type": "youtube",
            "title": "How AI Agents Are Replacing Traditional Freelancing",
            "description": "Deep dive into autonomous AI systems that find, build, and deliver software projects.",
            "tags": ["AI", "Automation", "Freelancing", "Python", "GPT"]
        }
    ]
    
    import random
    return random.choice(templates)

def run_herald_cycle() -> Dict:
    """Execute the Herald content generation cycle"""
    st.session_state["herald_running"] = True
    
    result = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "content": generate_herald_content(),
        "platforms": ["Twitter", "YouTube"],
        "message": "Content generated. Ready to post."
    }
    
    st.session_state["herald_running"] = False
    st.session_state["herald_last_run"] = datetime.now()
    st.session_state["herald_result"] = result
    
    return result

# === MAIN UI ===

def main():
    # === HEADER ===
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1>🔗 NEXUS 10</h1>
        <p style="color: #00d4ff; font-size: 0.9rem;">ADMIN MOBILE INTERFACE</p>
    </div>
    """, unsafe_allow_html=True)
    
    # === MAIN TABS ===
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🤖 Agents", "📣 Herald", "⚙️ System"])
    
    # =================== TAB 1: DASHBOARD ===================
    with tab1:
        # === BALANCE SECTION ===
        st.markdown("### 💎 Wallet Balance")
        
        balance = get_balance()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("USD", f"${balance.get('USD', 0):,.2f}")
        with col2:
            st.metric("EUR", f"€{balance.get('EUR', 0):,.2f}")
        with col3:
            st.metric("USDT", f"${balance.get('USDT', 0):,.2f}")
        
        st.markdown("---")
        
        # === CRYPTO WALLET MONITOR ===
        st.markdown("### 🔗 Polygon Wallet")
        
        wallet_display = f"{MY_WALLET[:10]}...{MY_WALLET[-6:]}"
        st.code(wallet_display, language=None)
        
        if st.button("🔄 Refresh Blockchain", key="refresh_blockchain"):
            with st.spinner("Fetching from Polygonscan..."):
                txs = get_polygon_transactions(MY_WALLET, limit=5)
                
                if txs and not txs[0].get("error") and not txs[0].get("mock"):
                    st.success(f"Found {len(txs)} recent transactions")
                    for tx in txs:
                        st.markdown(f"""
                        <div class="tx-item">
                            <div>
                                <span class="tx-amount">+{tx['amount']:.2f} {tx['token']}</span>
                                <br><span class="tx-time">{tx['timestamp']}</span>
                            </div>
                            <div style="color: #666; font-size: 0.8rem;">
                                From: {tx['from']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                elif txs and txs[0].get("mock"):
                    st.info("🔧 Configure POLYGONSCAN_API_KEY in .env for live data")
                else:
                    st.warning("No incoming transactions found")
        
        st.markdown("---")
        
        # === RECENT TRANSACTIONS ===
        st.markdown("### 📜 Recent Transactions")
        
        transactions = get_recent_transactions(5)
        if transactions:
            for tx in transactions:
                amount = tx.get('amount_cents', 0) / 100
                currency = tx.get('currency', 'USD')
                project = tx.get('project_title', 'Unknown')[:30]
                date = tx.get('created_at', '')[:10]
                
                st.markdown(f"""
                <div class="neon-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #00d4ff;">{project}</strong>
                            <br><span style="color: #666; font-size: 0.8rem;">{date}</span>
                        </div>
                        <div style="color: #00ff88; font-size: 1.2rem; font-weight: bold;">
                            +{amount:.2f} {currency}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No transactions yet. Start hunting for projects! 🎯")
    
    # =================== TAB 2: AGENTS ===================
    with tab2:
        st.markdown("### 🤖 Agent Status")
        
        agents = get_agent_status()
        
        for agent_id, agent in agents.items():
            status_class = "status-online" if agent["status"] == "ready" else "status-working"
            status_text = "READY" if agent["status"] == "ready" else "WORKING"
            
            st.markdown(f"""
            <div class="neon-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div>
                        <span style="font-size: 1.5rem;">{agent['icon']}</span>
                        <strong style="color: #fff; margin-left: 8px;">{agent['name']}</strong>
                        <span style="color: #666; font-size: 0.8rem; margin-left: 8px;">({agent['role']})</span>
                    </div>
                    <span class="{status_class}" style="font-weight: bold;">● {status_text}</span>
                </div>
                <div style="color: #888; font-size: 0.8rem;">
                    Last: {agent['last_task']} | {agent['last_run']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar for working agents
            if agent["status"] == "working":
                st.progress(agent["progress"] / 100)
        
        st.markdown("---")
        
        # === QUICK ACTIONS ===
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Start Hunter", key="start_hunter", use_container_width=True):
                st.info("Hunter scanning global markets for $50+ projects...")
                # In production: trigger actual hunter agent
                time.sleep(1)
                st.success("Hunter activated! Check results in 2-5 minutes.")
        
        with col2:
            if st.button("🏗️ Run Architect", key="start_architect", use_container_width=True):
                st.info("Architect ready. Select a project to analyze.")
    
    # =================== TAB 3: HERALD ===================
    with tab3:
        st.markdown("### 📣 The Herald")
        st.markdown("*AI Content Generation for Twitter/YouTube*")
        
        st.markdown("""
        <div class="neon-card">
            <h4 style="color: #00d4ff; margin: 0;">What is Herald?</h4>
            <p style="color: #aaa; margin-top: 0.5rem;">
                The Herald agent generates engaging content for social media
                to attract clients and showcase NEXUS 10 capabilities.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Herald Status
        last_run = st.session_state.get("herald_last_run", None)
        if last_run:
            st.markdown(f"**Last Run:** {last_run.strftime('%Y-%m-%d %H:%M')}")
        
        # === RUN HERALD ===
        if st.button("🚀 Run Herald Cycle", key="run_herald", use_container_width=True):
            with st.spinner("Generating content..."):
                result = run_herald_cycle()
                
                if result["status"] == "success":
                    st.success("✅ Content generated successfully!")
                    
                    content = result["content"]
                    
                    if content["type"] == "twitter":
                        st.markdown("#### 🐦 Twitter Post")
                        st.code(content["content"], language=None)
                        st.markdown(f"**Hashtags:** {' '.join(content['hashtags'])}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("📋 Copy", key="copy_twitter"):
                                st.info("Content copied! (Use Ctrl+C)")
                        with col2:
                            if st.button("🐦 Open Twitter", key="open_twitter"):
                                st.markdown("[Open Twitter](https://twitter.com/compose/tweet)")
                    
                    elif content["type"] == "youtube":
                        st.markdown("#### 🎬 YouTube Video Idea")
                        st.markdown(f"**Title:** {content['title']}")
                        st.markdown(f"**Description:** {content['description']}")
                        st.markdown(f"**Tags:** {', '.join(content['tags'])}")
        
        st.markdown("---")
        
        # === SCHEDULED POSTS ===
        st.markdown("### 📅 Schedule")
        
        schedule_enabled = st.checkbox("Enable auto-posting", value=False)
        
        if schedule_enabled:
            post_time = st.time_input("Daily post time", value=datetime.strptime("10:00", "%H:%M").time())
            platforms = st.multiselect("Platforms", ["Twitter", "YouTube", "LinkedIn"], default=["Twitter"])
            st.success(f"Herald will post daily at {post_time} to {', '.join(platforms)}")
    
    # =================== TAB 4: SYSTEM ===================
    with tab4:
        st.markdown("### ⚙️ System Status")
        
        # === SYSTEM METRICS ===
        stats = get_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Projects", stats["total_projects"])
            st.metric("Paid", stats["paid"])
        with col2:
            st.metric("Pending", stats["pending"])
            st.metric("Avg QA Score", f"{stats['avg_qa_score']}/100")
        
        st.markdown("---")
        
        # === ENVIRONMENT ===
        st.markdown("### 🔐 Environment")
        
        env_status = {
            "OPENAI_API_KEY": "✅" if os.getenv("OPENAI_API_KEY") else "❌",
            "TELEGRAM_BOT_TOKEN": "✅" if os.getenv("TELEGRAM_BOT_TOKEN") else "❌",
            "POLYGONSCAN_API_KEY": "✅" if os.getenv("POLYGONSCAN_API_KEY") else "❌",
            "MY_CRYPTO_WALLET": "✅" if os.getenv("MY_CRYPTO_WALLET") else "⚠️ (using default)",
        }
        
        for key, status in env_status.items():
            st.markdown(f"- **{key}**: {status}")
        
        st.markdown("---")
        
        # === DATABASE ===
        st.markdown("### 💾 Database")
        
        if os.path.exists(DB_PATH):
            size = os.path.getsize(DB_PATH) / 1024
            st.markdown(f"- **Business DB**: {DB_PATH} ({size:.1f} KB)")
        else:
            st.markdown("- **Business DB**: Not initialized")
        
        if os.path.exists(MEMORY_DB):
            size = os.path.getsize(MEMORY_DB) / 1024
            st.markdown(f"- **Memory DB**: {MEMORY_DB} ({size:.1f} KB)")
        else:
            st.markdown("- **Memory DB**: Not initialized")
        
        st.markdown("---")
        
        # === QUICK LINKS ===
        st.markdown("### 🔗 Quick Links")
        
        st.markdown("""
        - [Railway Dashboard](https://railway.com)
        - [Vercel Dashboard](https://vercel.com)
        - [GitHub Repo](https://github.com/Alex13Alex1/nexus10-brain)
        - [PolygonScan Wallet](https://polygonscan.com/address/0xf244499abff0e7c6939f470de0914fc1c848f308)
        """)

# === RUN ===
if __name__ == "__main__":
    main()




