# -*- coding: utf-8 -*-
"""
NEXUS 10 AI AGENCY - Support System v1.0
========================================
Автоматическая система поддержки клиентов.
Включает: FAQ бот, тикет система, AI-ассистент.

Author: Nexus 10 AI Agency
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
SUPPORT_DB = os.path.join(os.getcwd(), "support_tickets.db")
SUPPORT_HOURS = "24/7 (AI) | Human: Mon-Fri 9:00-18:00 UTC"
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@nexus10.ai")
SUPPORT_TELEGRAM = os.getenv("SUPPORT_TELEGRAM", "@nexus10_support")


# === FAQ DATABASE ===
FAQ_DATA = {
    "pricing": {
        "question": "How much do your services cost?",
        "answer": """**Pricing Guide:**
        
• Simple scripts (1-2 hours): $50-100
• Medium projects (3-8 hours): $100-400
• Complex projects (8+ hours): $400-2000

Factors affecting price:
- Project complexity
- Urgency (rush +20%)
- API integrations
- Documentation needs

Get a free estimate: Send /estimate [your project description]"""
    },
    
    "payment": {
        "question": "What payment methods do you accept?",
        "answer": """**Payment Options:**

[CARD] **Credit/Debit Card (Stripe)**
- Instant processing
- Visa, MasterCard, American Express

[BANK] **Bank Transfer (SEPA/SWIFT)**
- Processing: 1-3 business days
- Available worldwide

[CRYPTO] **Cryptocurrency**
- USDC/USDT on Polygon network
- Instant verification via blockchain

All payments are secure and encrypted."""
    },
    
    "timeline": {
        "question": "How long does delivery take?",
        "answer": """**Typical Delivery Times:**

• Simple projects: 1-2 days
• Medium projects: 3-5 days
• Complex projects: 1-2 weeks

Rush delivery available (+20% fee):
- 24-hour turnaround for simple projects
- 48-hour for medium projects

Timeline starts after payment confirmation."""
    },
    
    "revision": {
        "question": "What about revisions?",
        "answer": """**Revision Policy:**

✅ **Included FREE:**
- Up to 3 rounds of revisions
- Bug fixes within scope
- Minor adjustments

💰 **Additional charges apply:**
- Major scope changes
- New features not in original spec
- Revisions after 7 days

We work until you're satisfied!"""
    },
    
    "support": {
        "question": "What support do you offer?",
        "answer": """**Support Options:**

🤖 **AI Support (24/7)**
- Instant responses
- FAQ and common issues
- Project status updates

👨‍💻 **Human Support**
- Mon-Fri 9:00-18:00 UTC
- Complex issues
- Priority for paid clients

📧 **Email:** support@nexus10.ai
💬 **Telegram:** @nexus10_support

Response time: <2 hours (business hours)"""
    },
    
    "refund": {
        "question": "What's your refund policy?",
        "answer": """**Refund Policy:**

✅ **Full refund if:**
- Work not started yet
- We can't complete the project

⚡ **Partial refund if:**
- Project cancelled mid-way
- (Based on work completed)

❌ **No refund after:**
- Final delivery accepted
- 7 days post-delivery

We strive for 100% satisfaction!"""
    },
    
    "security": {
        "question": "Is my data secure?",
        "answer": """**Security Measures:**

🔒 **Code Security:**
- No hardcoded credentials
- Environment variables for secrets
- Input validation

📝 **NDA Available:**
- We can sign your NDA
- Confidentiality guaranteed

🗑️ **Data Handling:**
- Your code is yours
- We delete copies after delivery
- No sharing with third parties"""
    },
    
    "deliverables": {
        "question": "What do I receive?",
        "answer": """**Deliverables Include:**

📦 **Standard Package:**
- Complete source code
- requirements.txt / dependencies
- README with setup guide
- Basic documentation

⭐ **Premium Package (+50%):**
- Everything in Standard
- Detailed code comments
- API documentation
- Video walkthrough
- 30-day support"""
    }
}


# === TICKET SYSTEM ===

