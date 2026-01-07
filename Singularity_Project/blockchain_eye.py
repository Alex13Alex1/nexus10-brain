# -*- coding: utf-8 -*-
"""
NEXUS 10 AI AGENCY - Blockchain Eye
===================================
Автономный мониторинг платежей на блокчейне Polygon.
Проверяет входящие USDT/USDC транзакции и автоматически
обновляет статус заказов.

Author: Nexus 10 AI Agency
"""

import os
import time
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
POLYGONSCAN_API_KEY = os.getenv("POLYGONSCAN_API_KEY", "")
MY_WALLET = os.getenv("MY_CRYPTO_WALLET", "").lower()
POLYGONSCAN_URL = "https://api.polygonscan.com/api"

# Token contracts on Polygon
TOKENS = {
    "USDT": {
        "contract": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
        "decimals": 6
    },
    "USDC": {
        "contract": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174", 
        "decimals": 6
    }
}

# Monitoring settings
CHECK_INTERVAL_SECONDS = 300  # 5 minutes
TOLERANCE_PERCENT = 2.0  # 2% tolerance for amount matching


class BlockchainEye:
    """
    Автономный блокчейн-монитор для Nexus 10 AI Agency.
    Отслеживает входящие крипто-платежи и триггерит callback при подтверждении.
    """
    
    def __init__(self):
        self.wallet = MY_WALLET
        self.api_key = POLYGONSCAN_API_KEY
        self.running = False
        self._thread = None
        self._pending_payments: Dict[str, Dict] = {}  # reference -> {amount, callback, token}
        self._confirmed_hashes: set = set()
        
        if not self.wallet:
            print("[BLOCKCHAIN EYE] WARNING: MY_CRYPTO_WALLET not configured")
        if not self.api_key:
            print("[BLOCKCHAIN EYE] WARNING: POLYGONSCAN_API_KEY not configured")
    
    def _api_request(self, params: Dict) -> Optional[Dict]:
        """Execute Polygonscan API request"""
        if not self.api_key:
            return None
        
        full_params = {
            "apikey": self.api_key,
            **params
        }
        
        try:
            response = requests.get(POLYGONSCAN_URL, params=full_params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[BLOCKCHAIN EYE] API Error: {e}")
            return None
    
    def get_recent_token_transactions(self, token: str = "USDT", limit: int = 50) -> List[Dict]:
        """Get recent incoming token transactions"""
        if not self.wallet:
            return []
        
        token_info = TOKENS.get(token.upper())
        if not token_info:
            return []
        
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": token_info["contract"],
            "address": self.wallet,
            "sort": "desc",
            "page": 1,
            "offset": limit
        }
        
        response = self._api_request(params)
        
        if response and response.get("status") == "1":
            incoming_txs = []
            for tx in response.get("result", []):
                # Only incoming transactions
                if tx.get("to", "").lower() == self.wallet:
                    value_raw = int(tx.get("value", "0"))
                    decimals = int(tx.get("tokenDecimal", "6"))
                    amount = value_raw / (10 ** decimals)
                    
                    incoming_txs.append({
                        "hash": tx.get("hash"),
                        "from": tx.get("from"),
                        "to": tx.get("to"),
                        "amount": amount,
                        "token": tx.get("tokenSymbol", token),
                        "timestamp": datetime.fromtimestamp(int(tx.get("timeStamp", "0"))),
                        "block": tx.get("blockNumber")
                    })
            return incoming_txs
        
        return []
    
    def check_payment(self, expected_amount: float, token: str = "USDT",
                      time_window_hours: int = 24) -> Dict:
        """
        Check for a specific payment amount.
        
        Args:
            expected_amount: Expected payment in USD
            token: USDT or USDC
            time_window_hours: How far back to look
        
        Returns:
            {"found": bool, "tx_hash": str or None, "actual_amount": float}
        """
        if not self.wallet or not self.api_key:
            return {"found": False, "tx_hash": None, "message": "Not configured"}
        
        min_amount = expected_amount * (1 - TOLERANCE_PERCENT / 100)
        max_amount = expected_amount * (1 + TOLERANCE_PERCENT / 100)
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        # Check both USDT and USDC if token is generic
        tokens_to_check = [token.upper()] if token.upper() in TOKENS else ["USDT", "USDC"]
        
        for check_token in tokens_to_check:
            transactions = self.get_recent_token_transactions(check_token, limit=100)
            
            for tx in transactions:
                if (min_amount <= tx["amount"] <= max_amount and
                    tx["timestamp"] >= cutoff_time and
                    tx["hash"] not in self._confirmed_hashes):
                    
                    self._confirmed_hashes.add(tx["hash"])
                    
                    return {
                        "found": True,
                        "tx_hash": tx["hash"],
                        "actual_amount": tx["amount"],
                        "token": tx["token"],
                        "from_address": tx["from"],
                        "timestamp": tx["timestamp"].isoformat(),
                        "message": f"Payment of {tx['amount']:.2f} {tx['token']} confirmed!"
                    }
        
        return {
            "found": False,
            "tx_hash": None,
            "message": f"No matching payment found for ${expected_amount:.2f}"
        }
    
    def register_pending_payment(self, reference: str, amount: float,
                                  callback: Callable = None, token: str = "USDT"):
        """
        Register a payment to watch for.
        
        Args:
            reference: Order reference (unique ID)
            amount: Expected amount in USD
            callback: Function to call when payment confirmed: callback(reference, tx_data)
            token: Expected token (USDT/USDC)
        """
        self._pending_payments[reference] = {
            "amount": amount,
            "token": token,
            "callback": callback,
            "registered_at": datetime.now()
        }
        print(f"[BLOCKCHAIN EYE] Watching for payment: {reference} = ${amount:.2f} {token}")
    
    def unregister_payment(self, reference: str):
        """Stop watching for a payment"""
        if reference in self._pending_payments:
            del self._pending_payments[reference]
            print(f"[BLOCKCHAIN EYE] Stopped watching: {reference}")
    
    def _check_all_pending(self):
        """Check all pending payments (internal loop)"""
        if not self._pending_payments:
            return
        
        # Get all recent transactions
        all_txs = []
        for token in TOKENS.keys():
            txs = self.get_recent_token_transactions(token, limit=50)
            all_txs.extend(txs)
        
        # Match against pending
        cutoff = datetime.now() - timedelta(hours=48)
        confirmed = []
        
        for ref, payment_info in self._pending_payments.items():
            expected = payment_info["amount"]
            min_amt = expected * 0.98
            max_amt = expected * 1.02
            
            for tx in all_txs:
                if (min_amt <= tx["amount"] <= max_amt and
                    tx["timestamp"] >= cutoff and
                    tx["hash"] not in self._confirmed_hashes):
                    
                    self._confirmed_hashes.add(tx["hash"])
                    confirmed.append((ref, tx))
                    
                    # Trigger callback
                    if payment_info.get("callback"):
                        try:
                            payment_info["callback"](ref, tx)
                        except Exception as e:
                            print(f"[BLOCKCHAIN EYE] Callback error for {ref}: {e}")
                    
                    print(f"[BLOCKCHAIN EYE] PAYMENT CONFIRMED: {ref}")
                    print(f"   Amount: {tx['amount']:.2f} {tx['token']}")
                    print(f"   Hash: {tx['hash'][:20]}...")
                    break
        
        # Remove confirmed from pending
        for ref, _ in confirmed:
            self.unregister_payment(ref)
    
    def _monitoring_loop(self):
        """Background monitoring thread"""
        print(f"[BLOCKCHAIN EYE] Monitoring started (every {CHECK_INTERVAL_SECONDS}s)")
        
        while self.running:
            try:
                self._check_all_pending()
            except Exception as e:
                print(f"[BLOCKCHAIN EYE] Loop error: {e}")
            
            # Sleep in small increments for faster shutdown
            for _ in range(CHECK_INTERVAL_SECONDS):
                if not self.running:
                    break
                time.sleep(1)
        
        print("[BLOCKCHAIN EYE] Monitoring stopped")
    
    def start_monitoring(self):
        """Start background payment monitoring"""
        if self.running:
            print("[BLOCKCHAIN EYE] Already running")
            return
        
        if not self.wallet or not self.api_key:
            print("[BLOCKCHAIN EYE] Cannot start: missing wallet or API key")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "running": self.running,
            "wallet_configured": bool(self.wallet),
            "api_configured": bool(self.api_key),
            "pending_payments": len(self._pending_payments),
            "confirmed_count": len(self._confirmed_hashes),
            "pending_list": list(self._pending_payments.keys())
        }
    
    def get_balance_24h(self) -> Dict:
        """Get total received in last 24 hours"""
        total_usdt = 0.0
        total_usdc = 0.0
        cutoff = datetime.now() - timedelta(hours=24)
        
        for token in ["USDT", "USDC"]:
            txs = self.get_recent_token_transactions(token, limit=100)
            for tx in txs:
                if tx["timestamp"] >= cutoff:
                    if token == "USDT":
                        total_usdt += tx["amount"]
                    else:
                        total_usdc += tx["amount"]
        
        return {
            "USDT": round(total_usdt, 2),
            "USDC": round(total_usdc, 2),
            "total": round(total_usdt + total_usdc, 2),
            "period": "24h"
        }


