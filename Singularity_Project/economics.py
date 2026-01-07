# -*- coding: utf-8 -*-
"""
NEXUS-6 ECONOMICS ENGINE v1.0
==============================
Оценка рентабельности заказов.
Правила:
- Минимальный заказ: $50
- Минимальная маржа: 20%
- Если маржа < 20% → отказ или предложение доплаты

Author: NEXUS-6 AI System
"""

import os
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from enum import Enum

# === CONSTANTS ===
MIN_ORDER_AMOUNT = 50.0  # Минимальный заказ в USD
MIN_MARGIN_PERCENT = 20.0  # Минимальная чистая маржа %
HOURLY_RATE = 25.0  # Базовая ставка в час USD
PLATFORM_FEE_PERCENT = 20.0  # Комиссия платформы (Upwork ~20%)
PAYMENT_FEE_PERCENT = 3.0  # Комиссия платежных систем
AI_COST_PER_1K_TOKENS = 0.01  # Стоимость GPT-4o за 1K токенов


class OrderDecision(Enum):
    """Решение по заказу"""
    ACCEPT = "accept"  # Принять
    NEGOTIATE = "negotiate"  # Предложить доплату
    DECLINE = "decline"  # Отказаться


@dataclass
class CostBreakdown:
    """Разбивка затрат на заказ"""
    client_budget: float  # Бюджет клиента
    platform_fee: float  # Комиссия платформы
    payment_fee: float  # Комиссия за перевод
    ai_costs: float  # Затраты на AI (GPT-4o, API)
    time_hours: float  # Оценочное время в часах
    labor_cost: float  # Стоимость труда (time * hourly_rate)
    total_costs: float  # Общие затраты
    net_profit: float  # Чистая прибыль
    margin_percent: float  # Процент маржи
    decision: OrderDecision  # Решение
    suggested_price: Optional[float] = None  # Предложенная цена для переговоров


