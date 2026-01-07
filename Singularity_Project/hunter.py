# -*- coding: utf-8 -*-
"""
HUNTER v5.0 - REAL WEB SEARCH
============================
DuckDuckGo + Serper + Real Job Parsing
Global: USA, Europe, Asia, GitHub
"""

import os
import sys
import sqlite3
import time
import threading
import logging
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('hunter')

# === CONFIG ===
HUNT_INTERVAL = 600  # 10 minutes
MIN_BUDGET = 50  # Minimum $50 USD
DB_DIR = os.path.join(os.getcwd(), 'data')
os.makedirs(DB_DIR, exist_ok=True)
LEADS_DB = os.path.join(DB_DIR, 'leads.db')

# State
_hunter_running = False
_autonomous_mode = False  # 24/7 mode for Railway
_last_hunt_time = None
_hunt_count = 0
_telegram_notify = None
_admin_chat = None
_auto_execute = False  # Auto-start work on new leads

logger.info("HUNTER v6.0 | Real Web Search | Min Budget: $%d | Interval: 10 min", MIN_BUDGET)


def init_db():
    """Initialize database"""
    conn = sqlite3.connect(LEADS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT UNIQUE,
        project_hash TEXT UNIQUE,
        platform TEXT,
        title TEXT,
        url TEXT,
        budget TEXT,
        client TEXT,
        description TEXT,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        proposal_sent INTEGER DEFAULT 0,
        paid INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS hunt_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hunt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        leads_found INTEGER DEFAULT 0,
        new_leads INTEGER DEFAULT 0,
        search_query TEXT
    )''')
    conn.commit()
    conn.close()


init_db()


def get_hash(platform, title, url=""):
    """Generate unique hash for deduplication"""
    data = "{}:{}:{}".format(platform.lower(), title.lower()[:100], url.lower()[:100])
    return hashlib.md5(data.encode()).hexdigest()


def is_duplicate(platform, title, url=""):
    """Check if lead already exists"""
    h = get_hash(platform, title, url)
    conn = sqlite3.connect(LEADS_DB)
    c = conn.cursor()
    c.execute("SELECT id FROM leads WHERE project_hash = ?", (h,))
    exists = c.fetchone() is not None
    conn.close()
    return exists


def save_lead(platform, project_id, title, url="", budget="", client="", description=""):
    """Save new lead to database"""
    h = get_hash(platform, title, url)
    conn = sqlite3.connect(LEADS_DB)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO leads (project_id, project_hash, platform, title, url, budget, client, description)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (project_id, h, platform, title, url, budget, client, description[:500] if description else ""))
        conn.commit()
        lead_id = c.lastrowid
        conn.close()
        logger.info("[HUNTER] NEW lead #%d: %s", lead_id, title[:40])
        return lead_id
    except sqlite3.IntegrityError:
        conn.close()
        return -1


def log_hunt(found, new_count, query=""):
    """Log hunt results"""
    conn = sqlite3.connect(LEADS_DB)
    c = conn.cursor()
    c.execute("INSERT INTO hunt_log (leads_found, new_leads, search_query) VALUES (?, ?, ?)", 
              (found, new_count, query[:200] if query else ""))
    conn.commit()
    conn.close()


def set_telegram_notifier(func, admin_chat_id=None):
    """Set Telegram notification function"""
    global _telegram_notify, _admin_chat
    _telegram_notify = func
    _admin_chat = admin_chat_id
    logger.info("[HUNTER] Telegram notifier set")


def notify(message):
    """Send notification"""
    if _telegram_notify:
        try:
            _telegram_notify(message)
        except Exception as e:
            logger.error("[HUNTER] Notify error: %s", e)


def get_stripe_link(project_id):
    """Generate Stripe payment link"""
    STRIPE_BASE = os.getenv('STRIPE_PAYMENT_LINK', 'https://buy.stripe.com/test_5kQcN4gu04FUa0wfSCaEE00')
    return STRIPE_BASE + "?client_reference_id=" + str(project_id)


def get_wise_link(amount, ref):
    """Generate Wise payment link"""
    WISE_TAG = os.getenv('WISE_TAG', 'advancedmedicinalconsultingltd')
    return "https://wise.com/pay/me/{}?amount={}&currency=USD&description={}".format(WISE_TAG, amount, ref)


# ============================================================
# REAL WEB SEARCH
# ============================================================

def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict]:
    """Search using DuckDuckGo (FREE) - with fallback methods"""
    results = []
    
    # Method 1: Try ddgs package
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        
        with DDGS() as ddg:
            search_results = list(ddg.text(query, max_results=max_results))
        
        for r in search_results:
            results.append({
                "title": r.get('title', ''),
                "url": r.get('href', r.get('link', '')),
                "snippet": r.get('body', r.get('snippet', '')),
                "source": "DuckDuckGo"
            })
        
        if results:
            logger.info("[DDG] Found %d results for: %s", len(results), query[:50])
            return results
            
    except Exception as e:
        logger.warning("[DDG] Primary method failed: %s", str(e)[:50])
    
    # Method 2: Direct HTTP request as fallback
    try:
        import requests
        
        # Use DuckDuckGo HTML search
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(
            'https://html.duckduckgo.com/html/',
            params={'q': query},
            headers=headers,
            timeout=10
        )
        
        if response.ok:
            # Simple regex extraction
            import re
            
            # Find result links
            links = re.findall(r'href="(https?://[^"]+)"[^>]*>([^<]+)</a>', response.text)
            
            for url, title in links[:max_results]:
                if 'duckduckgo.com' not in url and len(title) > 10:
                    results.append({
                        "title": title.strip(),
                        "url": url,
                        "snippet": "",
                        "source": "DDG-HTML"
                    })
        
        logger.info("[DDG-HTML] Found %d results", len(results))
        
    except Exception as e:
        logger.error("[DDG] All methods failed: %s", e)
    
    return results


def search_serper(query: str, max_results: int = 10) -> List[Dict]:
    """Search using Serper API (Google)"""
    results = []
    api_key = os.getenv('SERPER_API_KEY', '')
    
    if not api_key:
        return results
    
    try:
        import requests
        
        response = requests.post(
            "https://google.serper.dev/search",
            headers={'X-API-KEY': api_key, 'Content-Type': 'application/json'},
            json={"q": query, "num": max_results},
            timeout=10
        )
        
        if response.ok:
            data = response.json()
            for item in data.get('organic', []):
                results.append({
                    "title": item.get('title', ''),
                    "url": item.get('link', ''),
                    "snippet": item.get('snippet', ''),
                    "source": "Google"
                })
        
        logger.info("[SERPER] Found %d results for: %s", len(results), query[:50])
        
    except Exception as e:
        logger.error("[SERPER] Search error: %s", e)
    
    return results


def extract_budget(text: str) -> str:
    """Extract budget from text"""
    patterns = [
        r'\$(\d{1,5}(?:,\d{3})*(?:\.\d{2})?)',  # $100, $1,000, $1,000.00
        r'(\d{1,5})\s*(?:USD|usd)',              # 100 USD
        r'budget[:\s]+\$?(\d{1,5})',             # budget: $100
        r'(\d{2,4})\s*-\s*(\d{2,4})',            # 100-500
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                return "${}-${}".format(match.group(1), match.group(2))
            return "${}".format(match.group(1))
    
    return "Negotiable"


def parse_budget_value(budget_str: str) -> int:
    """Parse budget string to numeric value"""
    if not budget_str or budget_str == "Negotiable":
        return 0
    
    # Remove $ and commas
    clean = budget_str.replace("$", "").replace(",", "").strip()
    
    # Handle range (take higher value)
    if "-" in clean:
        parts = clean.split("-")
        try:
            return max(int(p.strip()) for p in parts if p.strip().isdigit())
        except:
            pass
    
    # Single value
    match = re.search(r'(\d+)', clean)
    if match:
        return int(match.group(1))
    
    return 0


def meets_min_budget(budget_str: str, min_budget: int = MIN_BUDGET) -> bool:
    """Check if budget meets minimum threshold"""
    value = parse_budget_value(budget_str)
    
    # If "Negotiable", assume it could be good
    if budget_str == "Negotiable":
        return True
    
    return value >= min_budget


def detect_platform(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()
    if 'upwork.com' in url_lower:
        return 'Upwork'
    elif 'freelancer.com' in url_lower:
        return 'Freelancer'
    elif 'github.com' in url_lower:
        return 'GitHub'
    elif 'reddit.com' in url_lower:
        return 'Reddit'
    elif 'toptal.com' in url_lower:
        return 'Toptal'
    elif 'fiverr.com' in url_lower:
        return 'Fiverr'
    elif 'peopleperhour.com' in url_lower:
        return 'PeoplePerHour'
    return 'Web'


def is_relevant_job(title: str, snippet: str) -> bool:
    """Check if result is a relevant job posting"""
    text = (title + " " + snippet).lower()
    
    # Must have keywords
    job_keywords = ['python', 'developer', 'script', 'bot', 'automation', 'scraping', 
                    'api', 'data', 'freelance', 'project', 'need', 'looking for', 'hire']
    
    # Exclude keywords
    exclude = ['course', 'tutorial', 'learn', 'book', 'article', 'blog', 
               'salary', 'job board', 'career', 'company profile']
    
    has_keyword = any(kw in text for kw in job_keywords)
    has_exclude = any(ex in text for ex in exclude)
    
    return has_keyword and not has_exclude


# ============================================================
# MAIN HUNT FUNCTION
# ============================================================

def execute_real_hunt(auto_execute: bool = None) -> Dict:
    """Execute real web search for jobs with $50+ filter"""
    global _last_hunt_time, _hunt_count, _auto_execute
    _last_hunt_time = datetime.now()
    _hunt_count += 1
    
    if auto_execute is not None:
        _auto_execute = auto_execute
    
    logger.info("=" * 50)
    logger.info("[HUNTER] HUNT #%d - REAL WEB SEARCH (Min: $%d)", _hunt_count, MIN_BUDGET)
    logger.info("=" * 50)
    
    # Search queries optimized for $50+ projects
    queries = [
        # USA - High budget
        'python automation freelance "$100" OR "$200" site:upwork.com',
        'python developer budget "$50" "$100" site:upwork.com',
        'web scraping developer needed site:upwork.com',
        'telegram bot python site:freelancer.com',
        
        # Global - Budget keywords
        'python developer hire freelance budget $100',
        'need python script automation $50 $100',
        
        # GitHub - Bounties
        'python "help wanted" bounty $50 site:github.com',
        
        # Reddit - For hire
        'python developer forhire budget site:reddit.com',
    ]
    
    all_results = []
    new_leads = []
    filtered_low_budget = 0
    
    for query in queries:
        logger.info("[HUNTER] Searching: %s", query[:60])
        
        # Try Serper first (better results), fallback to DuckDuckGo
        results = search_serper(query, 5)
        if not results:
            results = search_duckduckgo(query, 5)
        
        for r in results:
            if is_relevant_job(r['title'], r['snippet']):
                all_results.append(r)
        
        time.sleep(1)  # Rate limiting
    
    # Process and save leads with budget filter
    for r in all_results:
        title = r['title'][:100]
        url = r['url']
        platform = detect_platform(url)
        budget = extract_budget(r['snippet'])
        
        # FILTER: Skip low budget projects
        if not meets_min_budget(budget, MIN_BUDGET):
            filtered_low_budget += 1
            logger.info("[HUNTER] Skipped (low budget %s): %s", budget, title[:40])
            continue
        
        if is_duplicate(platform, title, url):
            continue
        
        project_id = "{}-{}".format(platform[:3].upper(), _hunt_count * 1000 + len(new_leads))
        
        lead_id = save_lead(
            platform=platform,
            project_id=project_id,
            title=title,
            url=url,
            budget=budget,
            description=r['snippet']
        )
        
        if lead_id > 0:
            lead = {
                "id": lead_id,
                "project_id": project_id,
                "platform": platform,
                "title": title,
                "url": url,
                "budget": budget,
                "budget_value": parse_budget_value(budget),
                "description": r['snippet'][:200]
            }
            new_leads.append(lead)
            
            # Generate payment links
            ref = "SNG-{}".format(lead_id)
            stripe_url = get_stripe_link(project_id)
            
            # AUTO-EXECUTE: Start work immediately if enabled
            if _auto_execute:
                try:
                    from execution_engine import get_engine
                    engine = get_engine()
                    order = engine.create_order_from_lead(lead)
                    engine.generate_and_send_proposal(order['id'])
                    # Start execution automatically
                    engine.execute_order(order['id'])
                    lead['auto_executed'] = True
                    lead['order_id'] = order['id']
                    logger.info("[HUNTER] AUTO-EXECUTED: %s", title[:40])
                except Exception as e:
                    logger.error("[HUNTER] Auto-execute failed: %s", e)
            
            # Notify about new lead
            msg = """NEW LEAD FOUND!

Platform: {}
Title: {}
Budget: {}

URL: {}

Stripe: {}
Reference: {}""".format(
                platform, title[:50], budget, url[:80], stripe_url[:60], ref
            )
            notify(msg)
    
    # Log hunt
    log_hunt(len(all_results), len(new_leads), ", ".join(queries[:2]))
    
    logger.info("[HUNTER] Hunt complete: %d found, %d new, %d filtered (low budget)", 
                len(all_results), len(new_leads), filtered_low_budget)
    
    if new_leads:
        summary = "HUNT #{} COMPLETE!\n\n".format(_hunt_count)
        summary += "New Leads: {} (Budget ${}+)\n".format(len(new_leads), MIN_BUDGET)
        summary += "Filtered (low budget): {}\n".format(filtered_low_budget)
        for lead in new_leads[:5]:
            auto_tag = " [AUTO]" if lead.get('auto_executed') else ""
            summary += "\n- {}: {} ({}){}".format(
                lead['platform'], lead['title'][:30], lead['budget'], auto_tag
            )
        notify(summary)
    
    return {
        "success": True,
        "hunt_number": _hunt_count,
        "total_found": len(all_results),
        "new_leads": len(new_leads),
        "filtered_low_budget": filtered_low_budget,
        "min_budget": MIN_BUDGET,
        "auto_execute": _auto_execute,
        "leads": new_leads
    }


def execute_hunt():
    """Wrapper for compatibility"""
    return execute_real_hunt()


# ============================================================
# AUTONOMOUS MODE - 24/7 Operation
# ============================================================

def enable_autonomous_mode(auto_execute: bool = True):
    """Enable 24/7 autonomous mode"""
    global _autonomous_mode, _auto_execute
    _autonomous_mode = True
    _auto_execute = auto_execute
    logger.info("[HUNTER] AUTONOMOUS MODE ENABLED (auto_execute=%s)", auto_execute)
    notify("AUTONOMOUS MODE ENABLED\n\nThe system will run 24/7 even when your computer is off.\nAuto-execute: {}\nMin budget: ${}".format(
        "ON" if auto_execute else "OFF", MIN_BUDGET
    ))


def disable_autonomous_mode():
    """Disable autonomous mode"""
    global _autonomous_mode, _auto_execute
    _autonomous_mode = False
    _auto_execute = False
    logger.info("[HUNTER] AUTONOMOUS MODE DISABLED")
    notify("AUTONOMOUS MODE DISABLED")


def is_autonomous_mode() -> bool:
    """Check if autonomous mode is enabled"""
    return _autonomous_mode


def set_auto_execute(enabled: bool):
    """Set auto-execute mode"""
    global _auto_execute
    _auto_execute = enabled
    logger.info("[HUNTER] Auto-execute: %s", enabled)


# ============================================================
# BACKGROUND LOOP
# ============================================================

def hunting_loop():
    """Continuous hunting loop"""
    global _hunter_running
    _hunter_running = True
    
    logger.info("[HUNTER] STARTING INFINITE LOOP (10 min interval)")
    notify("HUNTER ACTIVATED\n\nMode: Real Web Search\nInterval: 10 minutes\nPlatforms: Upwork, Freelancer, GitHub, Reddit")
    
    while _hunter_running:
        try:
            execute_real_hunt()
            
            logger.info("[HUNTER] Sleeping 10 minutes...")
            for _ in range(60):  # 60 x 10s = 600s = 10 min
                if not _hunter_running:
                    break
                time.sleep(10)
                
        except Exception as e:
            logger.error("[HUNTER] Loop error: %s", e)
            notify("HUNTER ERROR: {}".format(str(e)[:100]))
            time.sleep(60)
    
    logger.info("[HUNTER] Loop stopped")


def start_hunter():
    """Start hunter in background"""
    global _hunter_running
    if _hunter_running:
        logger.warning("[HUNTER] Already running")
        return False
    
    t = threading.Thread(target=hunting_loop, daemon=True)
    t.start()
    return True


def stop_hunter():
    """Stop hunter"""
    global _hunter_running
    _hunter_running = False
    logger.info("[HUNTER] Stop requested")


def is_hunter_running():
    """Check if hunter is running"""
    return _hunter_running


def get_last_hunt_time():
    """Get last hunt time"""
    return _last_hunt_time


def get_stats():
    """Get hunter statistics"""
    try:
        conn = sqlite3.connect(LEADS_DB)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM leads")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM hunt_log")
        hunts = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM leads WHERE paid = 1")
        paid = c.fetchone()[0]
        conn.close()
        return {"total_leads": total, "total_hunts": hunts, "paid_leads": paid}
    except:
        return {"total_leads": 0, "total_hunts": 0, "paid_leads": 0}


def get_recent_leads(limit: int = 10) -> List[Dict]:
    """Get recent leads"""
    try:
        conn = sqlite3.connect(LEADS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM leads ORDER BY first_seen DESC LIMIT ?", (limit,))
        leads = [dict(row) for row in c.fetchall()]
        conn.close()
        return leads
    except:
        return []


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("Testing REAL web search...")
    result = execute_real_hunt()
    print("\nResult:", result)
