# -*- coding: utf-8 -*-
"""
NEXUS 10 AI AGENCY - Automatic Delivery Engine
===============================================
Автоматическая выдача результатов после подтверждения оплаты.
Интегрируется с BlockchainEye и Database.

Author: Nexus 10 AI Agency
"""

import os
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Callable
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
DELIVERY_CHECK_INTERVAL = 60  # seconds
WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)


class DeliveryEngine:
    """
    Автоматическая система доставки.
    Отслеживает оплаченные заказы и выдает результаты клиентам.
    """
    
    def __init__(self, telegram_callback: Callable = None, db = None):
        """
        Args:
            telegram_callback: function(chat_id, message, file_path=None) - для отправки в Telegram
            db: NexusDB instance
        """
        self.telegram_callback = telegram_callback
        self.db = db
        self.running = False
        self._thread = None
        self._pending_deliveries: Dict[str, Dict] = {}  # reference -> order_data
        
    def register_pending_delivery(self, reference: str, order_data: Dict):
        """
        Регистрирует заказ для автоматической выдачи после оплаты.
        
        Args:
            reference: Order reference
            order_data: {
                "chat_id": int,
                "title": str,
                "code_path": str,  # путь к коду
                "client_name": str,
                "amount": float
            }
        """
        self._pending_deliveries[reference] = {
            **order_data,
            "registered_at": datetime.now(),
            "status": "awaiting_payment"
        }
        print(f"[DELIVERY] Registered: {reference} for auto-delivery")
    
    def mark_as_paid(self, reference: str) -> bool:
        """
        Отмечает заказ как оплаченный и запускает доставку.
        
        Returns:
            True если доставка инициирована
        """
        if reference not in self._pending_deliveries:
            print(f"[DELIVERY] Reference not found: {reference}")
            return False
        
        order = self._pending_deliveries[reference]
        order["status"] = "paid"
        order["paid_at"] = datetime.now()
        
        print(f"[DELIVERY] Payment confirmed for {reference}, initiating delivery...")
        
        # Execute delivery
        success = self._execute_delivery(reference, order)
        
        if success:
            order["status"] = "delivered"
            order["delivered_at"] = datetime.now()
            
            # Update database
            if self.db:
                try:
                    self.db.update_order_status(reference, "DELIVERED")
                    self.db.confirm_payment(reference)
                except Exception as e:
                    print(f"[DELIVERY] DB update error: {e}")
            
            # Remove from pending
            del self._pending_deliveries[reference]
        
        return success
    
    def _execute_delivery(self, reference: str, order: Dict) -> bool:
        """Выполняет фактическую доставку"""
        chat_id = order.get("chat_id")
        title = order.get("title", "Project")
        code_path = order.get("code_path")
        client_name = order.get("client_name", "Client")
        
        if not self.telegram_callback:
            print(f"[DELIVERY] No telegram callback configured")
            return False
        
        try:
            # Send confirmation message
            message = f"""
✅ **PAYMENT CONFIRMED**

Thank you, {client_name}!

Your payment for **{title}** has been received and verified.

📦 **Delivering your project now...**

Reference: `{reference}`
"""
            self.telegram_callback(chat_id, message)
            
            # Send files if available
            if code_path and os.path.exists(code_path):
                time.sleep(1)  # Small delay for UX
                
                # Read and send code
                with open(code_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                
                code_message = f"""
📁 **{os.path.basename(code_path)}**

```python
{code_content[:3500]}
```

{'...(truncated, full file attached)' if len(code_content) > 3500 else ''}
"""
                self.telegram_callback(chat_id, code_message)
                
                # Send file
                self.telegram_callback(chat_id, "file", file_path=code_path)
            
            # Send thank you message
            thanks_message = f"""
🎉 **Delivery Complete!**

Your project **{title}** has been delivered successfully.

📋 **What's included:**
• Complete source code
• Documentation
• Setup instructions

🛡️ **Support:**
• 7-day support period active
• Up to 3 revisions included
• Contact via Telegram for assistance

Thank you for choosing **Nexus 10 AI Agency**!
"""
            time.sleep(0.5)
            self.telegram_callback(chat_id, thanks_message)
            
            print(f"[DELIVERY] Successfully delivered: {reference}")
            return True
            
        except Exception as e:
            print(f"[DELIVERY] Error delivering {reference}: {e}")
            return False
    
    def get_pending_count(self) -> int:
        """Количество ожидающих доставки"""
        return len(self._pending_deliveries)
    
    def get_status(self) -> Dict:
        """Статус системы доставки"""
        return {
            "running": self.running,
            "pending_deliveries": self.get_pending_count(),
            "pending_references": list(self._pending_deliveries.keys())
        }
    
    def check_payment_and_deliver(self, reference: str) -> Dict:
        """
        Проверяет оплату через BlockchainEye и выдает результат если оплачено.
        """
        from blockchain_eye import get_blockchain_eye
        
        if reference not in self._pending_deliveries:
            return {"success": False, "message": "Order not found"}
        
        order = self._pending_deliveries[reference]
        amount = order.get("amount", 0)
        
        eye = get_blockchain_eye()
        payment_result = eye.check_payment(amount)
        
        if payment_result["found"]:
            success = self.mark_as_paid(reference)
            return {
                "success": success,
                "message": "Payment confirmed, delivery initiated",
                "tx_hash": payment_result.get("tx_hash")
            }
        
        return {
            "success": False,
            "message": "Payment not yet detected",
            "hint": "Please ensure you sent the exact amount to the correct wallet"
        }


# === INTEGRATION WITH BLOCKCHAIN EYE ===

def setup_auto_delivery(delivery_engine: DeliveryEngine, reference: str, amount: float):
    """
    Настраивает автоматическую доставку после подтверждения оплаты.
    Использует BlockchainEye для мониторинга.
    """
    from blockchain_eye import get_blockchain_eye
    
    eye = get_blockchain_eye()
    
    def on_payment_confirmed(ref: str, tx_data: Dict):
        """Callback при подтверждении платежа"""
        print(f"[AUTO-DELIVERY] Payment confirmed for {ref}")
        print(f"   Tx: {tx_data.get('hash', 'N/A')[:20]}...")
        delivery_engine.mark_as_paid(ref)
    
    # Register with blockchain eye
    eye.register_pending_payment(reference, amount, callback=on_payment_confirmed)
    
    # Ensure monitoring is running
    if not eye.running:
        eye.start_monitoring()
    
    print(f"[AUTO-DELIVERY] Watching for ${amount:.2f} payment to trigger delivery of {reference}")


# === SINGLETON ===

_delivery_engine_instance = None


def get_delivery_engine(telegram_callback: Callable = None, db = None) -> DeliveryEngine:
    """Get or create DeliveryEngine singleton"""
    global _delivery_engine_instance
    if _delivery_engine_instance is None:
        _delivery_engine_instance = DeliveryEngine(telegram_callback, db)
    elif telegram_callback:
        _delivery_engine_instance.telegram_callback = telegram_callback
    if db:
        _delivery_engine_instance.db = db
    return _delivery_engine_instance


# === TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("NEXUS 10 AI AGENCY - Delivery Engine Test")
    print("=" * 60)
    
    # Mock telegram callback
    def mock_telegram(chat_id, message, file_path=None):
        print(f"\n[TELEGRAM -> {chat_id}]")
        if file_path:
            print(f"  File: {file_path}")
        else:
            print(f"  {message[:200]}...")
    
    engine = get_delivery_engine(telegram_callback=mock_telegram)
    
    # Test registration
    test_ref = "NX10-TEST001"
    engine.register_pending_delivery(test_ref, {
        "chat_id": 12345,
        "title": "Test Project",
        "code_path": None,
        "client_name": "Test Client",
        "amount": 100.00
    })
    
    print(f"\nStatus: {engine.get_status()}")
    
    # Simulate payment
    print("\n[Simulating payment confirmation...]")
    engine.mark_as_paid(test_ref)
    
    print(f"\nStatus after delivery: {engine.get_status()}")




