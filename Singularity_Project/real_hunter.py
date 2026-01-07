# -*- coding: utf-8 -*-
"""
REAL HUNTER v1.0 - Actual Job Search
====================================
DuckDuckGo + RSS Feeds + GitHub API
No paid API keys required!
"""
import os
import sys
import json
import time
import hashlib
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# === DATABASE ===
DB_PATH = os.path.join(os.getcwd(), 'data', 'real_jobs.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash TEXT UNIQUE,
        source TEXT,
        title TEXT,
        description TEXT,
        budget TEXT,
        url TEXT,
        posted_at TEXT,
        found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'NEW',
        proposal_sent INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS search_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        query TEXT,
        results_found INTEGER,
        new_jobs INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

# === SEARCH FUNCTIONS ===

def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict]:
    """Search using DuckDuckGo (FREE, no API key)"""
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddg:
            for r in ddg.text(query, max_results=max_results):
                results.append({
                    "source": "DuckDuckGo",
                    "title": r.get("title", ""),
                    "description": r.get("body", "")[:500],
                    "url": r.get("href", ""),
                    "posted_at": datetime.now().strftime("%Y-%m-%d")
                })
        return results
    except Exception as e:
        print(f"[HUNT] DuckDuckGo error: {e}")
        return []

def search_github_issues(keywords: str = "python help wanted") -> List[Dict]:
    """Search GitHub Issues with bounties (FREE)"""
    try:
        import requests
        
        # GitHub Search API (no auth needed for public repos)
        url = "https://api.github.com/search/issues"
        params = {
            "q": f"{keywords} is:open label:\"help wanted\"",
            "sort": "created",
            "order": "desc",
            "per_page": 10
        }
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        results = []
        
        for item in data.get("items", [])[:10]:
            # Extract budget from title/body if mentioned
            body = item.get("body", "") or ""
            title = item.get("title", "")
            
            budget = "Negotiable"
            for word in body.split() + title.split():
                if "$" in word:
                    budget = word
                    break
            
            results.append({
                "source": "GitHub",
                "title": title[:100],
                "description": body[:300],
                "url": item.get("html_url", ""),
                "budget": budget,
                "posted_at": item.get("created_at", "")[:10]
            })
        
        return results
    except Exception as e:
        print(f"[HUNT] GitHub error: {e}")
        return []

def search_rss_feeds() -> List[Dict]:
    """Search RSS feeds for freelance jobs (FREE)"""
    try:
        import requests
        import xml.etree.ElementTree as ET
        
        feeds = [
            # RemoteOK RSS
            "https://remoteok.com/remote-python-jobs.rss",
            # Craigslist (example - gigs)
            "https://newyork.craigslist.org/search/cpg?format=rss"
        ]
        
        results = []
        
        for feed_url in feeds:
            try:
                response = requests.get(feed_url, timeout=10)
                if response.status_code != 200:
                    continue
                
                root = ET.fromstring(response.content)
                
                for item in root.findall(".//item")[:5]:
                    title = item.find("title")
                    link = item.find("link")
                    desc = item.find("description")
                    pub = item.find("pubDate")
                    
                    if title is not None:
                        results.append({
                            "source": "RSS",
                            "title": title.text[:100] if title.text else "",
                            "description": desc.text[:300] if desc is not None and desc.text else "",
                            "url": link.text if link is not None else "",
                            "budget": "TBD",
                            "posted_at": pub.text[:10] if pub is not None and pub.text else ""
                        })
            except:
                continue
        
        return results
    except Exception as e:
        print(f"[HUNT] RSS error: {e}")
        return []

# === JOB PROCESSING ===

def get_job_hash(title: str, url: str) -> str:
    """Generate unique hash for deduplication"""
    data = f"{title.lower()[:50]}:{url.lower()}"
    return hashlib.md5(data.encode()).hexdigest()

def save_job(job: Dict) -> int:
    """Save job to database, return job_id or -1 if duplicate"""
    job_hash = get_job_hash(job.get("title", ""), job.get("url", ""))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO jobs (hash, source, title, description, budget, url, posted_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (job_hash, job.get("source", ""), job.get("title", ""),
                   job.get("description", ""), job.get("budget", "TBD"),
                   job.get("url", ""), job.get("posted_at", "")))
        conn.commit()
        job_id = c.lastrowid
        conn.close()
        return job_id
    except sqlite3.IntegrityError:
        conn.close()
        return -1  # Duplicate

