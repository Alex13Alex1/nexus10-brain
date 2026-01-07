# -*- coding: utf-8 -*-
"""
NEXUS CORE - Blockchain Eye
============================
Autonomous payment monitoring on Polygon blockchain.
Checks incoming USDT/USDC transactions and auto-updates order status.

Ported from: Singularity_Project/blockchain_eye.py
Author: NEXUS 10 AI Agency
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

CHECK_INTERVAL_SECONDS = 300  # 5 minutes
TOLERANCE_PERCENT = 2.0  # 2% tolerance for amount matching


class BlockchainEye:
    """
    Autonomous blockchain monitor for crypto payments.
    Tracks incoming payments and triggers callback on confirmation.
    """
    
    def __init__(self, wallet: str = None, api_key: str = None):
        self.wallet = (wallet or MY_WALLET).lower() if (wallet or MY_WALLET) else ""
        self.api_key = api_key or POLYGONSCAN_API_KEY
        self.running = False
        self._thread = None
        self._pending_payments: Dict[str, Dict] = {}
        self._confirmed_hashes: set = set()
    
    def _api_request(self, params: Dict) -> Optional[Dict]:
        """Execute Polygonscan API request"""
        if not self.api_key:
            return None
        
        full_params = {"apikey": self.api_key, **params}
        
        try:
            response = requests.get(POLYGONSCAN_URL, params=full_params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[BLOCKCHAIN] API Error: {e}")
            return None
    
    def get_recent_transactions(self, token: str = "USDT", limit: int = 50) -> List[Dict]:
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
        
        Returns:
            {"found": bool, "tx_hash": str or None, "actual_amount": float}
        """
        if not self.wallet or not self.api_key:
            return {"found": False, "tx_hash": None, "message": "Not configured"}
        
        min_amount = expected_amount * (1 - TOLERANCE_PERCENT / 100)
        max_amount = expected_amount * (1 + TOLERANCE_PERCENT / 100)
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        tokens_to_check = [token.upper()] if token.upper() in TOKENS else ["USDT", "USDC"]
        
        for check_token in tokens_to_check:
            transactions = self.get_recent_transactions(check_token, limit=100)
            
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
        """Register a payment to watch for."""
        self._pending_payments[reference] = {
            "amount": amount,
            "token": token,
            "callback": callback,
            "registered_at": datetime.now()
        }
        print(f"[BLOCKCHAIN] Watching: {reference} = ${amount:.2f} {token}")
    
    def unregister_payment(self, reference: str):
        """Stop watching for a payment"""
        if reference in self._pending_payments:
            del self._pending_payments[reference]
    
    def _check_all_pending(self):
        """Check all pending payments"""
        if not self._pending_payments:
            return
        
        all_txs = []
        for token in TOKENS.keys():
            txs = self.get_recent_transactions(token, limit=50)
            all_txs.extend(txs)
        
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
                    
                    if payment_info.get("callback"):
                        try:
                            payment_info["callback"](ref, tx)
                        except Exception as e:
                            print(f"[BLOCKCHAIN] Callback error: {e}")
                    
                    print(f"[BLOCKCHAIN] CONFIRMED: {ref} - {tx['amount']:.2f} {tx['token']}")
                    break
        
        for ref, _ in confirmed:
            self.unregister_payment(ref)
    
    def _monitoring_loop(self):
        """Background monitoring thread"""
        while self.running:
            try:
                self._check_all_pending()
            except Exception as e:
                print(f"[BLOCKCHAIN] Loop error: {e}")
            
            for _ in range(CHECK_INTERVAL_SECONDS):
                if not self.running:
                    break
                time.sleep(1)
    
    def start_monitoring(self):
        """Start background payment monitoring"""
        if self.running:
            return
        
        if not self.wallet or not self.api_key:
            print("[BLOCKCHAIN] Cannot start: missing wallet or API key")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        print(f"[BLOCKCHAIN] Monitoring started (every {CHECK_INTERVAL_SECONDS}s)")
    
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
            txs = self.get_recent_transactions(token, limit=100)
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


# === SINGLETON ===
_blockchain_eye_instance = None

def get_blockchain_eye() -> BlockchainEye:
    """Get or create BlockchainEye singleton"""
    global _blockchain_eye_instance
    if _blockchain_eye_instance is None:
        _blockchain_eye_instance = BlockchainEye()
    return _blockchain_eye_instance


# === QUICK FUNCTIONS ===

def check_crypto_payment(expected_amount: float, wallet: str = None) -> tuple:
    """Quick check for crypto payment. Returns: (found, tx_hash)"""
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



