# -*- coding: utf-8 -*-
"""
NEXUS 10 AI AGENCY DATABASE v3.0
================================
- Financial precision (cents accuracy)
- Profitability tracking (estimated_margin)
- Big Data history integration
- QA results linkage
- Gatekeeper verdicts

Author: NEXUS 10 AI Agency
"""
import sqlite3
import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any

# === DATABASE PATHS ===
DB_DIR = os.path.join(os.getcwd(), 'data')
os.makedirs(DB_DIR, exist_ok=True)

BUSINESS_DB = os.path.join(DB_DIR, 'nexus_business.db')
MEMORY_DB = 'singularity_memory.db'
LEADS_DB = os.path.join(DB_DIR, 'leads.db')

class NexusDB:
    """
    Финансовое хранилище Nexus-6
    Точность: до 0.01 в любой валюте
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or BUSINESS_DB
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """Создать все таблицы с финансовой точностью"""
        cursor = self.conn.cursor()
        
        # === PROJECTS TABLE ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                budget_amount REAL NOT NULL,
                budget_currency TEXT DEFAULT 'USD',
                actual_hours REAL,
                estimated_hours REAL,
                estimated_margin REAL,
                estimated_profit REAL,
                gatekeeper_verdict TEXT,
                spec_status TEXT DEFAULT 'DRAFT',
                status TEXT DEFAULT 'PENDING',
                qa_score INTEGER,
                client_name TEXT,
                platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                vetted_at TIMESTAMP,
                spec_approved_at TIMESTAMP,
                paid_at TIMESTAMP,
                delivered_at TIMESTAMP,
                closed_at TIMESTAMP
            )
        ''')
        
        # === TRANSACTIONS TABLE (точность до цента) ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                reference TEXT,
                amount_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                type TEXT DEFAULT 'INCOME',
                source TEXT,
                wise_transaction_id TEXT,
                stripe_payment_id TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # === QA REPORTS TABLE ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                score INTEGER,
                status TEXT,
                critical_issues TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # === DAILY EARNINGS TABLE ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                usd_cents INTEGER DEFAULT 0,
                eur_cents INTEGER DEFAULT 0,
                projects_completed INTEGER DEFAULT 0,
                avg_qa_score REAL,
                avg_margin REAL,
                total_profit_cents INTEGER DEFAULT 0
            )
        ''')
        
        # === GATEKEEPER LOG TABLE ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gatekeeper_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                reference TEXT,
                client_budget REAL,
                estimated_costs REAL,
                estimated_margin REAL,
                estimated_profit REAL,
                decision TEXT,
                reason TEXT,
                suggested_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # === SPECIFICATIONS TABLE (Deep Spec / Atomic Requirements) ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS specifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                version INTEGER DEFAULT 1,
                status TEXT DEFAULT 'DRAFT',
                requirements_json TEXT,
                clarifying_questions TEXT,
                client_responses TEXT,
                fixed_price REAL,
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # === CLARIFYING QUESTIONS TABLE ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clarifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                question TEXT,
                answer TEXT,
                asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answered_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # === INDICES для быстрого поиска ===
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_reference ON projects(reference)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_reference ON transactions(reference)')
        
        self.conn.commit()

    # === PROJECT METHODS ===
    
    def add_project(self, title: str, budget: float, currency: str = "USD", 
                    description: str = "", client: str = "", platform: str = "") -> int:
        """Добавить новый проект"""
        reference = f"SNG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO projects (reference, title, description, budget_amount, 
                                  budget_currency, client_name, platform)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (reference, title, description, budget, currency, client, platform))
        self.conn.commit()
        return cursor.lastrowid

    def get_project(self, project_id: int) -> Optional[Dict]:
        """Получить проект по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_project_by_reference(self, reference: str) -> Optional[Dict]:
        """Получить проект по reference"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE reference = ?", (reference,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_project_status(self, project_id: int, status: str):
        """Обновить статус проекта"""
        cursor = self.conn.cursor()
        timestamp_field = None
        if status == "PAID":
            timestamp_field = "paid_at"
        elif status == "DELIVERED":
            timestamp_field = "delivered_at"
        elif status == "CLOSED":
            timestamp_field = "closed_at"
        
        if timestamp_field:
            cursor.execute(f'''
                UPDATE projects SET status = ?, {timestamp_field} = ? WHERE id = ?
            ''', (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), project_id))
        else:
            cursor.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
        self.conn.commit()

    def mark_as_paid(self, project_id: int, amount_received: float = None):
        """Отметить проект как оплаченный"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE projects SET status = 'PAID', paid_at = ? WHERE id = ?
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), project_id))
        self.conn.commit()
        
        # Обновить daily earnings
        self._update_daily_earnings(project_id)

    def set_qa_score(self, project_id: int, score: int):
        """Установить QA score для проекта"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE projects SET qa_score = ? WHERE id = ?", (score, project_id))
        self.conn.commit()

    # === TRANSACTION METHODS (Точность до цента) ===
    
    def _to_cents(self, amount: float) -> int:
        """Конвертировать в центы для точного хранения"""
        return int(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)

    def _from_cents(self, cents: int) -> float:
        """Конвертировать из центов"""
        return cents / 100.0

    def record_transaction(self, project_id: int, amount: float, currency: str = "USD",
                          reference: str = "", source: str = "WISE", 
                          transaction_type: str = "INCOME") -> int:
        """Записать транзакцию с точностью до цента"""
        amount_cents = self._to_cents(amount)
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (project_id, reference, amount_cents, currency, 
                                       type, source, status)
            VALUES (?, ?, ?, ?, ?, ?, 'CONFIRMED')
        ''', (project_id, reference, amount_cents, currency, transaction_type, source))
        self.conn.commit()
        return cursor.lastrowid

    def record_payment(self, wise_ref: str, amount: float, currency: str = "USD",
                       sender: str = "", wise_transaction_id: str = "") -> int:
        """Записать входящий платёж"""
        # Найти проект по reference
        project = self.get_project_by_reference(wise_ref)
        project_id = project['id'] if project else None
        
        amount_cents = self._to_cents(amount)
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (project_id, reference, amount_cents, currency,
                                       type, source, wise_transaction_id, status, confirmed_at)
            VALUES (?, ?, ?, ?, 'INCOME', 'WISE', ?, 'CONFIRMED', ?)
        ''', (project_id, wise_ref, amount_cents, currency, wise_transaction_id,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.conn.commit()
        
        # Обновить статус проекта
        if project_id:
            self.mark_as_paid(project_id, amount)
        
        return cursor.lastrowid

    # === QA REPORTS ===
    
    def save_qa_report(self, project_id: int, score: int, status: str,
                       critical_issues: str = "", recommendations: str = "") -> int:
        """Сохранить QA отчёт"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO qa_reports (project_id, score, status, critical_issues, recommendations)
            VALUES (?, ?, ?, ?, ?)
        ''', (project_id, score, status, critical_issues, recommendations))
        
        # Обновить score в проекте
        cursor.execute("UPDATE projects SET qa_score = ? WHERE id = ?", (score, project_id))
        self.conn.commit()
        return cursor.lastrowid

    # === EARNINGS METHODS ===
    
    def _update_daily_earnings(self, project_id: int):
        """Обновить дневную статистику заработка"""
        project = self.get_project(project_id)
        if not project:
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        amount_cents = self._to_cents(project['budget_amount'])
        currency = project['budget_currency']
        qa_score = project.get('qa_score', 0) or 0
        
        cursor = self.conn.cursor()
        
        # Проверить существует ли запись
        cursor.execute("SELECT id FROM daily_earnings WHERE date = ?", (today,))
        existing = cursor.fetchone()
        
        if existing:
            if currency == 'USD':
                cursor.execute('''
                    UPDATE daily_earnings 
                    SET usd_cents = usd_cents + ?, 
                        projects_completed = projects_completed + 1,
                        avg_qa_score = (avg_qa_score * projects_completed + ?) / (projects_completed + 1)
                    WHERE date = ?
                ''', (amount_cents, qa_score, today))
            else:
                cursor.execute('''
                    UPDATE daily_earnings 
                    SET eur_cents = eur_cents + ?,
                        projects_completed = projects_completed + 1,
                        avg_qa_score = (avg_qa_score * projects_completed + ?) / (projects_completed + 1)
                    WHERE date = ?
                ''', (amount_cents, qa_score, today))
        else:
            usd = amount_cents if currency == 'USD' else 0
            eur = amount_cents if currency == 'EUR' else 0
            cursor.execute('''
                INSERT INTO daily_earnings (date, usd_cents, eur_cents, projects_completed, avg_qa_score)
                VALUES (?, ?, ?, 1, ?)
            ''', (today, usd, eur, qa_score))
        
        self.conn.commit()

    def get_total_earnings(self) -> List[Tuple[str, float]]:
        """Получить общий заработок по валютам"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT currency, SUM(amount_cents) as total_cents 
            FROM transactions 
            WHERE type = 'INCOME' AND status = 'CONFIRMED'
            GROUP BY currency
        ''')
        results = []
        for row in cursor.fetchall():
            results.append((row['currency'], self._from_cents(row['total_cents'])))
        return results

    def get_monthly_earnings(self, year: int, month: int) -> Dict[str, float]:
        """Получить заработок за месяц"""
        cursor = self.conn.cursor()
        date_pattern = f"{year}-{month:02d}%"
        cursor.execute('''
            SELECT currency, SUM(amount_cents) as total 
            FROM transactions 
            WHERE confirmed_at LIKE ? AND type = 'INCOME'
            GROUP BY currency
        ''', (date_pattern,))
        
        result = {"USD": 0.0, "EUR": 0.0}
        for row in cursor.fetchall():
            result[row['currency']] = self._from_cents(row['total'])
        return result

    # === STATISTICS ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Полная статистика"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'PAID'")
        paid = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'PENDING'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(qa_score) FROM projects WHERE qa_score IS NOT NULL")
        avg_qa = cursor.fetchone()[0] or 0
        
        earnings = self.get_total_earnings()
        
        return {
            "total_projects": total,
            "paid": paid,
            "pending": pending,
            "avg_qa_score": round(avg_qa, 1),
            "earnings": earnings
        }

    def get_pending_projects(self) -> List[Dict]:
        """Получить проекты ожидающие оплаты"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE status = 'PENDING' ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def get_paid_projects(self, limit: int = 10) -> List[Dict]:
        """Получить оплаченные проекты"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM projects WHERE status = 'PAID' 
            ORDER BY paid_at DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # === GATEKEEPER METHODS ===
    
    def log_gatekeeper_decision(self, project_id: int, reference: str, 
                                 client_budget: float, estimated_costs: float,
                                 margin: float, profit: float, 
                                 decision: str, reason: str,
                                 suggested_price: float = None) -> int:
        """Log gatekeeper decision for audit trail"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO gatekeeper_log 
            (project_id, reference, client_budget, estimated_costs, 
             estimated_margin, estimated_profit, decision, reason, suggested_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, reference, client_budget, estimated_costs,
              margin, profit, decision, reason, suggested_price))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_project_margin(self, project_id: int, margin: float, 
                               profit: float, verdict: str):
        """Update project with gatekeeper results"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE projects 
            SET estimated_margin = ?, estimated_profit = ?, 
                gatekeeper_verdict = ?, vetted_at = ?
            WHERE id = ?
        ''', (margin, profit, verdict, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), project_id))
        self.conn.commit()
    
    def get_gatekeeper_stats(self) -> Dict:
        """Get gatekeeper statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM gatekeeper_log WHERE decision = 'ACCEPT'")
        accepted = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM gatekeeper_log WHERE decision = 'NEGOTIATE'")
        negotiated = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM gatekeeper_log WHERE decision = 'DECLINE'")
        declined = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(estimated_margin) FROM gatekeeper_log WHERE decision = 'ACCEPT'")
        avg_margin = cursor.fetchone()[0] or 0
        
        return {
            "accepted": accepted,
            "negotiated": negotiated,
            "declined": declined,
            "avg_margin_accepted": round(avg_margin, 1),
            "total_vetted": accepted + negotiated + declined
        }
    
    # === SPECIFICATION METHODS ===
    
    def save_specification(self, project_id: int, requirements: str,
                           fixed_price: float = None) -> int:
        """Save project specification"""
        cursor = self.conn.cursor()
        
        # Get current version
        cursor.execute("SELECT MAX(version) FROM specifications WHERE project_id = ?", (project_id,))
        max_ver = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            INSERT INTO specifications (project_id, version, requirements_json, fixed_price)
            VALUES (?, ?, ?, ?)
        ''', (project_id, max_ver + 1, requirements, fixed_price))
        self.conn.commit()
        return cursor.lastrowid
    
    def approve_specification(self, spec_id: int, fixed_price: float):
        """Approve specification and lock price"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE specifications 
            SET status = 'APPROVED', fixed_price = ?, approved_at = ?
            WHERE id = ?
        ''', (fixed_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), spec_id))
        
        # Update project status
        cursor.execute("SELECT project_id FROM specifications WHERE id = ?", (spec_id,))
        project_id = cursor.fetchone()[0]
        cursor.execute('''
            UPDATE projects 
            SET spec_status = 'APPROVED', spec_approved_at = ?, budget_amount = ?
            WHERE id = ?
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fixed_price, project_id))
        
        self.conn.commit()
    
    def get_specification(self, project_id: int) -> Optional[Dict]:
        """Get latest specification for project"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM specifications 
            WHERE project_id = ? 
            ORDER BY version DESC LIMIT 1
        ''', (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # === CLARIFICATION METHODS ===
    
    def add_clarifying_question(self, project_id: int, question: str) -> int:
        """Add clarifying question"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO clarifications (project_id, question)
            VALUES (?, ?)
        ''', (project_id, question))
        self.conn.commit()
        return cursor.lastrowid
    
    def answer_clarification(self, clarification_id: int, answer: str):
        """Record answer to clarifying question"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE clarifications 
            SET answer = ?, answered_at = ?
            WHERE id = ?
        ''', (answer, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), clarification_id))
        self.conn.commit()
    
    def get_unanswered_questions(self, project_id: int) -> List[Dict]:
        """Get unanswered clarifying questions"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM clarifications 
            WHERE project_id = ? AND answer IS NULL
        ''', (project_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def all_questions_answered(self, project_id: int) -> bool:
        """Check if all questions are answered"""
        unanswered = self.get_unanswered_questions(project_id)
        return len(unanswered) == 0
    
    # === MONTHLY PROFITABILITY REPORT ===
    
    def get_monthly_profitability(self, year: int, month: int) -> Dict:
        """Get profitability report for month"""
        cursor = self.conn.cursor()
        date_pattern = f"{year}-{month:02d}%"
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_projects,
                SUM(budget_amount) as total_revenue,
                AVG(estimated_margin) as avg_margin,
                SUM(estimated_profit) as total_profit,
                AVG(qa_score) as avg_qa
            FROM projects 
            WHERE status = 'PAID' AND paid_at LIKE ?
        ''', (date_pattern,))
        
        row = cursor.fetchone()
        
        return {
            "year": year,
            "month": month,
            "total_projects": row[0] or 0,
            "total_revenue": round(row[1] or 0, 2),
            "avg_margin_percent": round(row[2] or 0, 1),
            "total_profit": round(row[3] or 0, 2),
            "avg_qa_score": round(row[4] or 0, 1)
        }

    def close(self):
        """Закрыть соединение"""
        self.conn.close()