def log_search(query: str, found: int, new: int):
    """Log search activity"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO search_log (query, results_found, new_jobs) VALUES (?, ?, ?)",
              (query, found, new))
    conn.commit()
    conn.close()

# === MAIN HUNT FUNCTION ===

def execute_real_hunt(keywords: str = "python automation freelance") -> Dict[str, Any]:
    """
    Execute real job hunt across multiple sources
    Returns: {success, new_jobs, total_found, jobs: [...]}
    """
    print(f"[HUNT] Starting real hunt: {keywords}")
    
    all_jobs = []
    new_jobs = []
    
    # 1. DuckDuckGo Search
    print("[HUNT] Searching DuckDuckGo...")
    queries = [
        f"{keywords} site:upwork.com",
        f"{keywords} site:freelancer.com",
        f"{keywords} hiring remote",
        "python developer needed 2024"
    ]
    
    for q in queries:
        results = search_duckduckgo(q, max_results=5)
        all_jobs.extend(results)
        time.sleep(1)  # Rate limiting
    
    # 2. GitHub Issues
    print("[HUNT] Searching GitHub...")
    github_jobs = search_github_issues("python automation")
    all_jobs.extend(github_jobs)
    
    # 3. RSS Feeds
    print("[HUNT] Checking RSS feeds...")
    rss_jobs = search_rss_feeds()
    all_jobs.extend(rss_jobs)
    
    # 4. Save new jobs
    for job in all_jobs:
        job_id = save_job(job)
        if job_id > 0:
            job["id"] = job_id
            new_jobs.append(job)
            try:
                title = job.get('title', '')[:50]
                # Safe print for Windows
                print("[HUNT] NEW: {}".format(title.encode('ascii', 'replace').decode()))
            except:
                print("[HUNT] NEW job added")
    
    # 5. Log search
    log_search(keywords, len(all_jobs), len(new_jobs))
    
    result = {
        "success": True,
        "total_found": len(all_jobs),
        "new_jobs": len(new_jobs),
        "duplicates": len(all_jobs) - len(new_jobs),
        "jobs": new_jobs[:10],  # Return top 10 new
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print(f"[HUNT] Complete: {len(new_jobs)} new / {len(all_jobs)} total")
    return result

def get_recent_jobs(limit: int = 10, status: str = None) -> List[Dict]:
    """Get recent jobs from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if status:
        c.execute("SELECT * FROM jobs WHERE status = ? ORDER BY found_at DESC LIMIT ?",
                  (status, limit))
    else:
        c.execute("SELECT * FROM jobs ORDER BY found_at DESC LIMIT ?", (limit,))
    
    jobs = [dict(row) for row in c.fetchall()]
    conn.close()
    return jobs

def get_hunt_stats() -> Dict:
    """Get hunting statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM jobs")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'NEW'")
    new = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM search_log")
    hunts = c.fetchone()[0]
    
    c.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source")
    by_source = dict(c.fetchall())
    
    conn.close()
    
    return {
        "total_jobs": total,
        "new_jobs": new,
        "total_hunts": hunts,
        "by_source": by_source
    }

# === BACKGROUND HUNTER ===

_hunter_running = False
_last_hunt = None
_notify_callback = None

def set_notify_callback(callback):
    """Set callback for notifications"""
    global _notify_callback
    _notify_callback = callback

def notify(message: str):
    """Send notification"""
    if _notify_callback:
        try:
            _notify_callback(message)
        except:
            pass
    print(f"[NOTIFY] {message}")

def hunting_loop(interval_minutes: int = 15):
    """Background hunting loop"""
    global _hunter_running, _last_hunt
    
    _hunter_running = True
    print(f"[HUNT] Background hunter started (interval: {interval_minutes} min)")
    notify(f"HUNTER ACTIVATED\nInterval: {interval_minutes} minutes")
    
    while _hunter_running:
        try:
            result = execute_real_hunt()
            _last_hunt = datetime.now()
            
            if result["new_jobs"] > 0:
                msg = f"HUNT COMPLETE!\n\n"
                msg += f"New jobs: {result['new_jobs']}\n"
                msg += f"Sources: DuckDuckGo, GitHub, RSS\n\n"
                
                for job in result["jobs"][:3]:
                    msg += f"- {job['source']}: {job['title'][:40]}\n"
                
                notify(msg)
            
            # Wait for next hunt
            for _ in range(interval_minutes * 6):  # Check every 10 seconds
                if not _hunter_running:
                    break
                time.sleep(10)
                
        except Exception as e:
            print(f"[HUNT] Error: {e}")
            time.sleep(60)
    
    print("[HUNT] Background hunter stopped")

def start_hunter(interval: int = 15):
    """Start background hunter"""
    global _hunter_running
    
    if _hunter_running:
        return False
    
    t = threading.Thread(target=hunting_loop, args=(interval,), daemon=True)
    t.start()
    return True

def stop_hunter():
    """Stop background hunter"""
    global _hunter_running
    _hunter_running = False

def is_hunter_running() -> bool:
    return _hunter_running

def get_last_hunt_time():
    return _last_hunt

# === TEST ===
if __name__ == "__main__":
    print("=" * 50)
    print("REAL HUNTER TEST")
    print("=" * 50)
    
    result = execute_real_hunt("python automation bot")
    
    print(f"\nResults: {result['new_jobs']} new jobs found")
    for job in result["jobs"][:5]:
        print(f"\n- [{job['source']}] {job['title'][:50]}")
        print(f"  URL: {job['url'][:60]}...")

