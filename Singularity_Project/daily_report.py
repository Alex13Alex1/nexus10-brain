# -*- coding: utf-8 -*-
"""
DAILY REPORT SYSTEM - Automated earnings reports
=================================================
Generates and sends daily financial reports via Telegram
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Database paths
DB_DIR = os.path.join(os.getcwd(), 'data')
BUSINESS_DB = os.path.join(DB_DIR, 'nexus_business.db')
ORDERS_DB = os.path.join(DB_DIR, 'orders.db')


def get_daily_earnings(days: int = 1) -> Dict:
    """Get earnings for last N days"""
    try:
        conn = sqlite3.connect(BUSINESS_DB)
        cursor = conn.cursor()
        
        # Calculate date threshold
        threshold = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get earnings by currency
        cursor.execute("""
            SELECT budget_currency, SUM(budget_amount), COUNT(*) 
            FROM projects 
            WHERE status = 'PAID' AND paid_at >= ?
            GROUP BY budget_currency
        """, (threshold,))
        
        earnings = {}
        total_projects = 0
        for row in cursor.fetchall():
            currency, amount, count = row
            earnings[currency] = {"amount": amount or 0, "count": count}
            total_projects += count
        
        # Get pending projects
        cursor.execute("""
            SELECT COUNT(*), SUM(budget_amount) 
            FROM projects 
            WHERE status = 'PENDING'
        """)
        pending_row = cursor.fetchone()
        pending_count = pending_row[0] or 0
        pending_value = pending_row[1] or 0
        
        conn.close()
        
        return {
            "success": True,
            "period_days": days,
            "earnings": earnings,
            "total_projects": total_projects,
            "pending_count": pending_count,
            "pending_value": pending_value
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_orders_stats(days: int = 1) -> Dict:
    """Get order execution stats"""
    try:
        conn = sqlite3.connect(ORDERS_DB)
        cursor = conn.cursor()
        
        threshold = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Orders by status
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM orders 
            WHERE created_at >= ?
            GROUP BY status
        """, (threshold,))
        
        by_status = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average QA score
        cursor.execute("""
            SELECT AVG(qa_score) 
            FROM orders 
            WHERE qa_score IS NOT NULL AND created_at >= ?
        """, (threshold,))
        
        avg_qa = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "success": True,
            "by_status": by_status,
            "avg_qa_score": round(avg_qa, 1),
            "total_orders": sum(by_status.values())
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_daily_report() -> str:
    """Generate formatted daily report"""
    earnings = get_daily_earnings(days=1)
    orders = get_orders_stats(days=1)
    
    report = """📊 **NEXUS-6 DAILY REPORT**
━━━━━━━━━━━━━━━━━━━━━━━━
📅 {}

""".format(datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    # Earnings section
    if earnings.get("success"):
        report += "💰 **EARNINGS (Last 24h):**\n"
        
        total_usd = 0
        for currency, data in earnings.get("earnings", {}).items():
            amount = data.get("amount", 0)
            count = data.get("count", 0)
            report += "   • {} {:.2f} ({} projects)\n".format(currency, amount, count)
            
            # Convert to USD for total
            if currency == "USD":
                total_usd += amount
            elif currency == "EUR":
                total_usd += amount * 1.09
        
        if total_usd > 0:
            report += "\n   **Total: ~${:.2f} USD**\n".format(total_usd)
        else:
            report += "   No paid projects today\n"
        
        report += "\n   📋 Pending: {} projects (${:.0f})\n".format(
            earnings.get("pending_count", 0),
            earnings.get("pending_value", 0)
        )
    else:
        report += "❌ Earnings data unavailable\n"
    
    report += "\n"
    
    # Orders section
    if orders.get("success"):
        report += "📦 **ORDERS (Last 24h):**\n"
        
        status_emoji = {
            "found": "🔍", "proposal": "📤", "in_progress": "⚙️",
            "ready": "📦", "delivered": "🚀", "paid": "💰"
        }
        
        by_status = orders.get("by_status", {})
        for status, count in by_status.items():
            emoji = status_emoji.get(status, "•")
            report += "   {} {}: {}\n".format(emoji, status.upper(), count)
        
        report += "\n   📊 Total: {} orders\n".format(orders.get("total_orders", 0))
        report += "   ✅ Avg QA Score: {}/100\n".format(orders.get("avg_qa_score", 0))
    
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━
🤖 NEXUS-6 Autonomous System"""
    
    return report


def generate_weekly_report() -> str:
    """Generate weekly summary"""
    earnings = get_daily_earnings(days=7)
    orders = get_orders_stats(days=7)
    
    report = """📊 **NEXUS-6 WEEKLY REPORT**
━━━━━━━━━━━━━━━━━━━━━━━━
📅 Week ending: {}

""".format(datetime.now().strftime("%Y-%m-%d"))
    
    if earnings.get("success"):
        report += "💰 **WEEKLY EARNINGS:**\n"
        
        total_usd = 0
        for currency, data in earnings.get("earnings", {}).items():
            amount = data.get("amount", 0)
            count = data.get("count", 0)
            report += "   • {} {:.2f} ({} projects)\n".format(currency, amount, count)
            if currency == "USD":
                total_usd += amount
            elif currency == "EUR":
                total_usd += amount * 1.09
        
        report += "\n   **Weekly Total: ~${:.2f} USD**\n".format(total_usd)
        report += "   📈 Daily Avg: ~${:.2f}\n".format(total_usd / 7 if total_usd > 0 else 0)
    
    if orders.get("success"):
        report += "\n📦 **WEEKLY ORDERS:**\n"
        report += "   Total: {}\n".format(orders.get("total_orders", 0))
        report += "   Avg QA: {}/100\n".format(orders.get("avg_qa_score", 0))
    
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━
🤖 NEXUS-6 Autonomous System"""
    
    return report


# Telegram notification helper
_notify_callback = None

def set_notify_callback(callback):
    """Set Telegram notification callback"""
    global _notify_callback
    _notify_callback = callback


def send_daily_report():
    """Send daily report via Telegram"""
    report = generate_daily_report()
    
    if _notify_callback:
        try:
            _notify_callback(report)
            return True
        except Exception as e:
            print("Failed to send report:", e)
            return False
    else:
        print(report)
        return True


# Test
if __name__ == "__main__":
    print(generate_daily_report())
    print("\n" + "=" * 50 + "\n")
    print(generate_weekly_report())









