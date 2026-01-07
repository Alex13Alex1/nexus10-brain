# -*- coding: utf-8 -*-
# ============================================================
# SINGULARITY SCHEDULER - APScheduler Background Tasks
# Wise Polling & Auto-Notifications
# ============================================================

import os
import sys
import logging
from datetime import datetime
from typing import Optional, Callable

os.environ['PYTHONIOENCODING'] = 'utf-8'
logger = logging.getLogger('scheduler')

# === SCHEDULER CONFIG ===
WISE_POLL_INTERVAL = 300  # 5 minutes (in seconds)
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')

# Global references
_scheduler = None
_telegram_bot = None
_check_payments_func = None

def init_scheduler():
    """Initialize APScheduler"""
    global _scheduler
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        
        _scheduler = BackgroundScheduler(
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Only one instance at a time
                'misfire_grace_time': 60  # 60 seconds grace
            }
        )
        logger.info("[SCHEDULER] Initialized")
        return _scheduler
        
    except ImportError as e:
        logger.error(f"[SCHEDULER] APScheduler not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"[SCHEDULER] Init error: {e}")
        return None

def set_telegram_bot(bot):
    """Set Telegram bot for notifications"""
    global _telegram_bot
    _telegram_bot = bot
    logger.info("[SCHEDULER] Telegram bot set")

def set_payment_checker(func):
    """Set the function to check payments from Wise"""
    global _check_payments_func
    _check_payments_func = func
    logger.info("[SCHEDULER] Payment checker set")

def send_notification(message: str):
    """Send notification via Telegram"""
    if not _telegram_bot or not ADMIN_CHAT_ID:
        logger.warning("[SCHEDULER] Cannot send notification - no bot or admin chat")
        return False
    
    try:
        _telegram_bot.send_message(ADMIN_CHAT_ID, message)
        logger.info(f"[SCHEDULER] Notification sent")
        return True
    except Exception as e:
        logger.error(f"[SCHEDULER] Notification error: {e}")
        return False

def wise_polling_job():
    """
    Background job: Poll Wise API for incoming payments
    Runs every 5 minutes
    """
    from database import (
        get_active_references, record_payment, 
        get_lead_by_reference, log_wise_sync,
        get_unnotified_payments, mark_payment_notified
    )
    
    logger.info("[WISE POLL] Starting...")
    
    transactions_found = 0
    payments_matched = 0
    
    try:
        if not _check_payments_func:
            logger.warning("[WISE POLL] No payment checker function set")
            log_wise_sync(0, 0, "error", "No payment checker")
            return
        
        # Get active references we're looking for
        active_refs = get_active_references()
        if not active_refs:
            logger.info("[WISE POLL] No active references to check")
            log_wise_sync(0, 0, "success", "No active references")
            return
        
        logger.info(f"[WISE POLL] Checking {len(active_refs)} active references")
        
        # Check Wise for payments in last 24 hours
        result = _check_payments_func(hours=24)
        
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"[WISE POLL] API error: {error_msg}")
            log_wise_sync(0, 0, "error", error_msg)
            return
        
        # Process transactions
        transactions = result.get("transactions", [])
        transactions_found = len(transactions)
        
        for tx in transactions:
            ref = tx.get("reference", "")
            amount = tx.get("amount", 0)
            currency = tx.get("currency", "USD")
            sender = tx.get("sender", "")
            tx_id = tx.get("id", "")
            
            # Check if this reference matches any of our leads
            if ref in active_refs:
                # Record payment
                payment_id = record_payment(
                    wise_ref=ref,
                    amount=amount,
                    currency=currency,
                    sender=sender,
                    wise_transaction_id=tx_id
                )
                
                if payment_id > 0:
                    payments_matched += 1
                    logger.info(f"[WISE POLL] PAYMENT MATCHED: {ref} = ${amount}")
        
        # Log sync
        log_wise_sync(transactions_found, payments_matched, "success")
        
        # Send notifications for unnotified payments
        unnotified = get_unnotified_payments()
        for payment in unnotified:
            lead_id = payment.get("lead_id", "?")
            amount = payment.get("amount", 0)
            currency = payment.get("currency", "USD")
            wise_ref = payment.get("wise_ref", "")
            
            # Send notification
            message = f"""💰 MONEY RECEIVED!

Lead #{lead_id} paid ${amount} {currency}
Reference: {wise_ref}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Status: PAID ✅"""
            
            if send_notification(message):
                mark_payment_notified(payment["id"])
        
        logger.info(f"[WISE POLL] Complete: {transactions_found} tx, {payments_matched} matched")
        
    except Exception as e:
        logger.error(f"[WISE POLL] Error: {e}")
        log_wise_sync(0, 0, "error", str(e)[:200])

def start_scheduler():
    """Start the scheduler with Wise polling job"""
    global _scheduler
    
    if not _scheduler:
        _scheduler = init_scheduler()
    
    if not _scheduler:
        logger.error("[SCHEDULER] Cannot start - not initialized")
        return False
    
    try:
        from apscheduler.triggers.interval import IntervalTrigger
        
        # Add Wise polling job - every 5 minutes
        _scheduler.add_job(
            wise_polling_job,
            trigger=IntervalTrigger(seconds=WISE_POLL_INTERVAL),
            id='wise_polling',
            name='Wise Payment Polling',
            replace_existing=True
        )
        
        _scheduler.start()
        logger.info(f"[SCHEDULER] Started - Wise poll every {WISE_POLL_INTERVAL//60} minutes")
        return True
        
    except Exception as e:
        logger.error(f"[SCHEDULER] Start error: {e}")
        return False

def stop_scheduler():
    """Stop the scheduler"""
    global _scheduler
    
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] Stopped")

def get_scheduler_status() -> dict:
    """Get scheduler status"""
    if not _scheduler:
        return {"running": False, "jobs": 0}
    
    jobs = _scheduler.get_jobs()
    return {
        "running": _scheduler.running,
        "jobs": len(jobs),
        "job_names": [j.name for j in jobs],
        "wise_interval_minutes": WISE_POLL_INTERVAL // 60
    }

# Run initial poll on import (disabled - let it run on schedule)
# wise_polling_job()












