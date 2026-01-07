# -*- coding: utf-8 -*-
"""
WISE ENGINE v2.0 - Payment Links + Monitoring
==============================================
Stripe (Card) + Wise (Invoice) + Payment Watcher
"""

import os
import sys
import uuid
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('wise')

# === CONFIG ===
WISE_TAG = os.getenv('WISE_TAG', 'advancedmedicinalconsultingltd')
WISE_API_TOKEN = os.getenv('WISE_API_TOKEN', '')
STRIPE_LINK = os.getenv('STRIPE_PAYMENT_LINK', 'https://buy.stripe.com/test_5kQcN4gu04FUa0wfSCaEE00')

logger.info("WISE ENGINE v2.0 | Tag: %s | API: %s", WISE_TAG, "OK" if WISE_API_TOKEN else "NO")

# === STATE ===
_watcher_running = False
_notify_callback = None
_pending_refs = {}  # reference -> {amount, currency, created_at}
_last_check_time = None


def generate_reference(prefix: str = "SNG") -> str:
    """Generate unique payment reference"""
    uid = uuid.uuid4().hex[:6].upper()
    return "{}-{}".format(prefix, uid)


def get_simple_link(amount: float, reference: str = None, currency: str = "EUR") -> str:
    """Simple Wise Pay Me link"""
    if not reference:
        reference = generate_reference()
    
    safe_ref = reference.replace(" ", "%20")
    url = "https://wise.com/pay/me/{}?amount={:.2f}&currency={}&description=REF%3A{}".format(
        WISE_TAG, amount, currency, safe_ref
    )
    
    logger.info("[WISE] URL: %s", url[:80])
    return url


def get_stripe_link(reference: str = None, amount: float = None) -> str:
    """Stripe payment link"""
    if not reference:
        reference = generate_reference()
    
    url = "{}?client_reference_id={}".format(STRIPE_LINK, reference)
    if amount:
        url += "&amount={}".format(int(amount * 100))  # Stripe uses cents
    
    logger.info("[STRIPE] URL: %s", url[:80])
    return url


def get_both_links(amount: float, currency: str = "USD", reference: str = None) -> dict:
    """Get both Stripe and Wise payment links"""
    if not reference:
        reference = generate_reference()
    
    # Track this reference for monitoring
    _pending_refs[reference] = {
        "amount": amount,
        "currency": currency,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "stripe": get_stripe_link(reference, amount),
        "wise": get_simple_link(amount, reference, currency),
        "reference": reference,
        "amount": amount,
        "currency": currency
    }


# ============================================================
# WISE API FUNCTIONS (if token available)
# ============================================================

def get_wise_profile_id() -> Optional[str]:
    """Get Wise profile ID"""
    if not WISE_API_TOKEN:
        return None
    
    try:
        import requests
        
        response = requests.get(
            "https://api.wise.com/v1/profiles",
            headers={"Authorization": "Bearer {}".format(WISE_API_TOKEN)},
            timeout=10
        )
        
        if response.ok:
            profiles = response.json()
            # Prefer business profile
            for p in profiles:
                if p.get('type') == 'BUSINESS':
                    return str(p['id'])
            # Fallback to personal
            if profiles:
                return str(profiles[0]['id'])
    except Exception as e:
        logger.error("[WISE API] Profile error: %s", e)
    
    return None


def check_incoming_payments(hours: int = 24) -> List[Dict]:
    """Check for incoming payments in last N hours"""
    if not WISE_API_TOKEN:
        logger.warning("[WISE API] No API token")
        return []
    
    profile_id = get_wise_profile_id()
    if not profile_id:
        return []
    
    try:
        import requests
        from datetime import timedelta
        
        # Get borderless accounts
        response = requests.get(
            "https://api.wise.com/v1/borderless-accounts?profileId={}".format(profile_id),
            headers={"Authorization": "Bearer {}".format(WISE_API_TOKEN)},
            timeout=10
        )
        
        if not response.ok:
            logger.error("[WISE API] Accounts error: %s", response.status_code)
            return []
        
        accounts = response.json()
        payments = []
        
        for account in accounts:
            for balance in account.get('balances', []):
                currency = balance.get('currency', '')
                
                # Get transactions for this currency
                tx_response = requests.get(
                    "https://api.wise.com/v1/borderless-accounts/{}/statement.json".format(account['id']),
                    headers={"Authorization": "Bearer {}".format(WISE_API_TOKEN)},
                    params={
                        "currency": currency,
                        "intervalStart": (datetime.now() - timedelta(hours=hours)).isoformat() + "Z",
                        "intervalEnd": datetime.now().isoformat() + "Z"
                    },
                    timeout=10
                )
                
                if tx_response.ok:
                    statement = tx_response.json()
                    for tx in statement.get('transactions', []):
                        if tx.get('type') == 'CREDIT':  # Incoming payment
                            payments.append({
                                "id": tx.get('referenceNumber', ''),
                                "amount": tx.get('amount', {}).get('value', 0),
                                "currency": tx.get('amount', {}).get('currency', ''),
                                "reference": tx.get('details', {}).get('description', ''),
                                "sender": tx.get('details', {}).get('senderName', ''),
                                "date": tx.get('date', '')
                            })
        
        logger.info("[WISE API] Found %d incoming payments", len(payments))
        return payments
        
    except Exception as e:
        logger.error("[WISE API] Check payments error: %s", e)
        return []