# === MEMORY DB FUNCTIONS (Big Data) ===

def save_to_memory(task: str, result: str, db_path: str = MEMORY_DB):
    """Сохранить в Big Data историю"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS history (date TEXT, task TEXT, output TEXT)')
    cursor.execute("INSERT INTO history VALUES (?, ?, ?)",
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task, str(result)[:5000]))
    conn.commit()
    conn.close()

def get_past_projects(limit: int = 10, db_path: str = MEMORY_DB) -> List[Tuple]:
    """Получить историю проектов"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT date, task, output FROM history ORDER BY date DESC LIMIT ?", (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    except:
        return []

def get_past_errors(db_path: str = MEMORY_DB) -> List[str]:
    """Получить историю ошибок для обучения"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT task, output FROM history 
            WHERE output LIKE '%error%' OR output LIKE '%Error%' OR output LIKE '%ошибка%'
            ORDER BY date DESC LIMIT 10
        ''')
        results = cursor.fetchall()
        conn.close()
        return [f"Task: {r[0][:50]} | Error: {r[1][:100]}" for r in results]
    except:
        return []


# === LEADS DB COMPATIBILITY ===

def get_active_references(db_path: str = LEADS_DB) -> List[str]:
    """Получить активные references для мониторинга"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT wise_ref FROM leads WHERE status != 'paid' AND wise_ref IS NOT NULL")
        refs = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return refs
    except:
        return []


# === INITIALIZATION ===
db = NexusDB()
