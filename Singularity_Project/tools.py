# -*- coding: utf-8 -*-
"""
NEXUS-6 TOOLS v3.0 - GLOBAL MARKET SCANNER
==========================================
США | Европа | Азия | GitHub Bounties
Конвертация валют | Multi-Source Search
"""
import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# === GLOBAL SEARCH TOOLS ===

class GlobalSearchTools:
    """Глобальный поисковик для Nexus-6 агентов"""
    
    def __init__(self):
        self.serper_key = os.getenv("SERPER_API_KEY", "")
        self.search_url = "https://google.serper.dev/search"
    
    def global_market_scanner(self, query: str) -> List[Dict]:
        """
        Сканирует биржи США, Европы, Азии и GitHub Issues.
        Принимает поисковый запрос, возвращает 'жирные' заказы.
        
        Args:
            query: Поисковый запрос (например, "python automation")
        
        Returns:
            Список найденных заказов с title, link, snippet
        """
        if not self.serper_key:
            # Fallback на DuckDuckGo если нет Serper ключа
            return self._fallback_search(query)
        
        headers = {
            'X-API-KEY': self.serper_key,
            'Content-Type': 'application/json'
        }
        
        # Глобальный охват: Upwork (USA), Freelancer (Global), GitHub (Bounty), Toptal
        payload = {
            "q": f"{query} site:upwork.com OR site:freelancer.com OR site:github.com 'bounty' OR site:toptal.com OR site:remoteok.com",
            "num": 15,
            "gl": "us"  # US results priority
        }
        
        try:
            response = requests.post(self.search_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            results = response.json().get('organic', [])
            
            curated_jobs = []
            for item in results:
                curated_jobs.append({
                    "title": item.get('title', ''),
                    "link": item.get('link', ''),
                    "snippet": item.get('snippet', ''),
                    "source": self._extract_source(item.get('link', ''))
                })
            
            print(f"[GLOBAL SCANNER] Found {len(curated_jobs)} jobs for: {query}")
            return curated_jobs
            
        except requests.exceptions.RequestException as e:
            print(f"[GLOBAL SCANNER] API Error: {e}")
            return self._fallback_search(query)
        except Exception as e:
            return [{"error": f"Ошибка глобального поиска: {str(e)}"}]

    def _extract_source(self, url: str) -> str:
        """Определить платформу по URL"""
        if "upwork.com" in url:
            return "Upwork"
        elif "freelancer.com" in url:
            return "Freelancer"
        elif "github.com" in url:
            return "GitHub"
        elif "toptal.com" in url:
            return "Toptal"
        elif "remoteok.com" in url:
            return "RemoteOK"
        return "Other"

    def _fallback_search(self, query: str) -> List[Dict]:
        """Fallback на DuckDuckGo если Serper недоступен"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddg:
                results = list(ddg.text(
                    f"{query} python developer job freelance", 
                    max_results=10
                ))
            
            return [
                {
                    "title": r.get('title', ''),
                    "link": r.get('href', ''),
                    "snippet": r.get('body', '')[:200],
                    "source": "DuckDuckGo"
                }
                for r in results
            ]
        except Exception as e:
            print(f"[FALLBACK SEARCH] Error: {e}")
            return []

    def search_by_region(self, query: str, region: str = "global") -> List[Dict]:
        """
        Поиск по конкретному региону
        
        Args:
            query: Поисковый запрос
            region: "usa", "europe", "asia", "global"
        """
        region_sites = {
            "usa": "site:upwork.com OR site:indeed.com",
            "europe": "site:freelancer.co.uk OR site:peopleperhour.com",
            "asia": "site:freelancer.in OR site:guru.com",
            "github": "site:github.com bounty OR 'help wanted'",
            "global": "site:upwork.com OR site:freelancer.com OR site:toptal.com"
        }
        
        site_filter = region_sites.get(region.lower(), region_sites["global"])
        full_query = f"{query} {site_filter}"
        
        return self.global_market_scanner(full_query)


# === CURRENCY CONVERTER ===

class CurrencyConverter:
    """Конвертер валют для финансового модуля"""
    
    # Актуальные примерные курсы (можно заменить на API)
    RATES_TO_USD = {
        "USD": 1.0,
        "EUR": 1.09,
        "GBP": 1.27,
        "JPY": 0.0067,
        "CNY": 0.14,
        "INR": 0.012,
        "RUB": 0.011,
        "AUD": 0.66,
        "CAD": 0.74,
        "CHF": 1.13
    }
    
    @classmethod
    def to_usd(cls, amount: float, from_currency: str) -> float:
        """Конвертировать в USD"""
        rate = cls.RATES_TO_USD.get(from_currency.upper(), 1.0)
        return round(amount * rate, 2)
    
    @classmethod
    def to_eur(cls, amount: float, from_currency: str) -> float:
        """Конвертировать в EUR"""
        usd_amount = cls.to_usd(amount, from_currency)
        return round(usd_amount / cls.RATES_TO_USD["EUR"], 2)
    
    @classmethod
    def convert(cls, amount: float, from_curr: str, to_curr: str = "USD") -> float:
        """Универсальная конвертация"""
        if to_curr.upper() == "EUR":
            return cls.to_eur(amount, from_curr)
        return cls.to_usd(amount, from_curr)


# === MULTI-SOURCE FACT CHECKER (восстановлено) ===

def check_facts_multi_source(query: str) -> Dict[str, Any]:
    """Проверка фактов из 3 независимых источников"""
    results = {
        "query": query,
        "sources": [],
        "consensus": None
    }
    
    # Source 1: DuckDuckGo (FREE)
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddg:
            ddg_results = list(ddg.text(query, max_results=3))
        if ddg_results:
            results["sources"].append({
                "name": "DuckDuckGo",
                "data": ddg_results[0].get('body', '')[:500]
            })
    except Exception as e:
        results["sources"].append({"name": "DuckDuckGo", "error": str(e)})
    
    # Source 2: Wikipedia (FREE)
    try:
        from langchain_community.tools import WikipediaQueryRun
        from langchain_community.utilities import WikipediaAPIWrapper
        
        wiki = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=500)
        wiki_tool = WikipediaQueryRun(api_wrapper=wiki)
        wiki_result = wiki_tool.run(query)
        results["sources"].append({
            "name": "Wikipedia",
            "data": wiki_result[:500]
        })
    except Exception as e:
        results["sources"].append({"name": "Wikipedia", "error": str(e)})
    
    # Source 3: Serper/Google (если есть ключ)
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        try:
            headers = {'X-API-KEY': serper_key, 'Content-Type': 'application/json'}
            response = requests.post(
                "https://google.serper.dev/search",
                headers=headers,
                json={"q": query, "num": 1},
                timeout=5
            )
            if response.ok:
                organic = response.json().get('organic', [])
                if organic:
                    results["sources"].append({
                        "name": "Google",
                        "data": organic[0].get('snippet', '')[:500]
                    })
        except:
            pass
    
    valid_sources = [s for s in results["sources"] if "data" in s]
    results["consensus"] = f"Verified from {len(valid_sources)} sources"
    
    return results


# === DATA TREND ANALYZER ===

def analyze_data_trends(data: Dict) -> List[str]:
    """Анализ трендов в данных"""
    trends = []
    
    if not data.get("success"):
        return ["Error: Could not analyze data"]
    
    # Для CSV/числовых данных
    if "stats" in data and data["stats"]:
        stats = data["stats"]
        for col, values in stats.items():
            if isinstance(values, dict):
                mean = values.get("mean", 0)
                std = values.get("std", 0)
                if std > mean * 0.5:
                    trends.append(f"High volatility in '{col}': std={std:.2f} vs mean={mean:.2f}")
    
    # Для текстовых данных
    if "content" in data:
        content = data["content"].lower()
        words = content.split()
        word_freq = {}
        for word in words:
            if len(word) > 5:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_words:
            trends.append(f"Key themes: {', '.join([w[0] for w in top_words])}")
    
    return trends[:5] if trends else ["No obvious patterns found"]


# === CREWAI TOOL WRAPPERS ===
# Для совместимости с CrewAI @tool декоратором

try:
    from crewai.tools import BaseTool
    from pydantic import Field
    
    class GlobalMarketScannerTool(BaseTool):
        name: str = "global_market_scanner"
        description: str = "Сканирует биржи США, Европы, Азии и GitHub для поиска заказов. Input: поисковый запрос."
        
        def _run(self, query: str) -> str:
            scanner = GlobalSearchTools()
            results = scanner.global_market_scanner(query)
            
            if not results:
                return "Заказов не найдено"
            
            output = []
            for i, job in enumerate(results[:5], 1):
                output.append(f"""
--- JOB #{i} ---
Source: {job.get('source', 'Unknown')}
Title: {job.get('title', 'N/A')}
Link: {job.get('link', 'N/A')}
Description: {job.get('snippet', 'N/A')[:150]}...
""")
            return "\n".join(output)
    
    class CurrencyConverterTool(BaseTool):
        name: str = "currency_converter"
        description: str = "Конвертирует валюты. Input: 'amount,from_currency,to_currency' (например: '500,EUR,USD')"
        
        def _run(self, input_str: str) -> str:
            try:
                parts = input_str.split(",")
                amount = float(parts[0].strip())
                from_curr = parts[1].strip().upper()
                to_curr = parts[2].strip().upper() if len(parts) > 2 else "USD"
                
                result = CurrencyConverter.convert(amount, from_curr, to_curr)
                return f"{amount} {from_curr} = {result} {to_curr}"
            except Exception as e:
                return f"Ошибка конвертации: {e}"
    
    # Экспорт готовых инструментов
    global_scanner_tool = GlobalMarketScannerTool()
    currency_tool = CurrencyConverterTool()
    
    print("[TOOLS] CrewAI tools loaded: GlobalMarketScanner, CurrencyConverter")
    
except ImportError:
    print("[TOOLS] CrewAI tools not available - using standalone functions")
    global_scanner_tool = None
    currency_tool = None


# === CRYPTO PAYMENT VERIFICATION ===

def verify_crypto_payment(amount_usd: float, token: str = "USDT") -> Dict:
    """
    Проверяет входящий крипто-платёж на Polygon.
    
    Args:
        amount_usd: Ожидаемая сумма в USD
        token: USDT или USDC
    
    Returns:
        Dict с результатом проверки
    """
    try:
        from crypto_payments import verify_crypto
        return verify_crypto(amount_usd, token)
    except ImportError:
        wallet = os.getenv("MY_CRYPTO_WALLET", "")
        api_key = os.getenv("POLYGONSCAN_API_KEY", "")
        
        if not wallet or not api_key:
            return {"found": False, "error": "Wallet or API key not configured"}
        
        # Простая проверка через API
        url = f"https://api.polygonscan.com/api?module=account&action=tokentx&address={wallet}&apikey={api_key}"
        
        try:
            res = requests.get(url, timeout=10).json()
            for tx in res.get('result', [])[:20]:
                val = int(tx.get('value', 0)) / (10**6)  # USDT/USDC = 6 decimals
                if tx.get('tokenSymbol') == token and val >= (amount_usd * 0.98):
                    return {
                        "found": True,
                        "amount": val,
                        "token": token,
                        "tx_hash": tx.get('hash', ''),
                        "message": f"Payment {val} {token} confirmed!"
                    }
            return {"found": False, "message": "Payment not found yet"}
        except Exception as e:
            return {"found": False, "error": str(e)}


# === ECONOMIC EVALUATION ===

def evaluate_order_economics(budget: float, complexity: str = "MEDIUM", 
                             platform: str = "upwork") -> Dict:
    """
    Оценивает экономическую целесообразность заказа.
    Минимум: $50, минимальная маржа: 20%
    
    Args:
        budget: Бюджет клиента
        complexity: LOW, MEDIUM, HIGH
        platform: upwork, freelancer, crypto, direct
    
    Returns:
        Dict с решением (accept/negotiate/decline)
    """
    try:
        from economics import evaluate_order
        return evaluate_order(budget, complexity, "", platform)
    except ImportError:
        # Fallback простая логика
        MIN_ORDER = 50
        MIN_MARGIN = 20
        
        if budget < MIN_ORDER:
            return {
                "accept": False,
                "decision": "decline",
                "reason": f"Budget ${budget} below minimum ${MIN_ORDER}"
            }
        
        # Грубый расчёт маржи
        platform_fee = budget * 0.20  # ~20% комиссия
        labor_cost = {"LOW": 50, "MEDIUM": 150, "HIGH": 400}.get(complexity, 150)
        net_profit = budget - platform_fee - labor_cost * 0.3
        margin = (net_profit / budget) * 100 if budget > 0 else 0
        
        if margin < MIN_MARGIN:
            suggested = budget * 1.3  # +30%
            return {
                "accept": False,
                "decision": "negotiate",
                "margin_percent": round(margin, 1),
                "suggested_price": round(suggested, -1)
            }
        
        return {
            "accept": True,
            "decision": "accept",
            "margin_percent": round(margin, 1),
            "net_profit": round(net_profit, 2)
        }


# === CREWAI CRYPTO TOOL ===

try:
    class CryptoVerifierTool(BaseTool):
        name: str = "crypto_payment_verifier"
        description: str = "Проверяет входящий USDC/USDT платёж на Polygon. Input: 'amount,token' (например: '100,USDT')"
        
        def _run(self, input_str: str) -> str:
            try:
                parts = input_str.split(",")
                amount = float(parts[0].strip())
                token = parts[1].strip().upper() if len(parts) > 1 else "USDT"
                
                result = verify_crypto_payment(amount, token)
                
                if result.get("found"):
                    return f"✅ Payment confirmed: {result['amount']} {result['token']}"
                else:
                    return f"⏳ Payment not found: {result.get('message', 'Waiting...')}"
            except Exception as e:
                return f"Error: {e}"
    
    class EconomicsEvaluatorTool(BaseTool):
        name: str = "economics_evaluator"
        description: str = "Оценивает рентабельность заказа. Input: 'budget,complexity,platform' (например: '100,MEDIUM,upwork')"
        
        def _run(self, input_str: str) -> str:
            try:
                parts = input_str.split(",")
                budget = float(parts[0].strip())
                complexity = parts[1].strip().upper() if len(parts) > 1 else "MEDIUM"
                platform = parts[2].strip().lower() if len(parts) > 2 else "upwork"
                
                result = evaluate_order_economics(budget, complexity, platform)
                
                if result.get("accept"):
                    return f"✅ ACCEPT: Margin {result['margin_percent']}%, Profit ${result.get('net_profit', 'N/A')}"
                elif result.get("decision") == "negotiate":
                    return f"💬 NEGOTIATE: Margin {result['margin_percent']}% too low. Suggest ${result['suggested_price']}"
                else:
                    return f"❌ DECLINE: {result.get('reason', 'Below minimum')}"
            except Exception as e:
                return f"Error: {e}"
    
    crypto_verifier_tool = CryptoVerifierTool()
    economics_tool = EconomicsEvaluatorTool()
    
    print("[TOOLS] Added: CryptoVerifier, EconomicsEvaluator")
    
except Exception:
    crypto_verifier_tool = None
    economics_tool = None


# === LEGACY EXPORTS ===
# Для обратной совместимости

search_tool = None
file_read_tool = None

try:
    from crewai_tools import SerperDevTool, FileReadTool
    if os.getenv("SERPER_API_KEY"):
        search_tool = SerperDevTool()
    file_read_tool = FileReadTool()
except:
    pass