class EconomicsEngine:
    """
    Движок экономических расчётов.
    Определяет, стоит ли брать заказ.
    """
    
    def __init__(self):
        self.min_order = MIN_ORDER_AMOUNT
        self.min_margin = MIN_MARGIN_PERCENT
        self.hourly_rate = HOURLY_RATE
        self.platform_fee = PLATFORM_FEE_PERCENT
        self.payment_fee = PAYMENT_FEE_PERCENT
        print(f"[ECONOMICS] Initialized: Min order ${self.min_order}, Min margin {self.min_margin}%")
    
    def estimate_time(self, complexity: str, description: str = "") -> float:
        """
        Оценивает время выполнения в часах.
        
        Args:
            complexity: LOW, MEDIUM, HIGH, VERY_HIGH
            description: Описание задачи для более точной оценки
        """
        base_hours = {
            "LOW": 2,
            "MEDIUM": 6,
            "HIGH": 16,
            "VERY_HIGH": 40
        }
        
        hours = base_hours.get(complexity.upper(), 6)
        
        # Модификаторы по ключевым словам
        desc_lower = description.lower()
        
        if any(kw in desc_lower for kw in ["api", "integration", "webhook"]):
            hours += 2
        if any(kw in desc_lower for kw in ["database", "db", "sql", "postgres"]):
            hours += 3
        if any(kw in desc_lower for kw in ["bot", "telegram", "discord"]):
            hours += 2
        if any(kw in desc_lower for kw in ["scraping", "crawler", "parser"]):
            hours += 4
        if any(kw in desc_lower for kw in ["ai", "ml", "machine learning", "gpt"]):
            hours += 6
        if any(kw in desc_lower for kw in ["simple", "basic", "quick"]):
            hours = max(1, hours - 2)
        if any(kw in desc_lower for kw in ["urgent", "asap", "rush"]):
            hours *= 0.8  # Ускоряемся, но это стоит дороже
        
        return round(hours, 1)
    
    def estimate_ai_costs(self, complexity: str) -> float:
        """Оценка затрат на AI для генерации кода"""
        # Примерное количество токенов на проект
        tokens_by_complexity = {
            "LOW": 5000,
            "MEDIUM": 15000,
            "HIGH": 40000,
            "VERY_HIGH": 100000
        }
        
        tokens = tokens_by_complexity.get(complexity.upper(), 15000)
        return round((tokens / 1000) * AI_COST_PER_1K_TOKENS, 2)
    
    def calculate_costs(self, client_budget: float, 
                       complexity: str = "MEDIUM",
                       description: str = "",
                       platform: str = "upwork") -> CostBreakdown:
        """
        Рассчитывает все затраты и определяет рентабельность.
        
        Args:
            client_budget: Бюджет клиента в USD
            complexity: Сложность проекта
            description: Описание для точной оценки
            platform: Платформа (влияет на комиссию)
        
        Returns:
            CostBreakdown с полным анализом
        """
        # Комиссии платформы
        platform_fees = {
            "upwork": 20.0,
            "freelancer": 15.0,
            "toptal": 0.0,  # Клиент платит
            "github": 0.0,
            "direct": 0.0,
            "crypto": 1.0  # Только gas
        }
        
        platform_fee_pct = platform_fees.get(platform.lower(), self.platform_fee)
        
        # Расчёт комиссий
        platform_fee = client_budget * (platform_fee_pct / 100)
        payment_fee = client_budget * (self.payment_fee / 100)
        
        # Оценка времени и затрат на труд
        time_hours = self.estimate_time(complexity, description)
        labor_cost = time_hours * self.hourly_rate
        
        # Затраты на AI
        ai_costs = self.estimate_ai_costs(complexity)
        
        # Общие затраты
        total_costs = platform_fee + payment_fee + labor_cost + ai_costs
        
        # Чистая прибыль
        net_profit = client_budget - total_costs
        
        # Процент маржи
        margin_percent = (net_profit / client_budget * 100) if client_budget > 0 else 0
        
        # Решение
        if client_budget < self.min_order:
            decision = OrderDecision.DECLINE
            suggested_price = self.min_order
        elif margin_percent < self.min_margin:
            decision = OrderDecision.NEGOTIATE
            # Рассчитываем минимальную цену для 20% маржи
            # net_profit = budget - costs >= budget * 0.20
            # budget - costs >= 0.20 * budget
            # budget * 0.80 >= costs
            # budget >= costs / 0.80
            min_budget_for_margin = total_costs / (1 - self.min_margin / 100)
            suggested_price = max(self.min_order, round(min_budget_for_margin, -1))  # Округляем до 10
        else:
            decision = OrderDecision.ACCEPT
            suggested_price = None
        
        return CostBreakdown(
            client_budget=client_budget,
            platform_fee=round(platform_fee, 2),
            payment_fee=round(payment_fee, 2),
            ai_costs=ai_costs,
            time_hours=time_hours,
            labor_cost=round(labor_cost, 2),
            total_costs=round(total_costs, 2),
            net_profit=round(net_profit, 2),
            margin_percent=round(margin_percent, 1),
            decision=decision,
            suggested_price=suggested_price
        )
    
    def should_accept(self, client_budget: float, 
                     complexity: str = "MEDIUM",
                     description: str = "",
                     platform: str = "upwork") -> Tuple[bool, str, Optional[float]]:
        """
        Быстрая проверка: брать заказ или нет.
        
        Returns:
            (accept: bool, reason: str, suggested_price: Optional[float])
        """
        breakdown = self.calculate_costs(client_budget, complexity, description, platform)
        
        if breakdown.decision == OrderDecision.ACCEPT:
            return True, f"Принять. Маржа {breakdown.margin_percent}%, прибыль ${breakdown.net_profit}", None
        
        elif breakdown.decision == OrderDecision.NEGOTIATE:
            return False, (
                f"Маржа {breakdown.margin_percent}% ниже минимума {self.min_margin}%. "
                f"Предложите клиенту ${breakdown.suggested_price} (вместо ${client_budget})"
            ), breakdown.suggested_price
        
        else:  # DECLINE
            return False, (
                f"Бюджет ${client_budget} ниже минимума ${self.min_order}. "
                f"Отказываемся."
            ), breakdown.suggested_price
    
    def format_analysis(self, breakdown: CostBreakdown) -> str:
        """Форматирует анализ для отображения"""
        decision_emoji = {
            OrderDecision.ACCEPT: "✅",
            OrderDecision.NEGOTIATE: "💬",
            OrderDecision.DECLINE: "❌"
        }
        
        lines = [
            "=" * 40,
            "💰 ECONOMIC ANALYSIS",
            "=" * 40,
            f"Client Budget: ${breakdown.client_budget}",
            "",
            "--- COSTS ---",
            f"Platform Fee: ${breakdown.platform_fee}",
            f"Payment Fee: ${breakdown.payment_fee}",
            f"AI Costs: ${breakdown.ai_costs}",
            f"Labor ({breakdown.time_hours}h @ ${self.hourly_rate}/h): ${breakdown.labor_cost}",
            f"TOTAL COSTS: ${breakdown.total_costs}",
            "",
            "--- PROFIT ---",
            f"Net Profit: ${breakdown.net_profit}",
            f"Margin: {breakdown.margin_percent}%",
            "",
            f"{decision_emoji[breakdown.decision]} DECISION: {breakdown.decision.value.upper()}"
        ]
        
        if breakdown.suggested_price:
            lines.append(f"Suggested Price: ${breakdown.suggested_price}")
        
        lines.append("=" * 40)
        
        return "\n".join(lines)
    
    def generate_negotiation_message(self, client_budget: float, 
                                     suggested_price: float,
                                     project_title: str = "") -> str:
        """
        Генерирует профессиональное сообщение для переговоров о цене.
        """
        difference = suggested_price - client_budget
        
        return f"""Dear Client,

Thank you for your interest in working together on "{project_title}".

After carefully analyzing the project requirements, I've estimated the scope of work involved. To ensure high-quality delivery with proper testing, documentation, and support, my rate for this project would be ${suggested_price:.0f} USD.

This includes:
• Complete, production-ready code
• Documentation and setup guide
• Up to 3 revisions
• 7-day post-delivery support

The additional ${difference:.0f} USD covers the complexity involved and ensures I can dedicate the necessary time to deliver excellence.

Would you be open to adjusting the budget? I'm confident the quality of work will exceed your expectations.

Best regards,
NEXUS-6 AI Development"""


