# -*- coding: utf-8 -*-
"""
NEXUS CORE - Gatekeeper (Profit Detector)
==========================================
Filters unprofitable projects BEFORE they consume agent resources.

Rules:
- Minimum order: $50 USD
- Minimum margin: 20%
- Automatic rejection if criteria not met
- Negotiation suggestions for borderline cases

Ported from: Singularity_Project/gatekeeper.py
Author: NEXUS 10 AI Agency
"""

import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum

# === CONSTANTS ===
MIN_ORDER_USD = 50.0
MIN_MARGIN_PERCENT = 20.0
HOURLY_RATE_USD = 30.0  # Internal cost per hour

# Cost estimates per 1000 tokens (GPT-4o)
GPT4O_INPUT_COST = 0.005   # $5 per 1M tokens
GPT4O_OUTPUT_COST = 0.015  # $15 per 1M tokens

# Platform fees
PLATFORM_FEES = {
    "upwork": 20.0,
    "freelancer": 15.0,
    "toptal": 0.0,
    "github": 0.0,
    "direct": 0.0,
    "crypto": 0.5,
    "wise": 1.0,
    "stripe": 2.9
}


class Verdict(Enum):
    """Gatekeeper decision"""
    ACCEPT = "ACCEPT"          # Proceed with project
    NEGOTIATE = "NEGOTIATE"    # Ask for higher budget
    DECLINE = "DECLINE"        # Reject - not profitable
    NEEDS_INFO = "NEEDS_INFO"  # Cannot calculate - need more data


@dataclass
class CostAnalysis:
    """Detailed cost breakdown"""
    client_budget: float
    platform_fee: float
    payment_fee: float
    estimated_hours: float
    labor_cost: float
    ai_token_cost: float
    infrastructure_cost: float
    total_costs: float
    gross_profit: float
    net_profit: float
    margin_percent: float
    verdict: Verdict
    reason: str
    suggested_price: Optional[float] = None
    missing_info: Optional[List[str]] = None