# === SINGLETON INSTANCE ===
_blockchain_eye_instance = None


def get_blockchain_eye() -> BlockchainEye:
    """Get or create BlockchainEye singleton"""
    global _blockchain_eye_instance
    if _blockchain_eye_instance is None:
        _blockchain_eye_instance = BlockchainEye()
    return _blockchain_eye_instance


# === QUICK FUNCTIONS (for agents) ===

def check_crypto_payment(expected_amount: float, target_address: str = None) -> tuple:
    """
    Quick check for crypto payment.
    Returns: (found: bool, tx_hash: str or None)
    """
    eye = get_blockchain_eye()
    result = eye.check_payment(expected_amount)
    return result["found"], result.get("tx_hash")


def watch_for_payment(reference: str, amount: float, callback: Callable = None):
    """Register a payment to watch"""
    eye = get_blockchain_eye()
    eye.register_pending_payment(reference, amount, callback)


def start_blockchain_monitor():
    """Start the blockchain monitoring service"""
    eye = get_blockchain_eye()
    eye.start_monitoring()


def stop_blockchain_monitor():
    """Stop the blockchain monitoring service"""
    eye = get_blockchain_eye()
    eye.stop_monitoring()


def get_crypto_balance() -> Dict:
    """Get 24h crypto balance"""
    eye = get_blockchain_eye()
    return eye.get_balance_24h()


# === TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("NEXUS 10 AI AGENCY - Blockchain Eye Test")
    print("=" * 60)
    
    eye = get_blockchain_eye()
    
    # Status check
    status = eye.get_status()
    print(f"\nStatus:")
    print(f"  Wallet configured: {status['wallet_configured']}")
    print(f"  API configured: {status['api_configured']}")
    print(f"  Running: {status['running']}")
    
    if status['wallet_configured'] and status['api_configured']:
        # Test transaction fetch
        print(f"\nFetching recent USDT transactions...")
        txs = eye.get_recent_token_transactions("USDT", limit=5)
        print(f"Found {len(txs)} incoming transactions")
        
        for tx in txs[:3]:
            print(f"  - {tx['amount']:.2f} {tx['token']} from {tx['from'][:10]}...")
        
        # Test balance
        print(f"\n24h Balance:")
        balance = eye.get_balance_24h()
        print(f"  USDT: ${balance['USDT']:.2f}")
        print(f"  USDC: ${balance['USDC']:.2f}")
        print(f"  Total: ${balance['total']:.2f}")
        
        # Test payment check
        print(f"\nTesting payment check for $100...")
        result = eye.check_payment(100)
        print(f"  Found: {result['found']}")
        print(f"  Message: {result['message']}")
    else:
        print("\n[SKIP] Configure wallet and API key to test")
    
    print("\n" + "=" * 60)








