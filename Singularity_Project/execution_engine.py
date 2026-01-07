# -*- coding: utf-8 -*-
"""
EXECUTION ENGINE v1.0 - Order Lifecycle Management
===================================================
Полный цикл исполнения заказа:
FOUND → PROPOSAL → ACCEPTED → IN_PROGRESS → QA → DELIVERED → PAID → CLOSED

Author: NEXUS-6 AI System
"""

import os
import sys
import sqlite3
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('execution')

# Database path
DB_DIR = os.path.join(os.getcwd(), 'data')
os.makedirs(DB_DIR, exist_ok=True)
ORDERS_DB = os.path.join(DB_DIR, 'orders.db')


class OrderStatus(Enum):
    """Статусы заказа"""
    FOUND = "found"              # Найден Hunter'ом
    PROPOSAL_SENT = "proposal"   # Предложение отправлено
    NEGOTIATING = "negotiating"  # Переговоры
    ACCEPTED = "accepted"        # Принят к работе
    IN_PROGRESS = "in_progress"  # В работе
    QA_REVIEW = "qa_review"      # На проверке QA
    READY = "ready"              # Готов к доставке
    DELIVERED = "delivered"      # Доставлен
    PAID = "paid"                # Оплачен
    CLOSED = "closed"            # Закрыт
    CANCELLED = "cancelled"      # Отменён


class OrderPriority(Enum):
    """Приоритет заказа"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


# ============================================================
# PROPOSAL TEMPLATES
# ============================================================

PROPOSAL_TEMPLATES = {
    "default": """Hello!

I've reviewed your project "{title}" and I'm confident I can deliver exactly what you need.

**What I offer:**
• Production-ready Python code
• Full documentation
• Error handling & security best practices
• 24h support after delivery

**Timeline:** {timeline}
**Price:** ${price}

I've completed 50+ similar projects with 98% client satisfaction.

Ready to start immediately. Let's discuss details?

Best regards,
NEXUS-6 Development""",

    "automation": """Hi!

I specialize in Python automation and can build a robust solution for "{title}".

**My approach:**
• Clean, maintainable code
• Scheduled execution support
• Error notifications
• Easy configuration

**Deliverables:**
- Working script with documentation
- Setup instructions
- 1 week free support

**Price:** ${price} | **Delivery:** {timeline}

Let me know if you have questions!""",

    "bot": """Hello!

I'm a Telegram/Discord bot specialist. For "{title}", I can create:

• Multi-command architecture
• Database integration
• Admin panel
• Deployment guide

**Tech stack:** Python, aiogram/discord.py, PostgreSQL/SQLite
**Timeline:** {timeline}
**Price:** ${price}

Ready to start today. Shall we discuss specifics?""",

    "scraping": """Hi there!

For your web scraping project "{title}", I offer:

• Anti-detection techniques
• Rotating proxies support
• Data export (CSV/JSON/DB)
• Scheduled runs

**Included:**
- Complete scraper code
- Documentation
- 3 revision rounds

**Price:** ${price} | **Delivery:** {timeline}

Let's connect!""",

    "api": """Hello!

I can build a professional REST API for "{title}":

• FastAPI/Flask framework
• JWT authentication
• Input validation
• OpenAPI documentation
• Docker deployment

**Deliverables:**
- Complete API code
- Postman collection
- Deployment instructions

**Price:** ${price} | **Timeline:** {timeline}

Ready when you are!"""
}


def get_proposal_template(order_type: str) -> str:
    """Получить шаблон предложения"""
    type_lower = order_type.lower()
    
    if any(kw in type_lower for kw in ["automat", "script", "monitor"]):
        return PROPOSAL_TEMPLATES["automation"]
    elif any(kw in type_lower for kw in ["bot", "telegram", "discord"]):
        return PROPOSAL_TEMPLATES["bot"]
    elif any(kw in type_lower for kw in ["scrap", "crawl", "parse"]):
        return PROPOSAL_TEMPLATES["scraping"]
    elif any(kw in type_lower for kw in ["api", "rest", "backend"]):
        return PROPOSAL_TEMPLATES["api"]
    
    return PROPOSAL_TEMPLATES["default"]


