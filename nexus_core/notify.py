# -*- coding: utf-8 -*-
"""
NEXUS CORE - Telegram Notifier
===============================
Simple Telegram notifications for system events.

Author: NEXUS 10 AI Agency
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")


class TelegramNotifier:
    """
    Send notifications to Telegram.
    
    Usage:
        notifier = TelegramNotifier()
        notifier.send("Hello, World!")
        notifier.send_payment_confirmed("NX10-123", 100.00)
    """
    
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or ADMIN_CHAT_ID
        self._enabled = bool(self.token and self.chat_id)
        
        if not self._enabled:
            print("[NOTIFY] Telegram not configured (missing token or chat_id)")
    
    def send(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message to Telegram.
        
        Args:
            message: Message text
            parse_mode: Markdown or HTML
            
        Returns:
            True if sent successfully
        """
        if not self._enabled:
            print(f"[NOTIFY] (disabled) {message[:50]}...")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"[NOTIFY] Error: {e}")
            return False
    
    def send_html(self, message: str) -> bool:
        """Send HTML formatted message"""
        return self.send(message, parse_mode="HTML")
    
    def send_payment_confirmed(self, reference: str, amount: float, 
                                method: str = "crypto", tx_hash: str = None) -> bool:
        """Send payment confirmation notification"""
        msg = f"""💰 *PAYMENT CONFIRMED*

Reference: `{reference}`
Amount: *${amount:.2f}*
Method: {method}
"""
        if tx_hash:
            msg += f"TX: `{tx_hash[:20]}...`"
        
        return self.send(msg)
    
    def send_new_lead(self, title: str, budget: float, 
                      platform: str = "direct") -> bool:
        """Send new lead notification"""
        msg = f"""📥 *NEW LEAD*

Title: {title}
Budget: *${budget:.2f}*
Platform: {platform}
"""
        return self.send(msg)
    
    def send_project_delivered(self, title: str, client: str) -> bool:
        """Send delivery notification"""
        msg = f"""📦 *PROJECT DELIVERED*

Project: {title}
Client: {client}
Status: ✅ Delivered
"""
        return self.send(msg)
    
    def send_error(self, error_msg: str, context: str = "") -> bool:
        """Send error notification"""
        msg = f"""🚨 *SYSTEM ERROR*

Error: {error_msg[:200]}
"""
        if context:
            msg += f"Context: {context[:100]}"
        
        return self.send(msg)
    
    def send_daily_report(self, projects: int, revenue: float, 
                          pending: int = 0) -> bool:
        """Send daily report"""
        msg = f"""📊 *DAILY REPORT*

Projects Completed: {projects}
Revenue: *${revenue:.2f}*
Pending: {pending}
"""
        return self.send(msg)
    
    def is_enabled(self) -> bool:
        """Check if notifications are enabled"""
        return self._enabled
    
    def set_chat_id(self, chat_id: str):
        """Update chat ID (useful for dynamic admin detection)"""
        self.chat_id = chat_id
        self._enabled = bool(self.token and self.chat_id)


# === SINGLETON ===
_notifier_instance: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    """Get or create notifier singleton"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier()
    return _notifier_instance


# === QUICK FUNCTIONS ===

def notify(message: str) -> bool:
    """Quick notification"""
    return get_notifier().send(message)


def notify_payment(reference: str, amount: float, method: str = "crypto") -> bool:
    """Quick payment notification"""
    return get_notifier().send_payment_confirmed(reference, amount, method)


def notify_error(error: str) -> bool:
    """Quick error notification"""
    return get_notifier().send_error(error)


def notify_lead(title: str, budget: float) -> bool:
    """Quick lead notification"""
    return get_notifier().send_new_lead(title, budget)


