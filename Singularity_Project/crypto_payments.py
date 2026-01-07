# -*- coding: utf-8 -*-
"""
NEXUS-6 CRYPTO PAYMENTS v1.0
=============================
Верификация платежей USDC/USDT на Polygon Network.
Мониторинг входящих транзакций.

Author: NEXUS-6 AI System
"""

import os
import time
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
MY_WALLET = os.getenv("MY_CRYPTO_WALLET", "")
POLYGONSCAN_API_KEY = os.getenv("POLYGONSCAN_API_KEY", "")

# Token contracts on Polygon
TOKEN_CONTRACTS = {
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # Polygon USDT
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # Polygon USDC
    "USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # Bridged USDC
}

# Decimals for tokens
TOKEN_DECIMALS = {
    "USDT": 6,
    "USDC": 6,
    "USDC.e": 6,
}

# State
_watcher_running = False
_watcher_thread = None
_notify_callback = None
_pending_payments = {}  # reference -> {amount, token, timestamp}


@dataclass
class CryptoPayment:
    """Крипто-платёж"""
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    token: str
    timestamp: datetime
    block_number: int
    confirmed: bool = True


class CryptoPaymentVerifier:
    """
    Верификатор крипто-платежей на Polygon.
    Проверяет входящие USDC/USDT транзакции.
    """
    
    def __init__(self, wallet: str = None, api_key: str = None):
        self.wallet = (wallet or MY_WALLET).lower()
        self.api_key = api_key or POLYGONSCAN_API_KEY
        self.base_url = "https://api.polygonscan.com/api"
        
        if not self.wallet:
            print("[CRYPTO] WARNING: No wallet address configured")
        if not self.api_key:
            print("[CRYPTO] WARNING: No Polygonscan API key - using limited mode")
    
    def get_token_transactions(self, token: str = "USDT", 
                               limit: int = 50) -> List[CryptoPayment]:
        """
        Получает последние токен-транзакции на кошелёк.
        
        Args:
            token: USDT, USDC, or USDC.e
            limit: Максимум транзакций
        
        Returns:
            Список CryptoPayment
        """
        if not self.wallet:
            return []
        
        contract = TOKEN_CONTRACTS.get(token.upper())
        if not contract:
            print(f"[CRYPTO] Unknown token: {token}")
            return []
        
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": contract,
            "address": self.wallet,
            "page": 1,
            "offset": limit,
            "sort": "desc"
        }
        
        if self.api_key:
            params["apikey"] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") != "1":
                # No transactions or error
                return []
            
            payments = []
            decimals = TOKEN_DECIMALS.get(token.upper(), 6)
            
            for tx in data.get("result", []):
                # Только входящие транзакции
                if tx.get("to", "").lower() != self.wallet:
                    continue
                
                amount = int(tx.get("value", 0)) / (10 ** decimals)
                
                payments.append(CryptoPayment(
                    tx_hash=tx.get("hash", ""),
                    from_address=tx.get("from", ""),
                    to_address=tx.get("to", ""),
                    amount=amount,
                    token=tx.get("tokenSymbol", token),
                    timestamp=datetime.fromtimestamp(int(tx.get("timeStamp", 0))),
                    block_number=int(tx.get("blockNumber", 0)),
                    confirmed=True
                ))
            
            return payments
            
        except Exception as e:
            print(f"[CRYPTO] Error fetching transactions: {e}")
            return []
    
    def verify_payment(self, expected_amount: float, 
                      token: str = "USDT",
                      tolerance: float = 0.02,
                      since_minutes: int = 60) -> Dict:
        """
        Проверяет получение платежа.
        
        Args:
            expected_amount: Ожидаемая сумма в USD
            token: USDT или USDC
            tolerance: Допуск (2% по умолчанию для курсовых колебаний)
            since_minutes: Искать за последние N минут
        
        Returns:
            Dict с результатом проверки
        """
        result = {
            "found": False,
            "amount": 0,
            "token": token,
            "tx_hash": None,
            "from_address": None,
            "message": "Платёж не найден"
        }
        
        payments = self.get_token_transactions(token, limit=20)
        
        if not payments:
            # Пробуем другой токен
            alt_token = "USDC" if token == "USDT" else "USDT"
            payments = self.get_token_transactions(alt_token, limit=20)
            if payments:
                token = alt_token
        
        min_amount = expected_amount * (1 - tolerance)
        max_amount = expected_amount * (1 + tolerance)
        cutoff_time = datetime.now().timestamp() - (since_minutes * 60)
        
        for payment in payments:
            # Проверяем время
            if payment.timestamp.timestamp() < cutoff_time:
                continue
            
            # Проверяем сумму
            if min_amount <= payment.amount <= max_amount:
                result["found"] = True
                result["amount"] = payment.amount
                result["token"] = payment.token
                result["tx_hash"] = payment.tx_hash
                result["from_address"] = payment.from_address
                result["timestamp"] = payment.timestamp.isoformat()
                result["message"] = f"✅ Платёж {payment.amount} {payment.token} подтверждён!"
                break
        
        return result
    
    def verify_payment_by_reference(self, reference: str,
                                    expected_amount: float,
                                    token: str = "USDT") -> Dict:
        """
        Проверяет платёж по референсу (ищет в memo или точную сумму).
        Поскольку Polygon не поддерживает memo, используем точную сумму.
        """
        # Добавляем небольшое уникальное число к сумме для идентификации
        # Например: $100.37 вместо $100.00
        unique_suffix = hash(reference) % 100 / 100
        exact_amount = expected_amount + unique_suffix
        
        return self.verify_payment(exact_amount, token, tolerance=0.005)  # 0.5% tolerance
    
    def get_recent_payments(self, hours: int = 24) -> List[CryptoPayment]:
        """Получить все платежи за последние N часов"""
        all_payments = []
        
        for token in ["USDT", "USDC"]:
            payments = self.get_token_transactions(token, limit=50)
            
            cutoff = datetime.now().timestamp() - (hours * 3600)
            for p in payments:
                if p.timestamp.timestamp() >= cutoff:
                    all_payments.append(p)
        
        # Сортируем по времени (новые первые)
        all_payments.sort(key=lambda x: x.timestamp, reverse=True)
        return all_payments
    
    def get_total_received(self, hours: int = 24) -> Dict[str, float]:
        """Общая сумма полученных платежей за период"""
        payments = self.get_recent_payments(hours)
        
        totals = {"USDT": 0, "USDC": 0, "total_usd": 0}
        
        for p in payments:
            if p.token in totals:
                totals[p.token] += p.amount
            totals["total_usd"] += p.amount
        
        return totals