class Gatekeeper:
    """
    Profit Detector - Filters projects based on profitability.
    
    Usage:
        gatekeeper = Gatekeeper()
        result = gatekeeper.evaluate(budget=100, complexity="MEDIUM")
        
        if result.verdict == Verdict.ACCEPT:
            # Proceed to Architect
        elif result.verdict == Verdict.NEGOTIATE:
            # Send counter-offer to client
        else:
            # Archive and move on
    """
    
    def __init__(self, 
                 min_order: float = MIN_ORDER_USD,
                 min_margin: float = MIN_MARGIN_PERCENT,
                 hourly_rate: float = HOURLY_RATE_USD):
        self.min_order = min_order
        self.min_margin = min_margin
        self.hourly_rate = hourly_rate
    
    def estimate_hours(self, complexity: str, description: str = "") -> float:
        """
        Estimate project hours based on complexity and keywords.
        
        Args:
            complexity: LOW, MEDIUM, HIGH, ENTERPRISE
            description: Project description for keyword analysis
            
        Returns:
            Estimated hours
        """
        base_hours = {
            "LOW": 2,
            "MEDIUM": 6,
            "HIGH": 16,
            "ENTERPRISE": 40
        }
        
        hours = base_hours.get(complexity.upper(), 6)
        desc_lower = description.lower()
        
        # Additive modifiers
        modifiers = [
            (["api", "rest", "graphql", "webhook"], 2),
            (["database", "postgres", "mysql", "mongodb"], 3),
            (["bot", "telegram", "discord", "slack"], 2),
            (["scraper", "crawler", "parsing", "selenium"], 4),
            (["ai", "ml", "gpt", "openai", "langchain"], 5),
            (["docker", "kubernetes", "deployment"], 3),
            (["authentication", "auth", "oauth", "jwt"], 2),
            (["payment", "stripe", "paypal"], 3),
            (["testing", "pytest", "unittest"], 2),
            (["documentation", "readme", "docs"], 1),
        ]
        
        for keywords, add_hours in modifiers:
            if any(kw in desc_lower for kw in keywords):
                hours += add_hours
        
        # Subtractive modifiers
        if any(kw in desc_lower for kw in ["simple", "basic", "quick", "small"]):
            hours = max(1, hours * 0.6)
        
        # Rush modifier
        if any(kw in desc_lower for kw in ["urgent", "asap", "rush", "today"]):
            hours *= 0.8
        
        return round(hours, 1)
    
    def estimate_ai_costs(self, complexity: str, hours: float) -> float:
        """Estimate AI/API costs based on complexity."""
        tokens_per_hour = {
            "LOW": 3000,
            "MEDIUM": 8000,
            "HIGH": 15000,
            "ENTERPRISE": 25000
        }
        
        tokens = tokens_per_hour.get(complexity.upper(), 8000) * hours
        
        input_cost = (tokens * 0.3 / 1000) * GPT4O_INPUT_COST
        output_cost = (tokens * 0.7 / 1000) * GPT4O_OUTPUT_COST
        
        return round(input_cost + output_cost, 2)
    
    def calculate_platform_fee(self, budget: float, platform: str) -> float:
        """Calculate platform fee"""
        fee_percent = PLATFORM_FEES.get(platform.lower(), 5.0)
        return round(budget * (fee_percent / 100), 2)
    
    def calculate_payment_fee(self, budget: float, payment_method: str = "wise") -> float:
        """Calculate payment processing fee"""
        fee_percent = PLATFORM_FEES.get(payment_method.lower(), 2.5)
        return round(budget * (fee_percent / 100), 2)
    
    def evaluate(self,
                 budget: float,
                 complexity: str = "MEDIUM",
                 description: str = "",
                 platform: str = "direct",
                 payment_method: str = "crypto",
                 has_clear_requirements: bool = True) -> CostAnalysis:
        """
        Evaluate project profitability.
        
        Args:
            budget: Client's budget in USD
            complexity: LOW, MEDIUM, HIGH, ENTERPRISE
            description: Project description
            platform: Source platform (upwork, direct, etc.)
            payment_method: How client will pay
            has_clear_requirements: Whether requirements are clear
            
        Returns:
            CostAnalysis with verdict and breakdown
        """
        # Check if we have enough info
        missing_info = []
        if not description and complexity == "MEDIUM":
            missing_info.append("Project description needed for accurate estimate")
        if budget <= 0:
            missing_info.append("Budget must be specified")
        
        if missing_info:
            return CostAnalysis(
                client_budget=budget, platform_fee=0, payment_fee=0,
                estimated_hours=0, labor_cost=0, ai_token_cost=0,
                infrastructure_cost=0, total_costs=0, gross_profit=0,
                net_profit=0, margin_percent=0,
                verdict=Verdict.NEEDS_INFO,
                reason="Cannot calculate - missing information",
                missing_info=missing_info
            )
        
        # Check minimum order
        if budget < self.min_order:
            return CostAnalysis(
                client_budget=budget, platform_fee=0, payment_fee=0,
                estimated_hours=0, labor_cost=0, ai_token_cost=0,
                infrastructure_cost=0, total_costs=0, gross_profit=0,
                net_profit=budget, margin_percent=0,
                verdict=Verdict.DECLINE,
                reason=f"Budget ${budget} below minimum ${self.min_order}",
                suggested_price=self.min_order
            )
        
        # Calculate costs
        platform_fee = self.calculate_platform_fee(budget, platform)
        payment_fee = self.calculate_payment_fee(budget, payment_method)
        estimated_hours = self.estimate_hours(complexity, description)
        labor_cost = round(estimated_hours * self.hourly_rate, 2)
        ai_cost = self.estimate_ai_costs(complexity, estimated_hours)
        infrastructure = 5.0 if complexity in ["HIGH", "ENTERPRISE"] else 2.0
        
        total_costs = platform_fee + payment_fee + labor_cost + ai_cost + infrastructure
        gross_profit = budget - platform_fee - payment_fee
        net_profit = budget - total_costs
        margin_percent = (net_profit / budget * 100) if budget > 0 else 0
        
        # Determine verdict
        if margin_percent >= self.min_margin:
            verdict = Verdict.ACCEPT
            reason = f"Profitable: {margin_percent:.1f}% margin, ${net_profit:.2f} profit"
            suggested = None
        elif margin_percent > 0:
            verdict = Verdict.NEGOTIATE
            min_budget = total_costs / (1 - self.min_margin / 100)
            suggested = max(self.min_order, round(min_budget / 10) * 10)
            reason = f"Margin {margin_percent:.1f}% below minimum {self.min_margin}%. Suggest ${suggested}"
        else:
            verdict = Verdict.DECLINE
            min_budget = total_costs / (1 - self.min_margin / 100)
            suggested = round(min_budget / 10) * 10
            reason = f"Project would result in loss of ${abs(net_profit):.2f}"
        
        return CostAnalysis(
            client_budget=budget,
            platform_fee=platform_fee,
            payment_fee=payment_fee,
            estimated_hours=estimated_hours,
            labor_cost=labor_cost,
            ai_token_cost=ai_cost,
            infrastructure_cost=infrastructure,
            total_costs=round(total_costs, 2),
            gross_profit=round(gross_profit, 2),
            net_profit=round(net_profit, 2),
            margin_percent=round(margin_percent, 1),
            verdict=verdict,
            reason=reason,
            suggested_price=suggested
        )
    
    def quick_check(self, budget: float, complexity: str = "MEDIUM") -> Tuple[bool, str]:
        """Quick profitability check."""
        result = self.evaluate(budget, complexity)
        
        if result.verdict == Verdict.ACCEPT:
            return True, f"ACCEPT: {result.margin_percent}% margin"
        elif result.verdict == Verdict.NEGOTIATE:
            return False, f"NEGOTIATE: Need ${result.suggested_price} (currently ${budget})"
        else:
            return False, f"DECLINE: {result.reason}"
    
    def format_report(self, analysis: CostAnalysis) -> str:
        """Format analysis as readable report"""
        verdict_emoji = {
            Verdict.ACCEPT: "✅",
            Verdict.NEGOTIATE: "💬",
            Verdict.DECLINE: "❌",
            Verdict.NEEDS_INFO: "❓"
        }
        
        lines = [
            "", "=" * 50,
            "  GATEKEEPER PROFIT ANALYSIS",
            "  NEXUS 10 AI Agency",
            "=" * 50, "",
            f"Client Budget: ${analysis.client_budget:.2f}", "",
            "--- COST BREAKDOWN ---",
            f"  Platform Fee:      ${analysis.platform_fee:.2f}",
            f"  Payment Fee:       ${analysis.payment_fee:.2f}",
            f"  Labor ({analysis.estimated_hours}h):    ${analysis.labor_cost:.2f}",
            f"  AI/API Costs:      ${analysis.ai_token_cost:.2f}",
            f"  Infrastructure:    ${analysis.infrastructure_cost:.2f}",
            f"  ─────────────────────────",
            f"  TOTAL COSTS:       ${analysis.total_costs:.2f}", "",
            "--- PROFIT ANALYSIS ---",
            f"  Gross Profit:      ${analysis.gross_profit:.2f}",
            f"  Net Profit:        ${analysis.net_profit:.2f}",
            f"  Margin:            {analysis.margin_percent:.1f}%", "",
            "=" * 50,
            f"  {verdict_emoji[analysis.verdict]} VERDICT: {analysis.verdict.value}",
            f"  {analysis.reason}",
        ]
        
        if analysis.suggested_price:
            lines.append(f"  → Suggested Price: ${analysis.suggested_price:.0f}")
        
        lines.extend(["=" * 50, ""])
        
        return "\n".join(lines)
    
    def generate_negotiation_email(self, 
                                    analysis: CostAnalysis,
                                    project_title: str,
                                    client_name: str = "Client") -> str:
        """Generate professional negotiation email"""
        if not analysis.suggested_price:
            return ""
        
        difference = analysis.suggested_price - analysis.client_budget
        
        return f"""Dear {client_name},

Thank you for considering NEXUS 10 AI Agency for your project: "{project_title}"

After a thorough analysis of the requirements, I've estimated the scope of work involved. To ensure high-quality delivery with:

✓ Production-ready, tested code
✓ Complete documentation
✓ Up to 3 revision rounds
✓ 7-day post-delivery support

My rate for this project would be ${analysis.suggested_price:.0f} USD.

The additional ${difference:.0f} USD reflects the complexity involved and ensures I can dedicate proper time and resources to exceed your expectations.

Would you be open to adjusting the budget? I'm confident the quality of work will justify the investment.

Alternatively, we could discuss reducing scope to fit within your current budget of ${analysis.client_budget:.0f}.

Looking forward to your response.

Best regards,
NEXUS 10 AI Agency
"""