def match_payments_to_refs(payments: List[Dict]) -> List[Dict]:
    """Match incoming payments to our pending references"""
    matched = []
    
    for payment in payments:
        ref_text = payment.get('reference', '').upper()
        
        for our_ref, info in _pending_refs.items():
            if our_ref.upper() in ref_text:
                matched.append({
                    "reference": our_ref,
                    "expected_amount": info['amount'],
                    "received_amount": payment['amount'],
                    "currency": payment['currency'],
                    "sender": payment['sender'],
                    "payment_id": payment['id']
                })
                logger.info("[WISE] MATCHED! Ref: %s, Amount: %s", our_ref, payment['amount'])
    
    return matched


# ============================================================
# PAYMENT WATCHER
# ============================================================

def set_notify_callback(callback: Callable):
    """Set notification callback"""
    global _notify_callback
    _notify_callback = callback
    logger.info("[WISE] Notify callback set")


def notify(message: str):
    """Send notification"""
    if _notify_callback:
        try:
            _notify_callback(message)
        except Exception as e:
            logger.error("[WISE] Notify error: %s", e)


def watcher_loop(interval: int = 300):
    """Background payment watcher loop"""
    global _watcher_running, _last_check_time
    _watcher_running = True
    
    logger.info("[WISE WATCHER] Starting (interval: %d seconds)", interval)
    
    while _watcher_running:
        try:
            _last_check_time = datetime.now()
            
            if WISE_API_TOKEN and _pending_refs:
                logger.info("[WISE WATCHER] Checking for payments...")
                
                payments = check_incoming_payments(hours=24)
                matched = match_payments_to_refs(payments)
                
                for m in matched:
                    msg = """PAYMENT RECEIVED!

Reference: {}
Amount: {} {}
Sender: {}

Status: PAID""".format(
                        m['reference'], m['received_amount'], m['currency'], m['sender']
                    )
                    notify(msg)
                    
                    # Remove from pending
                    if m['reference'] in _pending_refs:
                        del _pending_refs[m['reference']]
            
            # Sleep in chunks for faster shutdown
            for _ in range(interval // 10):
                if not _watcher_running:
                    break
                time.sleep(10)
                
        except Exception as e:
            logger.error("[WISE WATCHER] Error: %s", e)
            time.sleep(60)
    
    logger.info("[WISE WATCHER] Stopped")


def start_watcher(interval: int = 300):
    """Start payment watcher in background"""
    global _watcher_running
    if _watcher_running:
        logger.warning("[WISE WATCHER] Already running")
        return False
    
    t = threading.Thread(target=watcher_loop, args=(interval,), daemon=True)
    t.start()
    return True


def stop_watcher():
    """Stop payment watcher"""
    global _watcher_running
    _watcher_running = False
    logger.info("[WISE WATCHER] Stop requested")


def is_watcher_running() -> bool:
    """Check if watcher is running"""
    return _watcher_running


def get_watcher_status() -> Dict:
    """Get watcher status"""
    return {
        "running": _watcher_running,
        "last_check": _last_check_time.isoformat() if _last_check_time else None,
        "pending_refs": len(_pending_refs),
        "has_api_token": bool(WISE_API_TOKEN)
    }


# ============================================================
# ALIASES FOR COMPATIBILITY
# ============================================================

def create_payment_url(amount, currency="EUR", reference=None):
    return get_simple_link(amount, reference, currency)

def get_both_payment_urls(amount, currency="USD", reference=None):
    return get_both_links(amount, currency, reference)

def create_payment_link(amount, currency="EUR", reference=None, description=""):
    if not reference:
        reference = generate_reference()
    return {
        "success": True,
        "payment_url": get_simple_link(amount, reference, currency),
        "reference": reference,
        "amount": amount,
        "currency": currency,
        "wise_tag": WISE_TAG
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("WISE ENGINE v2.0 TEST")
    print("=" * 50)
    
    links = get_both_links(150.0, "USD", "TEST-123")
    print("Stripe:", links['stripe'])
    print("Wise:", links['wise'])
    print("Reference:", links['reference'])
    
    print("\nWatcher status:", get_watcher_status())
    
    if WISE_API_TOKEN:
        print("\nChecking payments...")
        payments = check_incoming_payments(hours=48)
        print("Found:", len(payments), "payments")
