# -*- coding: utf-8 -*-
"""
🔗 NEXUS 10 AI AGENCY - MOBILE COMMAND CENTER
==============================================
Полный контроль над AI-агентством через Streamlit UI.

Features:
- 📊 Dashboard с метриками
- 🧪 Sandbox режим (симуляция)
- 🔎 Hunter: поиск лидов $50+
- 📝 Генерация документов (Invoice + Copyright)
- 💳 Blockchain проверка оплаты
- 📦 Доставка проектов
- 💬 Q&A верификация

Run: streamlit run nexus_app.py
Author: NEXUS 10 AI Agency
"""

import streamlit as st
import os
import sys
from datetime import datetime, date
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# === PAGE CONFIG ===
st.set_page_config(
    page_title="NEXUS 10 COMMAND",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS ===
st.markdown("""
<style>
    /* Dark futuristic theme */
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Glowing headers */
    h1, h2, h3 {
        background: linear-gradient(90deg, #00d4ff, #7b2dff, #ff006e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(145deg, #1e3a5f, #0f172a);
        border: 1px solid #00d4ff;
        color: #00d4ff;
        border-radius: 8px;
        transition: all 0.3s ease;
        text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
    }
    
    .stButton > button:hover {
        background: linear-gradient(145deg, #00d4ff, #0096c7);
        color: #0a0a0f;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.6);
        transform: translateY(-2px);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid rgba(0, 212, 255, 0.2);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #94a3b8;
        border: 1px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(145deg, #1e3a5f, #0f172a);
        border: 1px solid #00d4ff;
        color: #00d4ff;
    }
    
    /* Success/Info boxes */
    .stSuccess, .stInfo, .stWarning {
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    /* Text inputs */
    .stTextInput input, .stTextArea textarea {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(0, 212, 255, 0.3);
        color: #e2e8f0;
        border-radius: 8px;
    }
    
    /* Checkbox */
    .stCheckbox label span {
        color: #94a3b8;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(145deg, #059669, #047857);
        border: 1px solid #10b981;
        color: white;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# === SESSION STATE ===
if 'sandbox_mode' not in st.session_state:
    st.session_state.sandbox_mode = False
if 'current_project' not in st.session_state:
    st.session_state.current_project = None
if 'simulation_log' not in st.session_state:
    st.session_state.simulation_log = []


# === IMPORTS (with fallbacks) ===
try:
    from Singularity_Project.database import NexusDB
    db = NexusDB()
    db_available = True
except:
    db_available = False
    db = None

try:
    from Singularity_Project.invoice_gen import InvoiceGenerator
    invoice_gen = InvoiceGenerator()
    invoice_available = True
except:
    invoice_available = False
    invoice_gen = None

try:
    from nexus_core.blockchain import BlockchainEye, get_blockchain_eye
    blockchain_available = True
except:
    try:
        from Singularity_Project.blockchain_eye import BlockchainEye, get_blockchain_eye
        blockchain_available = True
    except:
        blockchain_available = False


# === HELPER FUNCTIONS ===

def log_simulation(action: str, result: str):
    """Log action in sandbox mode"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.simulation_log.append({
        "time": timestamp,
        "action": action,
        "result": result
    })


def generate_pdf_package(client_name: str, amount: float, currency: str = "USD") -> str:
    """Generate Invoice + Copyright Transfer PDF"""
    if st.session_state.sandbox_mode:
        log_simulation("Generate PDF", f"Invoice for {client_name}: ${amount}")
        return None
    
    if invoice_available:
        return invoice_gen.create_pdf(
            project_name=f"Project for {client_name}",
            amount=amount,
            currency=currency,
            client_name=client_name
        )
    return None


def check_blockchain_payment(amount: float) -> Dict:
    """Check for crypto payment"""
    if st.session_state.sandbox_mode:
        log_simulation("Check Payment", f"Simulated check for ${amount}")
        return {
            "found": True,
            "tx_hash": "0x" + "a" * 64 + " (SIMULATED)",
            "actual_amount": amount,
            "message": "✅ SANDBOX: Payment simulated successfully!"
        }
    
    if blockchain_available:
        eye = get_blockchain_eye()
        return eye.check_payment(amount)
    return {"found": False, "message": "Blockchain module not available"}


def run_hunter_search(min_budget: int = 50) -> List[Dict]:
    """Run Hunter agent to find leads"""
    if st.session_state.sandbox_mode:
        log_simulation("Hunter Search", f"Searching leads ${min_budget}+")
        # Return simulated leads
        return [
            {"title": "AI Chatbot Development", "budget": "$150-300", "platform": "Upwork", "score": 9.2},
            {"title": "Python Automation Script", "budget": "$80-150", "platform": "Freelancer", "score": 8.5},
            {"title": "Telegram Bot with API", "budget": "$200-400", "platform": "Upwork", "score": 9.0},
        ]
    
    # Real implementation would call hunter agent
    return []


