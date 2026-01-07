# -*- coding: utf-8 -*-
"""
NEXUS CORE - Unified Database
==============================
SQLite database for all NEXUS operations.

Tables:
- projects: All projects/orders
- payments: Payment records
- leads: Lead/opportunity tracking
- logs: System logs

Author: NEXUS 10 AI Agency
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

# Default database path
DEFAULT_DB_PATH = os.path.join(os.getcwd(), "nexus_data.db")


class NexusDatabase:
    """
    Unified database for NEXUS 10 operations.
    
    Usage:
        db = NexusDatabase()
        
        # Add project
        project_id = db.add_project("Telegram Bot", 200, "USD")
        
        # Mark as paid
        db.mark_project_paid(project_id, "crypto", "0x123...")
        
        # Get stats
        stats = db.get_stats()
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reference TEXT UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT,
                    client_name TEXT,
                    platform TEXT DEFAULT 'direct',
                    budget REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    status TEXT DEFAULT 'pending',
                    margin_percent REAL,
                    profit REAL,
                    payment_method TEXT,
                    payment_tx TEXT,
                    created_at TEXT,
                    paid_at TEXT,
                    delivered_at TEXT,
                    closed_at TEXT
                )
            ''')
            
            # Payments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    reference TEXT,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    method TEXT,
                    tx_hash TEXT,
                    status TEXT DEFAULT 'pending',
                    confirmed_at TEXT,
                    created_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            ''')
            
            # Leads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    title TEXT,
                    description TEXT,
                    budget_estimate REAL,
                    url TEXT,
                    status TEXT DEFAULT 'new',
                    score INTEGER,
                    created_at TEXT,
                    contacted_at TEXT
                )
            ''')
            
            # Logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT,
                    component TEXT,
                    message TEXT,
                    details TEXT,
                    created_at TEXT
                )
            ''')
    
    # === PROJECTS ===
    
    def add_project(self, title: str, budget: float, currency: str = "USD",
                    description: str = "", client_name: str = "",
                    platform: str = "direct", reference: str = None) -> int:
        """Add new project"""
        if not reference:
            reference = f"NX10-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (reference, title, description, client_name, 
                                      platform, budget, currency, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (reference, title, description, client_name, platform, 
                  budget, currency, datetime.now().isoformat()))
            return cursor.lastrowid
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Get project by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_project_by_reference(self, reference: str) -> Optional[Dict]:
        """Get project by reference"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE reference = ?', (reference,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_project_status(self, project_id: int, status: str):
        """Update project status"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET status = ? WHERE id = ?
            ''', (status, project_id))
    
    def mark_project_paid(self, project_id: int, method: str = "crypto", 
                          tx_hash: str = ""):
        """Mark project as paid"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects 
                SET status = 'paid', payment_method = ?, payment_tx = ?, paid_at = ?
                WHERE id = ?
            ''', (method, tx_hash, datetime.now().isoformat(), project_id))
    
    def mark_project_delivered(self, project_id: int):
        """Mark project as delivered"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET status = 'delivered', delivered_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), project_id))
    
    def update_project_margin(self, project_id: int, margin: float, profit: float,
                              verdict: str = ""):
        """Update project margin analysis"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET margin_percent = ?, profit = ?
                WHERE id = ?
            ''', (margin, profit, project_id))
    
    def get_recent_projects(self, limit: int = 10) -> List[Dict]:
        """Get recent projects"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM projects ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_projects_by_status(self, status: str) -> List[Dict]:
        """Get projects by status"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC
            ''', (status,))
            return [dict(row) for row in cursor.fetchall()]
    
    # === PAYMENTS ===
    
    def add_payment(self, amount: float, currency: str = "USD",
                    method: str = "crypto", reference: str = None,
                    project_id: int = None) -> int:
        """Record a payment"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (project_id, reference, amount, currency, 
                                      method, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (project_id, reference, amount, currency, method, 
                  datetime.now().isoformat()))
            return cursor.lastrowid
    
    def confirm_payment(self, payment_id: int, tx_hash: str = ""):
        """Confirm a payment"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE payments SET status = 'confirmed', tx_hash = ?, confirmed_at = ?
                WHERE id = ?
            ''', (tx_hash, datetime.now().isoformat(), payment_id))
    
    # === LEADS ===
    
    def add_lead(self, title: str, source: str = "direct", 
                 description: str = "", budget_estimate: float = 0,
                 url: str = "", score: int = 0) -> int:
        """Add new lead"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leads (source, title, description, budget_estimate, 
                                   url, score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (source, title, description, budget_estimate, url, score,
                  datetime.now().isoformat()))
            return cursor.lastrowid
    
    def get_recent_leads(self, limit: int = 20) -> List[Dict]:
        """Get recent leads"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM leads ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_lead_status(self, lead_id: int, status: str):
        """Update lead status"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE leads SET status = ? WHERE id = ?
            ''', (status, lead_id))
    
    # === LOGS ===
    
    def log(self, message: str, level: str = "INFO", 
            component: str = "SYSTEM", details: str = ""):
        """Add log entry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs (level, component, message, details, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (level, component, message, details, datetime.now().isoformat()))
    
    def log_gatekeeper_decision(self, project_id: int, reference: str,
                                 client_budget: float, estimated_costs: float,
                                 margin: float, profit: float, decision: str,
                                 reason: str, suggested_price: float = None):
        """Log gatekeeper decision"""
        details = f"Budget: ${client_budget}, Costs: ${estimated_costs}, " \
                  f"Margin: {margin}%, Profit: ${profit}"
        if suggested_price:
            details += f", Suggested: ${suggested_price}"
        
        self.log(
            message=f"[{decision}] {reason}",
            level="INFO" if decision == "ACCEPT" else "WARN",
            component="GATEKEEPER",
            details=details
        )
    
    # === STATS ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM projects')
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'paid'")
            paid = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'delivered'")
            delivered = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(budget) FROM projects WHERE status IN ('paid', 'delivered')")
            total_revenue = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(profit) FROM projects WHERE profit IS NOT NULL")
            total_profit = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM leads')
            total_leads = cursor.fetchone()[0]
            
            return {
                "total_projects": total,
                "paid": paid,
                "pending": pending,
                "delivered": delivered,
                "total_revenue": round(total_revenue, 2),
                "total_profit": round(total_profit, 2),
                "total_leads": total_leads
            }
    
    def get_total_earnings(self) -> List[tuple]:
        """Get earnings by currency"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT currency, SUM(budget) as total 
                FROM projects 
                WHERE status IN ('paid', 'delivered')
                GROUP BY currency
            ''')
            return cursor.fetchall()


# === SINGLETON ===
_db_instance: Optional[NexusDatabase] = None


def get_database() -> NexusDatabase:
    """Get or create database singleton"""
    global _db_instance
    if _db_instance is None:
        _db_instance = NexusDatabase()
    return _db_instance


# === QUICK FUNCTIONS ===

def add_project(title: str, budget: float, **kwargs) -> int:
    """Quick add project"""
    return get_database().add_project(title, budget, **kwargs)


def get_stats() -> Dict:
    """Quick get stats"""
    return get_database().get_stats()


def log_action(message: str, component: str = "SYSTEM"):
    """Quick log"""
    get_database().log(message, component=component)