class SupportTicketDB:
    """Database for support tickets"""
    
    def __init__(self):
        self.conn = sqlite3.connect(SUPPORT_DB, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE,
                client_id TEXT,
                client_name TEXT,
                category TEXT,
                subject TEXT,
                message TEXT,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                assigned_to TEXT,
                created_at TEXT,
                updated_at TEXT,
                resolved_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT,
                sender TEXT,
                message TEXT,
                created_at TEXT,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
            )
        ''')
        
        self.conn.commit()
    
    def create_ticket(self, client_id: str, client_name: str, 
                      category: str, subject: str, message: str,
                      priority: str = "normal") -> str:
        """Create a new support ticket"""
        ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tickets 
            (ticket_id, client_id, client_name, category, subject, message, 
             status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
        ''', (ticket_id, client_id, client_name, category, subject, message,
              priority, datetime.now().isoformat(), datetime.now().isoformat()))
        
        self.conn.commit()
        return ticket_id
    
    def add_message(self, ticket_id: str, sender: str, message: str):
        """Add message to ticket"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO ticket_messages (ticket_id, sender, message, created_at)
            VALUES (?, ?, ?, ?)
        ''', (ticket_id, sender, message, datetime.now().isoformat()))
        
        cursor.execute('''
            UPDATE tickets SET updated_at = ? WHERE ticket_id = ?
        ''', (datetime.now().isoformat(), ticket_id))
        
        self.conn.commit()
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Get ticket details"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM tickets WHERE ticket_id = ?
        ''', (ticket_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [d[0] for d in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_client_tickets(self, client_id: str) -> List[Dict]:
        """Get all tickets for a client"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM tickets WHERE client_id = ? ORDER BY created_at DESC
        ''', (client_id,))
        
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_open_tickets(self) -> List[Dict]:
        """Get all open tickets"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM tickets WHERE status = 'open' ORDER BY 
            CASE priority 
                WHEN 'urgent' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'normal' THEN 3 
                WHEN 'low' THEN 4 
            END, created_at ASC
        ''')
        
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_status(self, ticket_id: str, status: str):
        """Update ticket status"""
        cursor = self.conn.cursor()
        
        if status == "resolved":
            cursor.execute('''
                UPDATE tickets SET status = ?, updated_at = ?, resolved_at = ?
                WHERE ticket_id = ?
            ''', (status, datetime.now().isoformat(), datetime.now().isoformat(), ticket_id))
        else:
            cursor.execute('''
                UPDATE tickets SET status = ?, updated_at = ? WHERE ticket_id = ?
            ''', (status, datetime.now().isoformat(), ticket_id))
        
        self.conn.commit()
    
    def assign_ticket(self, ticket_id: str, assignee: str):
        """Assign ticket to handler"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tickets SET assigned_to = ?, status = 'in_progress', updated_at = ?
            WHERE ticket_id = ?
        ''', (assignee, datetime.now().isoformat(), ticket_id))
        self.conn.commit()


# === SUPPORT AGENT ===

class SupportAgent:
    """AI-powered support agent"""
    
    def __init__(self):
        self.ticket_db = SupportTicketDB()
        self.faq = FAQ_DATA
    
    def find_faq_answer(self, query: str) -> Optional[str]:
        """Find matching FAQ answer"""
        query_lower = query.lower()
        
        keywords = {
            "pricing": ["price", "cost", "how much", "rate", "fee", "charge"],
            "payment": ["pay", "payment", "card", "crypto", "bank", "stripe", "wise"],
            "timeline": ["time", "long", "when", "delivery", "deadline", "fast"],
            "revision": ["revision", "change", "modify", "edit", "fix", "update"],
            "support": ["support", "help", "contact", "reach", "hours"],
            "refund": ["refund", "money back", "cancel", "return"],
            "security": ["secure", "safe", "nda", "confidential", "private"],
            "deliverables": ["receive", "get", "deliverable", "include", "package"]
        }
        
        for topic, words in keywords.items():
            if any(word in query_lower for word in words):
                return self.faq[topic]["answer"]
        
        return None
    
    def handle_query(self, client_id: str, client_name: str, query: str) -> Dict:
        """Handle support query"""
        
        # 1. Try FAQ first
        faq_answer = self.find_faq_answer(query)
        if faq_answer:
            return {
                "response": faq_answer,
                "source": "faq",
                "ticket_created": False,
                "needs_human": False
            }
        
        # 2. Try AI response
        try:
            from client_dialog import analyze_client_message
            ai_result = analyze_client_message(query)
            
            if ai_result.get("confidence", 0) > 0.7:
                return {
                    "response": ai_result["response"],
                    "source": "ai",
                    "ticket_created": False,
                    "needs_human": False,
                    "intent": ai_result.get("intent"),
                    "suggested_action": ai_result.get("suggested_action")
                }
        except Exception as e:
            print(f"[SUPPORT] AI error: {e}")
        
        # 3. Create ticket for human support
        ticket_id = self.ticket_db.create_ticket(
            client_id=client_id,
            client_name=client_name,
            category="general",
            subject=query[:100],
            message=query
        )
        
        return {
            "response": f"""I've created a support ticket for your query.