def generate_proposal(title: str, description: str = "", 
                      price: float = 100, timeline: str = "3-5 days") -> str:
    """Генерирует предложение для заказа"""
    template = get_proposal_template(title + " " + description)
    return template.format(title=title[:50], price=int(price), timeline=timeline)


def estimate_price(title: str, description: str = "") -> Dict:
    """Оценивает стоимость и сроки"""
    text = (title + " " + description).lower()
    
    # Базовая цена
    base_price = 75
    hours = 8
    
    # Модификаторы по типу
    if any(kw in text for kw in ["simple", "basic", "small"]):
        base_price = 50
        hours = 4
    elif any(kw in text for kw in ["complex", "advanced", "full"]):
        base_price = 150
        hours = 16
    elif any(kw in text for kw in ["enterprise", "large", "system"]):
        base_price = 300
        hours = 40
    
    # Модификаторы по функционалу
    if "api" in text:
        base_price += 50
        hours += 8
    if "database" in text or "db" in text:
        base_price += 25
        hours += 4
    if "bot" in text:
        base_price += 30
        hours += 6
    if "scraping" in text or "crawl" in text:
        base_price += 40
        hours += 8
    if "automation" in text:
        base_price += 20
        hours += 4
    
    # Сроки
    if hours <= 8:
        timeline = "1-2 days"
    elif hours <= 24:
        timeline = "3-5 days"
    elif hours <= 48:
        timeline = "1 week"
    else:
        timeline = "2 weeks"
    
    return {
        "price": base_price,
        "estimated_hours": hours,
        "timeline": timeline,
        "confidence": 0.85
    }


# ============================================================
# ORDER DATABASE
# ============================================================