# === SINGLETON ===
_gatekeeper_instance = None

def get_gatekeeper() -> Gatekeeper:
    """Get or create Gatekeeper singleton"""
    global _gatekeeper_instance
    if _gatekeeper_instance is None:
        _gatekeeper_instance = Gatekeeper()
    return _gatekeeper_instance


# === QUICK FUNCTIONS ===

def vet_project(budget: float, complexity: str = "MEDIUM", 
                description: str = "", platform: str = "direct") -> Dict:
    """Quick project vetting"""
    gk = get_gatekeeper()
    analysis = gk.evaluate(budget, complexity, description, platform)
    
    return {
        "proceed": analysis.verdict == Verdict.ACCEPT,
        "verdict": analysis.verdict.value,
        "margin": analysis.margin_percent,
        "profit": analysis.net_profit,
        "costs": analysis.total_costs,
        "suggested_price": analysis.suggested_price,
        "reason": analysis.reason
    }


def should_take_project(budget: float, complexity: str = "MEDIUM") -> bool:
    """Simple yes/no check"""
    gk = get_gatekeeper()
    proceed, _ = gk.quick_check(budget, complexity)
    return proceed


def minimum_price_for(complexity: str = "MEDIUM", 
                      description: str = "",
                      platform: str = "direct") -> float:
    """Calculate minimum profitable price"""
    gk = get_gatekeeper()
    
    low, high = MIN_ORDER_USD, 5000
    
    while high - low > 10:
        mid = (low + high) / 2
        analysis = gk.evaluate(mid, complexity, description, platform)
        
        if analysis.verdict == Verdict.ACCEPT:
            high = mid
        else:
            low = mid
    
    return round(high / 10) * 10