**Ticket ID:** `{ticket_id}`

A team member will respond within 2 hours during business hours.

In the meantime, you can:
• Check our FAQ: /faq
• View ticket status: /ticket {ticket_id}

Support hours: {SUPPORT_HOURS}""",
            "source": "ticket",
            "ticket_created": True,
            "ticket_id": ticket_id,
            "needs_human": True
        }
    
    def get_faq_menu(self) -> str:
        """Generate FAQ menu"""
        menu = "**📚 Frequently Asked Questions**\n\n"
        
        for key, data in self.faq.items():
            menu += f"• **/faq {key}** - {data['question']}\n"
        
        menu += "\nClick any topic above or type your question."
        return menu
    
    def get_ticket_status(self, ticket_id: str) -> str:
        """Get formatted ticket status"""
        ticket = self.ticket_db.get_ticket(ticket_id)
        
        if not ticket:
            return f"Ticket `{ticket_id}` not found."
        
        status_emoji = {
            "open": "🟡",
            "in_progress": "🔵",
            "resolved": "🟢",
            "closed": "⚫"
        }
        
        return f"""**Ticket Status**

ID: `{ticket['ticket_id']}`
Status: {status_emoji.get(ticket['status'], '⚪')} {ticket['status'].upper()}
Subject: {ticket['subject']}
Created: {ticket['created_at'][:16]}
Assigned: {ticket['assigned_to'] or 'Pending'}

{'**Resolution:** ' + ticket['resolved_at'][:16] if ticket['resolved_at'] else ''}

Need help? Contact: {SUPPORT_TELEGRAM}"""


# === SINGLETON ===
_support_agent_instance = None


def get_support_agent() -> SupportAgent:
    """Get or create SupportAgent singleton"""
    global _support_agent_instance
    if _support_agent_instance is None:
        _support_agent_instance = SupportAgent()
    return _support_agent_instance


# === QUICK FUNCTIONS FOR BOT ===

def handle_support_query(client_id: str, client_name: str, query: str) -> Dict:
    """Quick access for bot"""
    agent = get_support_agent()
    return agent.handle_query(client_id, client_name, query)


def get_faq_answer(topic: str) -> str:
    """Get FAQ answer by topic"""
    if topic in FAQ_DATA:
        return FAQ_DATA[topic]["answer"]
    return get_support_agent().get_faq_menu()


def create_ticket(client_id: str, client_name: str, 
                  category: str, subject: str, message: str) -> str:
    """Create support ticket"""
    agent = get_support_agent()
    return agent.ticket_db.create_ticket(
        client_id, client_name, category, subject, message
    )


# === TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("NEXUS 10 - Support System Test")
    print("=" * 60)
    
    agent = get_support_agent()
    
    # Test FAQ
    print("\n[TEST 1] FAQ Queries:")
    test_queries = [
        "How much does a bot cost?",
        "Do you accept crypto?",
        "How long for delivery?",
        "Random question about the weather"
    ]
    
    for query in test_queries:
        print(f"\nQ: {query}")
        result = agent.handle_query("test_123", "Test User", query)
        print(f"Source: {result['source']}")
        print(f"Response: {result['response'][:200]}...")
    
    # Test ticket
    print("\n[TEST 2] Ticket Creation:")
    ticket_id = agent.ticket_db.create_ticket(
        "test_456", "Test Client", "technical",
        "Bug in my code", "The script crashes on startup"
    )
    print(f"Ticket created: {ticket_id}")
    
    status = agent.get_ticket_status(ticket_id)
    print(status)
    
    print("\n" + "=" * 60)
    print("Support System Ready!")