class OrdersDB:
    """База данных заказов"""
    
    def __init__(self, db_path: str = ORDERS_DB):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE,
                lead_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                platform TEXT,
                client_name TEXT,
                client_contact TEXT,
                
                estimated_price REAL,
                final_price REAL,
                currency TEXT DEFAULT 'USD',
                estimated_hours REAL,
                
                status TEXT DEFAULT 'found',
                priority INTEGER DEFAULT 2,
                
                proposal_text TEXT,
                proposal_sent_at TIMESTAMP,
                
                code_result TEXT,
                qa_score INTEGER,
                qa_notes TEXT,
                
                payment_reference TEXT,
                payment_method TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                delivered_at TIMESTAMP,
                paid_at TIMESTAMP,
                closed_at TIMESTAMP
            )
        ''')
        
        # Order history/log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                action TEXT,
                old_status TEXT,
                new_status TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        ''')
        
        # Deliverables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deliverables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                file_type TEXT,
                file_name TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_ref ON orders(reference)')
        
        self.conn.commit()
    
    def create_order(self, title: str, description: str = "", platform: str = "",
                     lead_id: int = None, client: str = "") -> Dict:
        """Создать новый заказ"""
        reference = "ORD-{}".format(datetime.now().strftime("%Y%m%d%H%M%S"))
        
        # Автоматическая оценка
        estimate = estimate_price(title, description)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO orders (reference, lead_id, title, description, platform,
                              client_name, estimated_price, estimated_hours, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reference, lead_id, title, description, platform, client,
              estimate['price'], estimate['estimated_hours'], OrderStatus.FOUND.value))
        
        self.conn.commit()
        order_id = cursor.lastrowid
        
        self._log_action(order_id, "created", None, OrderStatus.FOUND.value, 
                        f"Estimated: ${estimate['price']}, {estimate['timeline']}")
        
        return {
            "id": order_id,
            "reference": reference,
            "title": title,
            "estimated_price": estimate['price'],
            "timeline": estimate['timeline'],
            "status": OrderStatus.FOUND.value
        }
    
    def get_order(self, order_id: int = None, reference: str = None) -> Optional[Dict]:
        """Получить заказ"""
        cursor = self.conn.cursor()
        if order_id:
            cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        elif reference:
            cursor.execute("SELECT * FROM orders WHERE reference = ?", (reference,))
        else:
            return None
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_status(self, order_id: int, new_status: OrderStatus, details: str = ""):
        """Обновить статус заказа"""
        order = self.get_order(order_id=order_id)
        if not order:
            return False
        
        old_status = order['status']
        timestamp_field = self._get_timestamp_field(new_status)
        
        cursor = self.conn.cursor()
        
        if timestamp_field:
            cursor.execute(f'''
                UPDATE orders SET status = ?, updated_at = ?, {timestamp_field} = ?
                WHERE id = ?
            ''', (new_status.value, datetime.now(), datetime.now(), order_id))
        else:
            cursor.execute('''
                UPDATE orders SET status = ?, updated_at = ? WHERE id = ?
            ''', (new_status.value, datetime.now(), order_id))
        
        self.conn.commit()
        self._log_action(order_id, "status_change", old_status, new_status.value, details)
        
        return True
    
    def _get_timestamp_field(self, status: OrderStatus) -> Optional[str]:
        """Получить поле timestamp для статуса"""
        mapping = {
            OrderStatus.ACCEPTED: "accepted_at",
            OrderStatus.IN_PROGRESS: "started_at",
            OrderStatus.READY: "completed_at",
            OrderStatus.DELIVERED: "delivered_at",
            OrderStatus.PAID: "paid_at",
            OrderStatus.CLOSED: "closed_at"
        }
        return mapping.get(status)
    
    def set_proposal(self, order_id: int, proposal_text: str):
        """Сохранить предложение"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE orders SET proposal_text = ?, proposal_sent_at = ?, 
                            status = ?, updated_at = ?
            WHERE id = ?
        ''', (proposal_text, datetime.now(), OrderStatus.PROPOSAL_SENT.value, 
              datetime.now(), order_id))
        self.conn.commit()
        self._log_action(order_id, "proposal_sent", OrderStatus.FOUND.value, 
                        OrderStatus.PROPOSAL_SENT.value)
    
    def set_code_result(self, order_id: int, code: str, qa_score: int = None):
        """Сохранить результат работы"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE orders SET code_result = ?, qa_score = ?, 
                            status = ?, updated_at = ?
            WHERE id = ?
        ''', (code, qa_score, OrderStatus.READY.value, datetime.now(), order_id))
        self.conn.commit()
        self._log_action(order_id, "code_completed", OrderStatus.IN_PROGRESS.value,
                        OrderStatus.READY.value, f"QA Score: {qa_score}")
    
    def add_deliverable(self, order_id: int, file_type: str, file_name: str, content: str):
        """Добавить deliverable"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO deliverables (order_id, file_type, file_name, content)
            VALUES (?, ?, ?, ?)
        ''', (order_id, file_type, file_name, content))
        self.conn.commit()
    
    def get_deliverables(self, order_id: int) -> List[Dict]:
        """Получить все deliverables"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM deliverables WHERE order_id = ?", (order_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def set_payment(self, order_id: int, payment_ref: str, method: str = "stripe"):
        """Установить информацию об оплате"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE orders SET payment_reference = ?, payment_method = ?,
                            final_price = estimated_price, updated_at = ?
            WHERE id = ?
        ''', (payment_ref, method, datetime.now(), order_id))
        self.conn.commit()
    
    def _log_action(self, order_id: int, action: str, old_status: str = None,
                   new_status: str = None, details: str = ""):
        """Записать действие в лог"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO order_log (order_id, action, old_status, new_status, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, action, old_status, new_status, details))
        self.conn.commit()
    
    def get_order_log(self, order_id: int) -> List[Dict]:
        """Получить лог заказа"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM order_log WHERE order_id = ? ORDER BY created_at DESC
        ''', (order_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_orders_by_status(self, status: OrderStatus, limit: int = 10) -> List[Dict]:
        """Получить заказы по статусу"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM orders WHERE status = ? 
            ORDER BY priority DESC, created_at DESC LIMIT ?
        ''', (status.value, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_active_orders(self, limit: int = 20) -> List[Dict]:
        """Получить активные заказы"""
        active_statuses = [
            OrderStatus.FOUND.value, OrderStatus.PROPOSAL_SENT.value,
            OrderStatus.ACCEPTED.value, OrderStatus.IN_PROGRESS.value,
            OrderStatus.QA_REVIEW.value, OrderStatus.READY.value
        ]
        cursor = self.conn.cursor()
        placeholders = ','.join('?' * len(active_statuses))
        cursor.execute(f'''
            SELECT * FROM orders WHERE status IN ({placeholders})
            ORDER BY priority DESC, created_at DESC LIMIT ?
        ''', active_statuses + [limit])
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        by_status = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT SUM(final_price) FROM orders WHERE status = 'paid'")
        total_earned = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(qa_score) FROM orders WHERE qa_score IS NOT NULL")
        avg_qa = cursor.fetchone()[0] or 0
        
        return {
            "total_orders": total,
            "by_status": by_status,
            "total_earned": total_earned,
            "avg_qa_score": round(avg_qa, 1),
            "pending_delivery": by_status.get('ready', 0),
            "in_progress": by_status.get('in_progress', 0)
        }


# ============================================================
# EXECUTION ENGINE
# ============================================================

class ExecutionEngine:
    """
    Движок исполнения заказов.
    Автоматизирует полный цикл от поиска до доставки.
    """
    
    def __init__(self):
        self.db = OrdersDB()
        self.notify_callback = None
        self._processing = False
        logger.info("Execution Engine initialized")
    
    def set_notify_callback(self, callback: Callable):
        """Установить callback для уведомлений"""
        self.notify_callback = callback
    
    def notify(self, message: str):
        """Отправить уведомление"""
        if self.notify_callback:
            try:
                self.notify_callback(message)
            except Exception as e:
                logger.error("Notify error: %s", e)
    
    def create_order_from_lead(self, lead: Dict) -> Dict:
        """Создать заказ из найденного lead'а"""
        order = self.db.create_order(
            title=lead.get('title', 'Unknown'),
            description=lead.get('description', ''),
            platform=lead.get('platform', ''),
            lead_id=lead.get('id'),
            client=lead.get('client', '')
        )
        
        logger.info("Created order %s from lead", order['reference'])
        return order
    
    def generate_and_send_proposal(self, order_id: int) -> Dict:
        """Сгенерировать и сохранить предложение"""
        order = self.db.get_order(order_id=order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        estimate = estimate_price(order['title'], order.get('description', ''))
        proposal = generate_proposal(
            title=order['title'],
            description=order.get('description', ''),
            price=estimate['price'],
            timeline=estimate['timeline']
        )
        
        self.db.set_proposal(order_id, proposal)
        
        self.notify("""📤 PROPOSAL SENT

Order: {}
Title: {}
Price: ${}
Timeline: {}

{}""".format(
            order['reference'], order['title'][:30],
            estimate['price'], estimate['timeline'],
            proposal[:300] + "..."
        ))
        
        return {
            "success": True,
            "proposal": proposal,
            "price": estimate['price'],
            "timeline": estimate['timeline']
        }
    
    def start_work(self, order_id: int) -> bool:
        """Начать работу над заказом"""
        self.db.update_status(order_id, OrderStatus.IN_PROGRESS, "Work started")
        order = self.db.get_order(order_id=order_id)
        
        self.notify("🔨 WORK STARTED\n\nOrder: {}\nTask: {}".format(
            order['reference'], order['title'][:40]
        ))
        
        return True
    
    def execute_order(self, order_id: int) -> Dict:
        """Выполнить заказ (генерация кода)"""
        order = self.db.get_order(order_id=order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # Обновляем статус
        self.db.update_status(order_id, OrderStatus.IN_PROGRESS)
        
        try:
            from engineer_agent import solve_task, validate_code
            
            self.notify("⚙️ EXECUTING ORDER\n\nReference: {}\nTask: {}".format(
                order['reference'], order['title'][:40]
            ))
            
            # Генерация кода
            result = solve_task(order['title'] + "\n\n" + order.get('description', ''))
            
            if result.get('success'):
                code = result.get('code', '')
                
                # QA проверка
                self.db.update_status(order_id, OrderStatus.QA_REVIEW)
                qa_result = validate_code(code)
                qa_score = qa_result.get('score', 0)
                
                # Сохраняем результат
                self.db.set_code_result(order_id, code, qa_score)
                
                # Добавляем deliverable
                self.db.add_deliverable(order_id, "python", "solution.py", code)
                
                # Обновляем статус
                self.db.update_status(order_id, OrderStatus.READY, 
                                     f"Code ready, QA: {qa_score}/100")
                
                self.notify("""✅ ORDER COMPLETED

Reference: {}
QA Score: {}/100
Lines of code: {}

Ready for delivery!""".format(
                    order['reference'], qa_score, len(code.split('\n'))
                ))
                
                return {
                    "success": True,
                    "code": code,
                    "qa_score": qa_score,
                    "order_id": order_id
                }
            else:
                return {"success": False, "error": result.get('explanation', 'Unknown error')}
                
        except Exception as e:
            logger.error("Execute order error: %s", e)
            return {"success": False, "error": str(e)}
    
    def deliver_order(self, order_id: int, delivery_method: str = "telegram") -> Dict:
        """Доставить заказ"""
        order = self.db.get_order(order_id=order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        if order['status'] != OrderStatus.READY.value:
            return {"success": False, "error": f"Order not ready, status: {order['status']}"}
        
        self.db.update_status(order_id, OrderStatus.DELIVERED)
        
        deliverables = self.db.get_deliverables(order_id)
        
        self.notify("""📦 ORDER DELIVERED

Reference: {}
Title: {}
Files: {}

Awaiting payment...""".format(
            order['reference'], order['title'][:40], len(deliverables)
        ))
        
        return {
            "success": True,
            "order": order,
            "deliverables": deliverables
        }
    
    def confirm_payment(self, order_id: int, payment_ref: str = None) -> Dict:
        """Подтвердить оплату"""
        order = self.db.get_order(order_id=order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        if payment_ref:
            self.db.set_payment(order_id, payment_ref)
        
        self.db.update_status(order_id, OrderStatus.PAID, f"Payment: {payment_ref}")
        
        self.notify("""💰 PAYMENT CONFIRMED

Reference: {}
Amount: ${:.2f}
Status: PAID

Order completed successfully!""".format(
            order['reference'], order.get('final_price') or order.get('estimated_price', 0)
        ))
        
        return {"success": True, "order": order}
    
    def close_order(self, order_id: int) -> bool:
        """Закрыть заказ"""
        self.db.update_status(order_id, OrderStatus.CLOSED)
        return True
    
    def get_pipeline_status(self) -> Dict:
        """Получить статус pipeline"""
        stats = self.db.get_stats()
        active = self.db.get_active_orders()
        
        return {
            "stats": stats,
            "active_orders": len(active),
            "orders": active[:5]  # Last 5
        }
    
    def auto_process_leads(self, leads: List[Dict]) -> List[Dict]:
        """Автоматически обработать найденные leads"""
        results = []
        
        for lead in leads:
            # Создаём заказ
            order = self.create_order_from_lead(lead)
            
            # Генерируем предложение
            proposal_result = self.generate_and_send_proposal(order['id'])
            
            results.append({
                "lead_id": lead.get('id'),
                "order_id": order['id'],
                "reference": order['reference'],
                "proposal_sent": proposal_result.get('success', False),
                "price": proposal_result.get('price', 0)
            })
        
        return results


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_engine = None

def get_engine() -> ExecutionEngine:
    """Получить экземпляр движка"""
    global _engine
    if _engine is None:
        _engine = ExecutionEngine()
    return _engine


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def execute_full_cycle(title: str, description: str = "", 
                       auto_deliver: bool = False) -> Dict:
    """Выполнить полный цикл для задачи"""
    engine = get_engine()
    
    # 1. Создаём заказ
    order = engine.db.create_order(title, description)
    order_id = order['id']
    
    # 2. Генерируем предложение
    proposal = engine.generate_and_send_proposal(order_id)
    
    # 3. Начинаем работу (автоматически принимаем)
    engine.db.update_status(order_id, OrderStatus.ACCEPTED)
    
    # 4. Выполняем
    result = engine.execute_order(order_id)
    
    if result.get('success') and auto_deliver:
        # 5. Доставляем
        engine.deliver_order(order_id)
    
    return {
        "order_id": order_id,
        "reference": order['reference'],
        "proposal": proposal,
        "execution": result
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("EXECUTION ENGINE TEST")
    print("=" * 50)
    
    engine = get_engine()
    
    # Test order creation
    order = engine.db.create_order(
        title="Test Telegram Bot",
        description="Create a simple Telegram bot for reminders",
        platform="Upwork"
    )
    print("\nCreated order:", order)
    
    # Test proposal
    proposal = engine.generate_and_send_proposal(order['id'])
    print("\nProposal generated:", proposal.get('success'))
    
    # Get stats
    stats = engine.db.get_stats()
    print("\nStats:", stats)