# === PAYMENT WATCHER ===

def register_pending_payment(reference: str, amount: float, token: str = "USDT"):
    """Регистрирует ожидаемый платёж для мониторинга"""
    global _pending_payments
    _pending_payments[reference] = {
        "amount": amount,
        "token": token,
        "timestamp": datetime.now().isoformat(),
        "verified": False
    }
    print(f"[CRYPTO] Registered pending payment: {reference} - ${amount} {token}")


def check_pending_payments() -> List[Dict]:
    """Проверяет все ожидающие платежи"""
    global _pending_payments
    verified = []
    
    verifier = CryptoPaymentVerifier()
    
    for ref, data in list(_pending_payments.items()):
        if data.get("verified"):
            continue
        
        result = verifier.verify_payment(
            expected_amount=data["amount"],
            token=data["token"],
            since_minutes=120  # 2 часа
        )
        
        if result["found"]:
            data["verified"] = True
            data["tx_hash"] = result["tx_hash"]
            verified.append({
                "reference": ref,
                **result
            })
            
            # Уведомляем
            if _notify_callback:
                _notify_callback(f"""💰 CRYPTO PAYMENT CONFIRMED!

Reference: {ref}
Amount: {result['amount']} {result['token']}
TX: {result['tx_hash'][:16]}...

Blockchain verification complete!""")
    
    return verified