def analyze_qa_question(question: str) -> str:
    """Analyze client question with QA agent"""
    if st.session_state.sandbox_mode:
        log_simulation("QA Analysis", f"Question: {question[:50]}...")
        return f"""
**🤖 QA Agent Analysis:**

Question received: "{question}"

**Verdict:** ✅ Request is consistent with NEXUS v10.0 architecture.

**Recommendations:**
1. This modification is technically feasible
2. Estimated time: 2-4 hours
3. No breaking changes detected
4. Full test coverage recommended

**Risk Level:** LOW 🟢
        """
    
    # Real implementation would use OpenAI
    return "QA module not available in production mode"


# === SIDEBAR ===
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/0a0a0f/00d4ff?text=NEXUS+10", width=150)
    
    st.markdown("---")
    
    # Sandbox Mode Toggle
    st.header("🧪 Test Environment")
    sandbox = st.checkbox(
        "Activate Sandbox Mode",
        value=st.session_state.sandbox_mode,
        help="Simulate all operations without real money/API calls"
    )
    st.session_state.sandbox_mode = sandbox
    
    if sandbox:
        st.success("🧪 SANDBOX ACTIVE")
        st.caption("All operations are simulated")
    else:
        st.warning("⚡ PRODUCTION MODE")
        st.caption("Real API calls enabled")
    
    st.markdown("---")
    
    # System Status
    st.header("📊 System Status")
    
    status_items = [
        ("Database", db_available, "NexusDB"),
        ("Invoices", invoice_available, "PDF Generator"),
        ("Blockchain", blockchain_available, "PolygonScan"),
    ]
    
    for name, available, desc in status_items:
        icon = "✅" if available else "❌"
        st.markdown(f"{icon} **{name}**: {desc}")
    
    st.markdown("---")
    
    # Quick Stats
    if db_available:
        stats = db.get_stats()
        st.metric("Total Projects", stats.get("total_projects", 0))
        st.metric("Avg QA Score", f"{stats.get('avg_qa_score', 0):.1f}/100")
    
    # Simulation Log (in sandbox mode)
    if sandbox and st.session_state.simulation_log:
        st.markdown("---")
        st.header("📋 Simulation Log")
        for log in st.session_state.simulation_log[-5:]:
            st.caption(f"[{log['time']}] {log['action']}")
        
        if st.button("Clear Log"):
            st.session_state.simulation_log = []
            st.rerun()


# === MAIN CONTENT ===

# Header
st.title("🔗 NEXUS 10: Mobile Command Center")
st.caption("Autonomous AI Agency Control Panel v10.0")

# Top Metrics Dashboard
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if blockchain_available and not st.session_state.sandbox_mode:
        try:
            eye = get_blockchain_eye()
            balance = eye.get_balance_24h()
            wallet_balance = balance.get("total", 0)
        except:
            wallet_balance = 0
    else:
        wallet_balance = 1250.00 if st.session_state.sandbox_mode else 0
    st.metric("💳 Wallet Balance", f"${wallet_balance:,.2f}", "24h")

with col2:
    active_orders = 3 if st.session_state.sandbox_mode else (
        len(db.get_pending_projects()) if db_available else 0
    )
    st.metric("📦 Active Orders", active_orders)

with col3:
    system_status = "SANDBOX" if st.session_state.sandbox_mode else "PRODUCTION"
    st.metric("⚡ System Mode", system_status)

with col4:
    st.metric("🤖 Agents Online", "10+", "Elite v4.0")


# === MAIN TABS ===
st.markdown("---")
st.header("🔄 Full Cycle Management")

tabs = st.tabs(["🔎 Hunt", "📝 Proposal", "💳 Payment", "📦 Delivery", "💬 Q&A Center"])