# === SINGLETON ===
_economics_engine = None

def get_economics() -> EconomicsEngine:
    global _economics_engine
    if _economics_engine is None:
        _economics_engine = EconomicsEngine()
    return _economics_engine


# === QUICK FUNCTIONS ===

def evaluate_order(budget: float, complexity: str = "MEDIUM", 
                  description: str = "", platform: str = "upwork") -> Dict:
    """Быстрая оценка заказа"""
    engine = get_economics()
    breakdown = engine.calculate_costs(budget, complexity, description, platform)
    
    return {
        "accept": breakdown.decision == OrderDecision.ACCEPT,
        "decision": breakdown.decision.value,
        "margin_percent": breakdown.margin_percent,
        "net_profit": breakdown.net_profit,
        "suggested_price": breakdown.suggested_price,
        "analysis": engine.format_analysis(breakdown)
    }


def min_price_for_task(complexity: str = "MEDIUM", 
                       description: str = "",
                       platform: str = "upwork") -> float:
    """Минимальная цена для задачи с 20% маржой"""
    engine = get_economics()
    
    # Пробуем с разными бюджетами пока не найдём минимальный с 20% маржой
    for test_budget in range(50, 1000, 10):
        breakdown = engine.calculate_costs(test_budget, complexity, description, platform)
        if breakdown.decision == OrderDecision.ACCEPT:
            return float(test_budget)
    
    return 1000.0  # Fallback


# === TEST ===
if __name__ == "__main__":
    print("=" * 50)
    print("ECONOMICS ENGINE TEST")
    print("=" * 50)
    
    engine = get_economics()
    
    # Test 1: Cheap order (should decline)
    print("\n[TEST 1] Budget $30 (below minimum)")
    result = evaluate_order(30, "LOW")
    print(f"Decision: {result['decision']}")
    print(f"Suggested: ${result['suggested_price']}")
    
    # Test 2: Low margin order (should negotiate)
    print("\n[TEST 2] Budget $60 for MEDIUM task")
    result = evaluate_order(60, "MEDIUM")
    print(result['analysis'])
    
    # Test 3: Good order (should accept)
    print("\n[TEST 3] Budget $150 for MEDIUM task")
    result = evaluate_order(150, "MEDIUM")
    print(f"Decision: {result['decision']}")
    print(f"Margin: {result['margin_percent']}%")
    print(f"Net Profit: ${result['net_profit']}")
    
    # Test 4: Crypto payment (lower fees)
    print("\n[TEST 4] Budget $100 via CRYPTO (lower fees)")
    result = evaluate_order(100, "MEDIUM", platform="crypto")
    print(f"Decision: {result['decision']}")
    print(f"Margin: {result['margin_percent']}%")
    
    # Test 5: Generate negotiation message
    print("\n[TEST 5] Negotiation Message")
    msg = engine.generate_negotiation_message(80, 120, "Telegram Bot")
    print(msg[:300] + "...")