def payment_watcher_loop(interval: int = 60):
    """Фоновый цикл проверки платежей"""
    global _watcher_running
    
    print(f"[CRYPTO] Payment watcher started (interval: {interval}s)")
    
    while _watcher_running:
        try:
            verified = check_pending_payments()
            if verified:
                print(f"[CRYPTO] Verified {len(verified)} payments")
        except Exception as e:
            print(f"[CRYPTO] Watcher error: {e}")
        
        time.sleep(interval)
    
    print("[CRYPTO] Payment watcher stopped")


def start_crypto_watcher(interval: int = 60):
    """Запустить фоновый мониторинг платежей"""
    global _watcher_running, _watcher_thread
    
    if _watcher_running:
        print("[CRYPTO] Watcher already running")
        return
    
    _watcher_running = True
    _watcher_thread = threading.Thread(
        target=payment_watcher_loop,
        args=(interval,),
        daemon=True
    )
    _watcher_thread.start()


def stop_crypto_watcher():
    """Остановить мониторинг"""
    global _watcher_running
    _watcher_running = False


def set_crypto_notify(callback: Callable):
    """Установить callback для уведомлений"""
    global _notify_callback
    _notify_callback = callback


# === PAYMENT LINK GENERATOR ===

def generate_payment_link(amount: float, reference: str, 
                         token: str = "USDT") -> str:
    """
    Генерирует ссылку для крипто-платежа.
    Примечание: Стандартных deep links для крипто нет,
    поэтому возвращаем информацию для ручного перевода.
    """
    wallet = MY_WALLET
    
    # Для MetaMask можно использовать ethereum: URI (но не для Polygon токенов)
    # Лучше вернуть информацию для отображения
    
    return f"""
💎 CRYPTO PAYMENT

Network: Polygon (MATIC)
Token: {token}
Amount: {amount}
Wallet: {wallet}
Reference: {reference}

⚠️ Send EXACTLY {amount} {token} to the wallet above.
The system will automatically verify your payment.
"""


# === QUICK FUNCTIONS ===

def verify_crypto(amount: float, token: str = "USDT") -> Dict:
    """Быстрая проверка платежа"""
    verifier = CryptoPaymentVerifier()
    return verifier.verify_payment(amount, token)


def get_crypto_balance() -> Dict:
    """Получить баланс за 24 часа"""
    verifier = CryptoPaymentVerifier()
    return verifier.get_total_received(24)


# === TEST ===

if __name__ == "__main__":
    print("=" * 50)
    print("CRYPTO PAYMENTS TEST")
    print("=" * 50)
    
    print(f"\nWallet: {MY_WALLET[:10]}...{MY_WALLET[-6:]}" if MY_WALLET else "No wallet configured")
    print(f"API Key: {'Configured' if POLYGONSCAN_API_KEY else 'Not configured'}")
    
    if MY_WALLET and POLYGONSCAN_API_KEY:
        verifier = CryptoPaymentVerifier()
        
        # Test 1: Get recent transactions
        print("\n[TEST 1] Recent USDT transactions:")
        payments = verifier.get_token_transactions("USDT", limit=5)
        for p in payments[:3]:
            print(f"  {p.amount} {p.token} from {p.from_address[:10]}...")
        
        # Test 2: Total received
        print("\n[TEST 2] Total received (24h):")
        totals = verifier.get_total_received(24)
        print(f"  USDT: ${totals['USDT']:.2f}")
        print(f"  USDC: ${totals['USDC']:.2f}")
        print(f"  Total: ${totals['total_usd']:.2f}")
        
        # Test 3: Verify specific amount
        print("\n[TEST 3] Verify $100 payment:")
        result = verifier.verify_payment(100, "USDT")
        print(f"  Found: {result['found']}")
        # Avoid emoji encoding issues on Windows
        msg = result.get('message', 'No message')
        print(f"  Status: {'CONFIRMED' if result['found'] else 'NOT FOUND'}")
    else:
        print("\n[SKIP] Configure MY_CRYPTO_WALLET and POLYGONSCAN_API_KEY to test")
    
    print("\n[OK] Crypto system ready!")
    print("=" * 50)