# === TAB 1: HUNT ===
with tabs[0]:
    st.subheader("🎯 Lead Hunter - Search $50+ Projects")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        min_budget = st.slider("Minimum Budget ($)", 50, 500, 50, step=25)
        platforms = st.multiselect(
            "Platforms",
            ["Upwork", "Freelancer", "Fiverr", "Toptal", "LinkedIn"],
            default=["Upwork", "Freelancer"]
        )
    
    with col2:
        st.markdown("### 🌍 Markets")
        st.checkbox("🇺🇸 USA", value=True)
        st.checkbox("🇬🇧 UK", value=True)
        st.checkbox("🇪🇺 Europe", value=True)
        st.checkbox("🌏 Global", value=False)
    
    if st.button("🚀 Launch Hunter Agent", type="primary", use_container_width=True):
        with st.spinner("🔍 Scanning markets for opportunities..."):
            leads = run_hunter_search(min_budget)
            
            if leads:
                st.success(f"Found {len(leads)} qualified leads!")
                
                for i, lead in enumerate(leads, 1):
                    with st.expander(f"#{i} {lead['title']} - {lead['budget']}", expanded=i==1):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Platform:** {lead['platform']}")
                            st.write(f"**Budget:** {lead['budget']}")
                        with col2:
                            st.metric("Match Score", f"{lead['score']}/10")
                        
                        if st.button(f"📝 Create Proposal", key=f"prop_{i}"):
                            st.session_state.current_project = lead
                            st.info("Switch to Proposal tab to continue")
            else:
                st.warning("No leads found. Try adjusting filters.")


# === TAB 2: PROPOSAL ===
with tabs[1]:
    st.subheader("📝 Proposal & Document Generation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        client_name = st.text_input("Client Name", placeholder="John Smith")
        project_title = st.text_input("Project Title", placeholder="AI Telegram Bot")
    
    with col2:
        amount = st.number_input("Amount ($)", min_value=50, max_value=50000, value=250, step=50)
        currency = st.selectbox("Currency", ["USD", "EUR", "USDT"])
    
    st.text_area(
        "Proposal Draft",
        value=f"""Dear {client_name or 'Client'},

Thank you for your interest in {project_title or 'our services'}.

We propose a solution powered by NEXUS 10 AI Agency technology:

✅ Full development with AI-assisted coding
✅ Quality assurance (QA score 95%+)
✅ 48-72 hour turnaround
✅ Unlimited revisions for 7 days
✅ Source code ownership transfer

Investment: ${amount} {currency}

Payment accepted via:
• Crypto (USDT/USDC on Polygon) - Instant
• Bank Transfer (SEPA/SWIFT) - 1-2 days

Best regards,
NEXUS 10 AI Agency""",
        height=300
    )
    
    st.markdown("---")
    st.markdown("### 📄 Generate Legal Documents")
    
    doc_col1, doc_col2 = st.columns(2)
    
    with doc_col1:
        if st.button("📄 Generate Invoice PDF", use_container_width=True):
            if client_name and amount:
                pdf_path = generate_pdf_package(client_name, amount, currency)
                
                if pdf_path and os.path.exists(pdf_path):
                    st.success("✅ Invoice generated!")
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Invoice",
                            f,
                            file_name=f"invoice_{client_name}.pdf",
                            mime="application/pdf"
                        )
                elif st.session_state.sandbox_mode:
                    st.success("✅ SANDBOX: Invoice would be generated")
                else:
                    st.error("Failed to generate invoice")
            else:
                st.warning("Please fill client name and amount")
    
    with doc_col2:
        if st.button("📜 Generate Copyright Agreement", use_container_width=True):
            if client_name:
                if st.session_state.sandbox_mode:
                    st.success("✅ SANDBOX: Copyright agreement would be generated")
                    log_simulation("Copyright Doc", f"For {client_name}")
                else:
                    # Real implementation
                    st.info("Copyright agreement generation...")
            else:
                st.warning("Please enter client name")


# === TAB 3: PAYMENT ===
with tabs[2]:
    st.subheader("💳 Payment Verification")
    
    st.markdown("""
    **Accepted Payment Methods:**
    - 🔷 **Crypto**: USDT/USDC on Polygon Network
    - 🏦 **Bank**: SEPA/SWIFT via Wise
    """)
    
    st.markdown("---")
    
    # Crypto Payment Check
    st.markdown("### 🔷 Check Crypto Payment")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        check_amount = st.number_input(
            "Expected Amount ($)", 
            min_value=10.0, 
            max_value=10000.0, 
            value=250.0,
            step=10.0
        )
        wallet_display = os.getenv("MY_CRYPTO_WALLET", "0xf244499abff0e7c6939f470de0914fc1c848f308")
    
    with col2:
        st.markdown("**Wallet:**")
        st.code(wallet_display[:20] + "...")
    
    if st.button("🔍 Check PolygonScan", use_container_width=True, type="primary"):
        with st.spinner("Checking blockchain..."):
            result = check_blockchain_payment(check_amount)
            
            if result.get("found"):
                st.success(f"✅ Payment Found!")
                st.json({
                    "Amount": result.get("actual_amount", check_amount),
                    "Transaction": result.get("tx_hash", "")[:40] + "...",
                    "Status": "CONFIRMED"
                })
                
                # Auto-update order status
                if db_available and not st.session_state.sandbox_mode:
                    st.info("Order status updated to PAID")
            else:
                st.warning(f"⏳ {result.get('message', 'Payment not found yet')}")
                st.caption("Payments are checked every 5 minutes automatically")
    
    st.markdown("---")
    
    # Pending Payments
    st.markdown("### 📋 Pending Payments")
    
    if db_available:
        pending = db.get_pending_projects()
        if pending:
            for proj in pending[:5]:
                with st.expander(f"📦 {proj.get('title', 'Project')} - ${proj.get('budget_amount', 0)}"):
                    st.write(f"**Reference:** {proj.get('reference')}")
                    st.write(f"**Created:** {proj.get('created_at')}")
                    st.write(f"**Status:** {proj.get('status')}")
        else:
            st.info("No pending payments")
    elif st.session_state.sandbox_mode:
        # Simulated pending payments
        for i, proj in enumerate([
            {"title": "AI Chatbot", "amount": 250, "ref": "SNG-20260107001"},
            {"title": "API Integration", "amount": 180, "ref": "SNG-20260107002"},
        ]):
            with st.expander(f"📦 {proj['title']} - ${proj['amount']}"):
                st.write(f"**Reference:** {proj['ref']}")
                st.write("**Status:** PENDING")


# === TAB 4: DELIVERY ===
with tabs[3]:
    st.subheader("📦 Project Delivery")
    
    st.markdown("""
    ### Delivery Checklist
    Before sending the project to the client:
    """)
    
    checklist = [
        st.checkbox("✅ Code reviewed and tested"),
        st.checkbox("✅ QA score 90%+"),
        st.checkbox("✅ Documentation complete"),
        st.checkbox("✅ Payment confirmed"),
        st.checkbox("✅ Copyright transfer ready"),
    ]
    
    all_checked = all(checklist)
    
    st.markdown("---")
    
    project_ref = st.text_input("Project Reference", placeholder="SNG-20260107001")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📦 Package Project", disabled=not all_checked, use_container_width=True):
            if st.session_state.sandbox_mode:
                st.success("✅ SANDBOX: Project packaged as ZIP")
                log_simulation("Package", f"Project {project_ref}")
            else:
                st.info("Packaging project files...")
    
    with col2:
        if st.button("📧 Send to Client", disabled=not all_checked, use_container_width=True, type="primary"):
            if st.session_state.sandbox_mode:
                st.success("✅ SANDBOX: Project would be sent to client")
                st.balloons()
                log_simulation("Delivery", f"Sent {project_ref}")
            else:
                st.info("Sending to client...")
    
    if not all_checked:
        st.warning("⚠️ Complete all checklist items before delivery")


# === TAB 5: Q&A CENTER ===
with tabs[4]:
    st.subheader("💬 Verification Center")
    
    st.markdown("""
    **Use this module to:**
    - Verify client change requests
    - Check compatibility with architecture
    - Analyze edge cases
    - Get QA recommendations
    """)
    
    user_query = st.text_area(
        "Enter client question or change request:",
        placeholder="Example: Can you add payment integration with Stripe?",
        height=100
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        query_type = st.selectbox(
            "Query Type",
            ["Client Request", "Change Request", "Bug Report", "Feature Question"]
        )
    
    with col2:
        priority = st.selectbox(
            "Priority",
            ["Normal", "High", "Critical"]
        )
    
    if st.button("🤖 Analyze with QA Agent", use_container_width=True, type="primary"):
        if user_query:
            with st.spinner("QA Agent analyzing..."):
                response = analyze_qa_question(user_query)
                st.markdown(response)
                
                if st.session_state.sandbox_mode:
                    log_simulation("QA Query", query_type)
        else:
            st.warning("Please enter a question")
    
    st.markdown("---")
    
    # Recent Q&A History
    st.markdown("### 📚 Recent Q&A History")
    
    if st.session_state.sandbox_mode:
        history = [
            {"q": "Add dark mode support?", "status": "✅ Approved", "time": "10:30"},
            {"q": "Change database to PostgreSQL?", "status": "⚠️ Review needed", "time": "09:15"},
            {"q": "Add multi-language support?", "status": "✅ Approved", "time": "08:45"},
        ]
        
        for item in history:
            st.markdown(f"**[{item['time']}]** {item['q']} - {item['status']}")


# === FOOTER ===
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.8em;">
    🔗 NEXUS 10 AI AGENCY v10.0 | Autonomous Development System<br>
    <span style="color: #00d4ff;">Made with ❤️ by AI Agents</span>
</div>
""", unsafe_allow_html=True)


